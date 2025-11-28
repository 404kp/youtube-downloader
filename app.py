from flask import Flask, render_template, request, send_file, after_this_request, jsonify
import yt_dlp
import os
import tempfile
import zipfile
import uuid
import shutil

app = Flask(__name__)

# Add FFmpeg to PATH
ffmpeg_path = r"C:\Users\Pommer\AppData\Local\Microsoft\WinGet\Packages\Gyan.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe\ffmpeg-8.0.1-full_build\bin"
if os.path.exists(ffmpeg_path) and ffmpeg_path not in os.environ['PATH']:
    os.environ['PATH'] += os.pathsep + ffmpeg_path

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/get_info', methods=['POST'])
def get_info():
    data = request.get_json()
    urls = data.get('urls', [])
    
    if not urls:
        return jsonify({'error': 'Keine URLs angegeben'}), 400

    videos = []
    ydl_opts = {
        'quiet': True,
        'extract_flat': True, # Faster, gets basic info
        'no_warnings': True,
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        for url in urls:
            if not url.strip(): continue
            try:
                info = ydl.extract_info(url, download=False)
                
                video_data = {
                    'url': url,
                    'title': info.get('title', 'Unbekannter Titel'),
                    'thumbnail': info.get('thumbnail', ''), # Might be empty in flat mode
                    'duration': info.get('duration_string', ''),
                    'uploader': info.get('uploader', '')
                }
                # If thumbnail is missing in flat mode, we might need to fetch it differently or just show a placeholder.
                # Usually flat extraction gives 'thumbnails' list or 'thumbnail' string.
                videos.append(video_data)
            except Exception as e:
                print(f"Error extracting info for {url}: {e}")
                pass
    
    return jsonify({'videos': videos})

def process_download(urls, format_type, is_zip=False):
    # Create a unique temp directory for this request
    request_id = str(uuid.uuid4())
    temp_dir = os.path.join(tempfile.gettempdir(), 'yt_dl_' + request_id)
    os.makedirs(temp_dir, exist_ok=True)

    try:
        downloaded_files = []
        
        ydl_opts = {
            'outtmpl': os.path.join(temp_dir, '%(title)s.%(ext)s'),
            'format': 'bestvideo+bestaudio/best' if format_type == 'mp4' else 'bestaudio/best',
            'noplaylist': True,
            'quiet': True,
        }

        if format_type == 'mp3':
            ydl_opts['postprocessors'] = [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }]
        elif format_type == 'mp4':
             ydl_opts['merge_output_format'] = 'mp4'

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            for url in urls:
                try:
                    info = ydl.extract_info(url, download=True)
                    filename = ydl.prepare_filename(info)
                    
                    if format_type == 'mp3':
                        final_filename = os.path.splitext(filename)[0] + '.mp3'
                    elif format_type == 'mp4':
                        final_filename = os.path.splitext(filename)[0] + '.mp4'
                    else:
                        final_filename = filename

                    if os.path.exists(final_filename):
                        downloaded_files.append(final_filename)
                except Exception as e:
                    print(f"Error downloading {url}: {e}")
                    continue

        if not downloaded_files:
            shutil.rmtree(temp_dir, ignore_errors=True)
            return None, "Keine Videos konnten heruntergeladen werden."

        if is_zip:
            output_filename = os.path.join(temp_dir, f'downloads_{format_type}.zip')
            with zipfile.ZipFile(output_filename, 'w') as zipf:
                for file in downloaded_files:
                    zipf.write(file, os.path.basename(file))
            final_output = output_filename
            mimetype = 'application/zip'
            as_attachment_name = f'downloads_{format_type}.zip'
        else:
            # Single file
            final_output = downloaded_files[0]
            mimetype = 'audio/mpeg' if format_type == 'mp3' else 'video/mp4'
            as_attachment_name = os.path.basename(final_output)

        @after_this_request
        def cleanup(response):
            try:
                shutil.rmtree(temp_dir)
            except Exception as e:
                app.logger.error(f"Error cleaning up temp dir: {e}")
            return response

        return send_file(final_output, as_attachment=True, download_name=as_attachment_name, mimetype=mimetype), None

    except Exception as e:
        shutil.rmtree(temp_dir, ignore_errors=True)
        return None, str(e)

@app.route('/download_single', methods=['POST'])
def download_single():
    data = request.get_json()
    url = data.get('url')
    format_type = data.get('format')
    
    if not url:
        return jsonify({'error': 'Keine URL angegeben'}), 400
        
    response, error = process_download([url], format_type, is_zip=False)
    if error:
        return jsonify({'error': error}), 500
    return response

@app.route('/download_all', methods=['POST'])
def download_all():
    data = request.get_json()
    urls = data.get('urls', [])
    format_type = data.get('format')
    
    if not urls:
        return jsonify({'error': 'Keine URLs angegeben'}), 400
        
    response, error = process_download(urls, format_type, is_zip=True)
    if error:
        return jsonify({'error': error}), 500
    return response

if __name__ == '__main__':
    app.run(debug=True)
