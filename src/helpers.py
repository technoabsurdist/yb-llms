from functools import wraps
from flask import jsonify, request
from youtube_transcript_api import YouTubeTranscriptApi
import requests
from bs4 import BeautifulSoup
from openai import OpenAI
from dotenv import load_dotenv
import re
from urllib.parse import urlparse, parse_qs
from concurrent.futures import ThreadPoolExecutor
from weasyprint import HTML
import markdown2

load_dotenv()
client = OpenAI()

def download_youtube_transcript(video_id):
    """Downloads the transcript for a given YouTube video using youtube_transcript_api."""
    try:
        transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)
        transcript_fulltxt = ""
        for transcript in transcript_list:
            for item in transcript.fetch():
                transcript_fulltxt += item['text'] + " "
            return transcript_fulltxt
        return ""
    except Exception as e:
        print(f"Error fetching transcript: {e}")
        return "" 

def llm_request(prompt):
    """Generates a response from chat openai-3.5-turbo"""
    try:
        response = client.chat.completions.create(model="gpt-3.5-turbo", messages=[{'role': 'user', 'content': prompt}])
        return response.choices[0].message.content
    except Exception as e:
        return {'error': 'Failed to generate response from language model', 'detail': str(e)}
    
def get_youtube_title(video_id):
    """Fetches the title of a YouTube video using web scraping (beautifulsoup)"""
    try:
        url = "https://www.youtube.com/watch?v=" + video_id
        r = requests.get(url)
        soup = BeautifulSoup(r.text, features="html.parser")
        link = soup.find_all(name="title")[0]
        title = str(link)
        title = title.replace("<title>","")
        title = title.replace("</title>","")
    except Exception as e:
        print(f"Error fetching title: {e}")
        return ""

    return title

def extract_video_id(url):
    """Extracts the video ID from a YouTube URL. Supports both regular and shortened URLs."""
    parsed_url = urlparse(url)
    if parsed_url.hostname in ('www.youtube.com', 'youtube.com') and parsed_url.path == '/watch':
        video_id = parse_qs(parsed_url.query).get('v', [None])[0]
    elif parsed_url.hostname == 'youtu.be':
        video_id = parsed_url.path[1:]
    else:
        return None
    return video_id if re.match(r'^[a-zA-Z0-9_-]{11}$', video_id) else None

def validate_video(f):
    """Decorator to validate video ID or URL."""
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

def process_transcript(video_id, processing_function):
    """Fetches transcript and processes it using the given function."""
    transcript_raw = download_youtube_transcript(video_id)
    return processing_function(transcript_raw)

def generate_response(video_id, prompt_function):
    """Generates a standard JSON response for a given processing function."""
    processed_text = process_transcript(video_id, lambda x: llm_request(prompt_function(x)))
    return jsonify({prompt_function.__name__: processed_text})

def fetch_data_concurrently(transcript_raw, summary_prompt, bps_prompt, format_prompt, llm_request):
    """Fetches summary, bullet points, and formatted transcript concurrently."""
    def fetch_data(prompt):
        return llm_request(prompt(transcript_raw))
    
    with ThreadPoolExecutor(max_workers=3) as executor:
        future_summary = executor.submit(fetch_data, summary_prompt)
        future_bullet_points = executor.submit(fetch_data, bps_prompt)
        future_formatted_transcript = executor.submit(fetch_data, format_prompt)
        
        summary = future_summary.result()
        bullet_points = future_bullet_points.result()
        formatted_transcript = future_formatted_transcript.result()
    
    return summary, bullet_points, formatted_transcript

def generate_markdown_content(video_title, summary, bullet_points, formatted_transcript):
    """Generates markdown content for the video."""
    return f"""# {video_title} -- Transcript\n\n## Summary\n{summary}\n\n## Bullet Points\n{bullet_points}\n\n## Formatted Transcript\n{formatted_transcript}\n"""

def write_content_to_file(file_path, content, is_html=False):
    """Writes content to a file. Converts to HTML if needed."""
    if is_html:
        content = markdown2.markdown(content)
    with open(file_path, 'w') as file:
        file.write(content)

def convert_markdown_to_pdf(html_content, file_path):
    """Converts markdown content to PDF."""
    HTML(string=html_content).write_pdf(file_path)