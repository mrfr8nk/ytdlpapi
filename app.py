import os
import time
import psutil
import requests
from threading import Thread
from yt_dlp import YoutubeDL
from datetime import timedelta
from werkzeug.utils import secure_filename
from flask import Flask, request, jsonify, send_from_directory, render_template


app = Flask(__name__)
DOWNLOAD_FOLDER = 'stream'
app.config['DOWNLOAD_FOLDER'] = DOWNLOAD_FOLDER
URL = 'https://subzerodl-api.vercel.app'

app.config['JSONIFY_PRETTYPRINT_REGULAR'] = True
app.json.sort_keys = False
app.json.compact = False

if not os.path.exists(DOWNLOAD_FOLDER):
    os.makedirs(DOWNLOAD_FOLDER)

def delete_file_later(filepath, delay=3600):
    """Delete file after specified delay in seconds"""
    def delete_file():
        time.sleep(delay)
        try:
            if os.path.exists(filepath):
                os.remove(filepath)
        except Exception as e:
            app.logger.error(f"Error deleting file {filepath}: {str(e)}")
    Thread(target=delete_file).start()

def get_server_stats():
    """Get server statistics including uptime and RAM usage"""
    try:
        process = psutil.Process(os.getpid())
        uptime_seconds = time.time() - process.create_time()
        uptime = str(timedelta(seconds=uptime_seconds)).split('.')[0]
        
        ram = psutil.virtual_memory()
        used_ram = f"{ram.used / (1024 ** 3):.2f}GB"
        total_ram = f"{ram.total / (1024 ** 3):.2f}GB"
        
        return {
            'runtime': uptime,
            'server_ram': f"{used_ram}/{total_ram}"
        }
    except Exception as e:
        app.logger.error(f"Error getting server stats: {str(e)}")
        return {
            'runtime': 'unknown',
            'server_ram': 'unknown'
        }

@app.route('/stream.php/<path:filename>')
def serve_static(filename):
    try:
        return send_from_directory(
            app.config['DOWNLOAD_FOLDER'],
            filename,
            mimetype='audio/mpeg' if filename.endswith('.mp3') else 'video/mp4'
        )
    except Exception as e:
        app.logger.error(f"Error serving file {filename}: {str(e)}")
        return jsonify({
            'status': 404,
            'success': False,
            'error': 'File not found'
        }), 404

@app.route('/')
def home():
    try:
        stats = get_server_stats()
        response = {
            'status': 200,
            'success': True,
            'creator': 'Mr Frank',
            'result': {
                'runtime': stats['runtime'],
                'your_ip': request.remote_addr,
                'server_ram': stats['server_ram'],
                'supports': [
                    'youtube',
                    'tiktok',
                    'instagram',
                    'twitter(x)',
                    'soundcloud',
                    'pornhub',
                    'xnxx',
                    'xvideos',
                    'youporn'
                ],
                'yts_param': [
                    'query (required)'
                ],
                'dl_params': [
                    'url (required)',
                    'format (optional)'
                ],
                'endpoints': [
                    '/api/yts.php',
                    '/api/audio.php',
                    '/api/video.php'
                ],
                'info': 'Files are auto deleted soon, make sure to download if you intend to. Available video formats are 360p, 480p, 720p, 1080p, 4k/2160p and can be passed as ?url=...&format=... Default is 720p if format param is empty. If a requested format is not available for a specific video, its highest quality available will be downloaded.'
            }
        }
        return jsonify(response)
    except Exception as e:
        app.logger.error(f"Error in home route: {str(e)}")
        return jsonify({
            'status': 500,
            'success': False,
            'error': 'Internal server error'
        }), 500

@app.route('/try')
def try_page():
    try:
        return render_template('index.html')
    except Exception as e:
        app.logger.error(f"Error rendering template: {str(e)}")
        return jsonify({
            'status': 500,
            'success': False,
            'error': 'Template rendering error'
        }), 500

@app.route('/health')
def health_check():
    return jsonify({"status": "healthy"}), 200


@app.route('/api/yts.php')
def search_youtube():
    query = request.args.get('query')
    if not query:
        return jsonify({
            'status': 400,
            'success': False,
            'creator': 'Mr Frank',
            'error': 'QUERY parameter is required'
        }), 400
    
    try:
        response = requests.get(f'https://yts.giftedtech.co.ke/?q={query}')
        response.raise_for_status()  
        return jsonify(response.json()), 200
    except requests.exceptions.RequestException as e:
        return jsonify({"error": str(e)}), 500
        

