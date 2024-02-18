from flask import Flask, request, jsonify, send_file
from functools import wraps
from helpers import download_youtube_transcript, get_youtube_title
from prompts import summary_prompt, format_prompt, bps_prompt
from openai import OpenAI
from dotenv import load_dotenv
from urllib.parse import urlparse, parse_qs
from concurrent.futures import ThreadPoolExecutor

load_dotenv()
client = OpenAI()
app = Flask(__name__)

def llm_request(prompt):
    response = client.chat.completions.create(model="gpt-3.5-turbo", messages=[{'role': 'user', 'content': prompt}])
    return response.choices[0].message.content

def validate_video(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        video_id = request.args.get('video_id')
        video_url = request.args.get('video_url')
        print(f"Received video URL: {video_url} or ID: {video_id}")
        if not video_id and not video_url:
            print("Error: No video_id or video_url provided.")  # Log error
            return jsonify({'error': 'Please provide a video_id or video_url'}), 400
        if video_url:
            query = urlparse(video_url)
            if query.hostname in ('www.youtube.com', 'youtube.com') and query.path == '/watch':
                video_id = parse_qs(query.query).get('v', [None])[0]
            elif query.hostname in ('youtu.be',):
                video_id = query.path[1:]
            print(f"Extracted video ID: {video_id}") 
        if not video_id:
            print("Error: Unable to extract video ID from URL.")
            return jsonify({'error': 'Unable to extract video ID from URL'}), 400
        
        return f(video_id, *args, **kwargs)
    return decorated_function



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
    print(f"Generating transcription for video ID: {video_id}")
    transcript_raw = download_youtube_transcript(video_id)
    formatted_transcript = llm_request(format_prompt(transcript_raw))
    return jsonify({'transcription': formatted_transcript})

@app.route('/markdown_download', methods=['GET'])
@validate_video
def markdown_download(video_id):
    video_title = get_youtube_title(video_id)
    transcript_raw = download_youtube_transcript(video_id)

    def fetch_data(prompt):
        return llm_request(prompt(transcript_raw))
    
    # concurrent requests
    with ThreadPoolExecutor(max_workers=3) as executor:
        future_summary = executor.submit(fetch_data, summary_prompt)
        future_bullet_points = executor.submit(fetch_data, bps_prompt)
        future_formatted_transcript = executor.submit(fetch_data, format_prompt)
        
        summary = future_summary.result()
        bullet_points = future_bullet_points.result()
        formatted_transcript = future_formatted_transcript.result()
    
    markdown_content = f"""# {video_title} -- Transcript\n\n## Summary\n{summary}\n\n## Bullet Points\n{bullet_points}\n\n## Formatted Transcript\n{formatted_transcript}\n"""
    file_path = f"outputs/{video_id}.md"
    with open(file_path, 'w') as markdown_file:
        markdown_file.write(markdown_content)
    return send_file(file_path, as_attachment=True, download_name=f"{video_id}_summary.md")

@app.route('/', methods=['GET'])
def index():
    return jsonify({'message': 'YB <> LLM => Server running!'})

if __name__ == "__main__":
    app.run(debug=True)
