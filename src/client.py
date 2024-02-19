from flask import Flask, request, jsonify, send_file
from weasyprint import HTML
from functools import wraps
import re
from helpers import download_youtube_transcript, get_youtube_title
from prompts import summary_prompt, format_prompt, bps_prompt
from openai import OpenAI
from dotenv import load_dotenv
from urllib.parse import urlparse, parse_qs
from concurrent.futures import ThreadPoolExecutor
import markdown2

load_dotenv()
client = OpenAI()
app = Flask(__name__)

def llm_request(prompt):
    try:
        response = client.chat.completions.create(model="gpt-3.5-turbo", messages=[{'role': 'user', 'content': prompt}])
        return response.choices[0].message.content
    except Exception as e:
        return {'error': 'Failed to generate response from language model', 'detail': str(e)}

def validate_video(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        video_id = request.args.get('video_id')
        video_url = request.args.get('video_url')
        if not video_id and not video_url:
            return jsonify({'error': 'Missing video_id or video_url'}), 400
        if video_url:
            video_id = extract_video_id(video_url)
            if not video_id:
                return jsonify({'error': 'Invalid or unsupported video URL'}), 400
        if not re.match(r'^[a-zA-Z0-9_-]{11}$', video_id):
            return jsonify({'error': 'Invalid video ID format'}), 400
        return f(video_id, *args, **kwargs)
    return decorated_function

def extract_video_id(url):
    parsed_url = urlparse(url)
    if parsed_url.hostname in ('www.youtube.com', 'youtube.com') and parsed_url.path == '/watch':
        video_id = parse_qs(parsed_url.query).get('v', [None])[0]
    elif parsed_url.hostname == 'youtu.be':
        video_id = parsed_url.path[1:]
    else:
        return None
    return video_id if re.match(r'^[a-zA-Z0-9_-]{11}$', video_id) else None


### Routes

@app.route('/summary', methods=['GET'])
@validate_video
def get_summary(video_id):
    print(f"Generating summary for video ID: {video_id}")
    transcript_raw = download_youtube_transcript(video_id)
    summary_text = llm_request(summary_prompt(transcript_raw))
    return jsonify({'summary': summary_text})

@app.route('/bullet_points', methods=['GET'])
@validate_video
def get_bullet_points(video_id):
    print("Generating bullet points for video ID: {video_id}")
    transcript_raw = download_youtube_transcript(video_id)
    bullet_points = llm_request(bps_prompt(transcript_raw))
    return jsonify({'bullet_points': bullet_points})

@app.route('/transcription', methods=['GET'])
@validate_video
def get_transcription(video_id):
    print(f"Generating and formatting transcription for video ID: {video_id}")
    transcript_raw = download_youtube_transcript(video_id)
    formatted_transcript = llm_request(format_prompt(transcript_raw))
    return jsonify({'transcription': formatted_transcript})

@app.route('/download', methods=['GET'])
@validate_video
def download_content(video_id):
    format_type = request.args.get('format', 'markdown').lower()
    video_title = get_youtube_title(video_id) if get_youtube_title(video_id) else f"{video_id}"
    transcript_raw = download_youtube_transcript(video_id)

    def fetch_data(prompt):
        return llm_request(prompt(transcript_raw))
    
    with ThreadPoolExecutor(max_workers=3) as executor:
        future_summary = executor.submit(fetch_data, summary_prompt)
        future_bullet_points = executor.submit(fetch_data, bps_prompt)
        future_formatted_transcript = executor.submit(fetch_data, format_prompt)
        
        summary = future_summary.result()
        bullet_points = future_bullet_points.result()
        formatted_transcript = future_formatted_transcript.result()
    
    markdown_content = f"""# {video_title} -- Transcript\n\n## Summary\n{summary}\n\n## Bullet Points\n{bullet_points}\n\n## Formatted Transcript\n{formatted_transcript}\n"""
    
    if format_type == 'pdf':
        html_content = markdown2.markdown(markdown_content)
        file_path = f"../outputs/{video_id}.pdf"
        HTML(string=html_content).write_pdf(file_path)
    if format_type == 'html':
        html_content = markdown2.markdown(markdown_content)
        file_path = f"../outputs/{video_id}.html"
        with open(file_path, 'w') as file:
            file.write(html_content)
    else:
        file_path = f"../outputs/{video_id}.md"
        with open(file_path, 'w') as file:
            file.write(markdown_content)
    
    return send_file(file_path, as_attachment=True, download_name=f"{video_id}_summary.{format_type}")


# 404
@app.errorhandler(404)
def page_not_found(e):
    return jsonify({'error': 'This endpoint does not exist. Please check the URL and try again.'}), 404


@app.route('/', methods=['GET'])
def index():
    return jsonify({'message': 'YB <> LLM => Server running!'})



if __name__ == "__main__":
    app.run(debug=True)