@app.route('/api/audio.php', methods=['GET'])
def download_audio():
    url = request.args.get('url')

    if not url:
        return jsonify({
            'status': 400,
            'success': False,
            'creator': 'Mr Frank',
            'error': 'URL parameter is required'
        }), 400

    ydl_opts = {
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:94.0) Gecko/20100101 Firefox/94.0',
        'cookiefile': 'cookies.txt',
        'format': 'bestaudio/best',
        'outtmpl': os.path.join(DOWNLOAD_FOLDER, '%(title)s.%(ext)s'),
        'prefer_ffmpeg': False,
        #'noplaylist': True,
       # 'postprocessors': [{
        #    'key': 'FFmpegExtractAudio',
        #    'preferredcodec': 'mp3',
       #     'preferredquality': '320',
       # }],
        'quiet': True,
        'no_warnings': True
    }

    try:
        with YoutubeDL(ydl_opts) as ydl:
            info_dict = ydl.extract_info(url, download=True)
            title = info_dict.get('title', 'unknown')
            thumbnail = info_dict.get('thumbnail', 'unknown')
            original_filename = ydl.prepare_filename(info_dict)
            mp3_filename = original_filename.replace('.webm', '.mp3').replace('.m4a', '.mp3')
            
            safe_filename = secure_filename(title).replace(' ', '_') + '_by_mrfrank_api' + '.mp3'
            output_path = os.path.join(DOWNLOAD_FOLDER, safe_filename)

            if os.path.exists(mp3_filename):
                os.rename(mp3_filename, output_path)
            elif os.path.exists(original_filename):
                os.rename(original_filename, output_path)
            else:
                raise FileNotFoundError("Downloaded file not found")

            delete_file_later(output_path)

            response = {
                'status': 200,
                'success': True,
                'creator': 'Mr Frank',
                'result': {
                    'format': '320kbps',
                    'title': title,
                    'src_url': url,
                    'thumbnail': thumbnail,
                    'info': 'Audio file will be auto deleted soon, make sure to download it if you intend to.',
                    'stream_url': f'{URL}/stream.php/{safe_filename}',
                    'download_url': f'{URL}/download.php/{safe_filename}'
                }
            }
            
        return jsonify(response), 200
    except Exception as e:
        app.logger.error(f"Audio download error: {str(e)}")
        return jsonify({
            'status': 500,
            'success': False,
            'creator': 'MrFrank,
            'error': str(e)
        }), 500


@app.route('/api/video.php', methods=['GET'])
def download_video():
    url = request.args.get('url')
    format = request.args.get('format', '720p')

    if not url:
        return jsonify({
            'status': 400,
            'success': False,
            'creator': 'Mr Frank',
            'error': 'URL parameter is required'
        }), 400

    format_map = {
        '360p': 'bestvideo[height<=360]+bestaudio/best',
        '480p': 'bestvideo[height<=480]+bestaudio/best',
        '720p': 'bestvideo[height<=720]+bestaudio/best',
        '1080p': 'bestvideo[height<=1080]+bestaudio/best',
        '2160p': 'bestvideo[height<=2160]+bestaudio/best',
        '4k': 'bestvideo[height<=2160]+bestaudio/best'
    }

    ydl_opts = {
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:94.0) Gecko/20100101 Firefox/94.0',
        'cookiefile': 'cookies.txt',
        'format': format_map.get(format, format_map['720p']),
        'outtmpl': os.path.join(DOWNLOAD_FOLDER, '%(title)s.%(ext)s'),
        'quiet': True,
        'no_warnings': True
    }

    try:
        with YoutubeDL(ydl_opts) as ydl:
            info_dict = ydl.extract_info(url, download=True)
            title = info_dict.get('title', 'unknown')
            thumbnail = info_dict.get('thumbnail', 'unknown')
            file_path = ydl.prepare_filename(info_dict)
            
            safe_filename = secure_filename(title).replace(' ', '_') + f'_{format}' + '_by_mrfrankapis' + '.mp4'
            output_path = os.path.join(DOWNLOAD_FOLDER, safe_filename)

            os.rename(file_path, output_path)
            delete_file_later(output_path)

            response = {
                'status': 200,
                'success': True,
                'creator': 'Mr Frank',
                'result': {
                    'format': format,
                    'title': title,
                    'src_url': url,
                    'thumbnail': thumbnail,
                    'stream_url': f'{URL}/stream.php/{safe_filename}',
                    'download_url': f'{URL}/download.php/{safe_filename}',
                    'info': 'Video file will be auto deleted soon, make sure to download it if you intend to. Available video formats are 360p, 480p, 720p, 1080p, 4k/2160p and can be passed as ?url=...&format=... Default is 720p if format param is empty. If a requested format is not available for a specific video, its highest quality available will be downloaded.'
                }
            }
            
        return jsonify(response), 200
    except Exception as e:
        app.logger.error(f"Video download error: {str(e)}")
        return jsonify({
            'status': 500,
            'success': False,
            'creator': 'Gifted Tech',
            'error': str(e)
        }), 500


@app.route('/download.php/<filename>', methods=['GET'])
def download_file(filename):
    try:
        download_as = request.args.get('name', filename)
        return send_from_directory(
            app.config['DOWNLOAD_FOLDER'],
            filename,
            as_attachment=True,
            download_name=download_as
        )
    except Exception as e:
        app.logger.error(f"File download error: {str(e)}")
        return jsonify({
            'status': 404,
            'success': False,
            'error': 'File not found or has been auto deleted'
        }), 404

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 1300))
    app.run(host='0.0.0.0', port=port)



