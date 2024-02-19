from flask import Flask, request, jsonify, send_file
from helpers import *
from prompts import summary_prompt, format_prompt, bps_prompt
import markdown2


app = Flask(__name__)


### Routes

@app.route('/summary', methods=['GET'])
@validate_video
def get_summary(video_id):
    return generate_response(video_id, summary_prompt)

@app.route('/bullet_points', methods=['GET'])
@validate_video
def get_bullet_points(video_id):
    return generate_response(video_id, bps_prompt)

@app.route('/transcription', methods=['GET'])
@validate_video
def get_transcription(video_id):
    return generate_response(video_id, format_prompt)

@app.route('/download', methods=['GET'])
@validate_video
def download_content(video_id):
    format_type = request.args.get('format', 'markdown').lower()
    video_title = get_youtube_title(video_id) if get_youtube_title(video_id) else f"{video_id}"
    transcript_raw = download_youtube_transcript(video_id)
    
    summary, bullet_points, formatted_transcript = fetch_data_concurrently(
        transcript_raw, summary_prompt, bps_prompt, format_prompt, llm_request)
    
    markdown_content = generate_markdown_content(video_title, summary, bullet_points, formatted_transcript)
    
    file_path = f"../outputs/{video_id}.{format_type}"
    if format_type == 'pdf':
        html_content = markdown2.markdown(markdown_content)
        convert_markdown_to_pdf(html_content, file_path)
    elif format_type == 'html':
        write_content_to_file(file_path, markdown_content, is_html=True)
    else:
        write_content_to_file(file_path, markdown_content)
    
    return send_file(file_path, as_attachment=True, download_name=f"{video_id}_summary.{format_type}")

# 404
@app.errorhandler(404)
def page_not_found(e):
    return jsonify({'error': 'This endpoint does not exist. Please check the URL and try again.'}), 404

# testing active server route
@app.route('/', methods=['GET'])
def index():
    return jsonify({'message': 'YB <> LLM => Server running!'})


if __name__ == "__main__":
    app.run(debug=True)
