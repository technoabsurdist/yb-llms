from youtube_transcript_api import YouTubeTranscriptApi
import requests
from bs4 import BeautifulSoup

def download_youtube_transcript(video_id):
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

# Scraping to not use official API
def get_youtube_title(video_id):
    url = "https://www.youtube.com/watch?v=" + video_id
    r = requests.get(url)
    soup = BeautifulSoup(r.text)
    link = soup.find_all(name="title")[0]
    title = str(link)
    title = title.replace("<title>","")
    title = title.replace("</title>","")

    return title