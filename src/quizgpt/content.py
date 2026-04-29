import requests
from bs4 import BeautifulSoup
import validators
from youtube_transcript_api import YouTubeTranscriptApi


def check_youtube_url(input_url: str) -> bool:
    checker_url = "https://www.youtube.com/oembed?url="
    response = requests.get(checker_url + input_url, timeout=10)
    return response.status_code == 200


def get_youtube_captions(input_from_api: str) -> str:
    if "youtu.be" in input_from_api:
        video_id = input_from_api.split("/")[-1].split("?")[0]
    else:
        video_id = input_from_api.split("v=")[-1].split("&")[0]

    caption_list = YouTubeTranscriptApi.get_transcript(video_id)
    return " ".join(item["text"] for item in caption_list)


def get_website_content(input_from_api: str) -> str:
    response = requests.get(input_from_api, timeout=10)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, "html.parser")
    paragraphs = [p.get_text(separator=" ", strip=True) for p in soup.find_all("p")]
    return "\n\n".join(paragraphs).strip()


def get_content_text(input_from_api: str) -> str:
    if validators.url(input_from_api.strip()):
        if check_youtube_url(input_from_api):
            return get_youtube_captions(input_from_api)
        return get_website_content(input_from_api)

    return input_from_api.strip()
