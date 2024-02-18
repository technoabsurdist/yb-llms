from flask import Flask, request, jsonify, send_file
from functools import wraps
from helpers import download_youtube_transcript, get_youtube_title
from prompts import summary_prompt, format_prompt, bps_prompt
from openai import OpenAI
from dotenv import load_dotenv

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
        if not video_id and not video_url:
            return jsonify({'error': 'Please provide a video_id or video_url'})
        if not video_id:
            video_id = video_url.split("v=")[1].split("&")[0]
        return f(video_id, *args, **kwargs)
    return decorated_function

@app.route('/summary', methods=['GET'])
@validate_video
def get_summary(video_id):
    transcript_raw = download_youtube_transcript(video_id)
    summary_text = llm_request(summary_prompt(transcript_raw))
    return jsonify({'summary': summary_text})

@app.route('/bullet_points', methods=['GET'])
@validate_video
def get_bullet_points(video_id):
    transcript_raw = download_youtube_transcript(video_id)
    bullet_points = llm_request(bps_prompt(transcript_raw))
    return jsonify({'bullet_points': bullet_points})

@app.route('/transcription', methods=['GET'])
@validate_video
def get_transcription(video_id):
    transcript_raw = download_youtube_transcript(video_id)
    formatted_transcript = llm_request(format_prompt(transcript_raw))
    return jsonify({'transcription': formatted_transcript})

@app.route('/markdown_download', methods=['GET'])
@validate_video
def markdown_download(video_id):
    video_title = get_youtube_title(video_id)
    transcript_raw = download_youtube_transcript(video_id)
    summary = llm_request(summary_prompt(transcript_raw))
    bullet_points = llm_request(bps_prompt(transcript_raw))
    formatted_transcript = llm_request(format_prompt(transcript_raw))
    markdown_content = f"""# {video_title} -- Transcript\n\n## Summary\n{summary}\n\n## Bullet Points\n{bullet_points}\n\n## Formatted Transcript\n{formatted_transcript}\n"""
    file_path = f"outputs/{video_id}.md"
    with open(file_path, 'w') as markdown_file:
        markdown_file.write(markdown_content)
    return send_file(file_path, as_attachment=True, download_name=f"{video_id}_summary.md")





if __name__ == "__main__":
    app.run(debug=True)
