from youtube_transcript_api import YouTubeTranscriptApi
from pytube import extract
import requests
from bs4 import BeautifulSoup
from pytesseract import pytesseract
from PIL import Image
def get_text_from_youtube(url):
    video_id=extract.video_id(url)
    try:
        transcript = YouTubeTranscriptApi.get_transcript(video_id, languages=['en'])
    except Exception as e:
        print(f"Error fetching transcript: {e}")
        return ''

    # Combine all parts of the transcript and limit the text to 1500 words
    text = ' '.join([part['text'] for part in transcript])
    words = text.split()
    limited_text = ' '.join(words[:2000])

    return limited_text

# x=get_text_from_youtube('https://youtu.be/58N2N7zJGrQ')
# print(x)
def get_text_from_wikipedia(url):
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')
    content = soup.find(id='content').get_text()
    return content

def get_text_from_image(image_path):
    img = Image.open(image_path)
    text = pytesseract.image_to_string(img)
    return text