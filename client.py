from flask import Flask, request, jsonify, send_file
from helpers import download_youtube_transcript
from prompts import summary_prompt, format_prompt, bps_prompt
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

client = OpenAI()

app = Flask(__name__)

def llm_request(prompt):
    messages = [{'role': 'user', 'content': prompt}]
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=messages,
    )
    output = response.choices[0].message.content
    return output


@app.route('/summary', methods=['GET'])
def get_summary():
    video_id = request.args.get('video_id')
    transcript_raw = download_youtube_transcript(video_id)
    summary_text = _llm_summary(transcript_raw)
    return jsonify({'summary': summary_text})


@app.route('/bullet_points', methods=['GET'])
def get_bullet_points():
    video_id = request.args.get('video_id')
    transcript_raw = download_youtube_transcript(video_id)
    bullet_points = _llm_bps(transcript_raw)
    return jsonify({'bullet_points': bullet_points})


@app.route('/transcription', methods=['GET'])
def get_transcription():
    video_id = request.args.get('video_id')
    transcript_raw = download_youtube_transcript(video_id)
    formatted_transcript = _llm_format(transcript_raw)
    return jsonify({'transcription': formatted_transcript})


@app.route('/markdown_download', methods=['GET'])
def markdown_download():
    video_id = request.args.get('video_id')
    transcript_raw = download_youtube_transcript(video_id)

    summary = _llm_summary(transcript_raw)
    bullet_points = _llm_bps(transcript_raw)
    formatted_transcript = _llm_format(transcript_raw)

    markdown_content = f"""
# Video Summary

## Summary
{summary}

## Bullet Points
{bullet_points}

## Formatted Transcript
{formatted_transcript}
"""

    file_path = f"{video_id}.md"
    with open(file_path, 'w') as markdown_file:
        markdown_file.write(markdown_content)
    return send_file(file_path, as_attachment=True, download_name=f"{video_id}_summary.md")


def _llm_summary(transcript):
    summary_prompt_text = summary_prompt(transcript)
    return llm_request(summary_prompt_text)

def _llm_bps(transcript):
    bps_prompt_text = bps_prompt(transcript)
    return llm_request(bps_prompt_text)

def _llm_format(transcript):
    formatted_prompt = format_prompt(transcript)
    return llm_request(formatted_prompt)

if __name__ == "__main__":
    app.run(debug=True)
