from youtube_transcript_api import YouTubeTranscriptApi
import asyncio

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

