import json
import time
import os
import re
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from tiktokvoice import tts
import requests
import subprocess
from openai import OpenAI

# Configuration
API_KEY = ''
PROMPT = """
Create a video on how to make money with digital marketing.
"""
SAVE_DIRECTORY = 'media\\video1'
STOCK_VIDEO_URL_TEMPLATE = 'https://www.pexels.com/search/videos/{}/?orientation=portrait'
BACKGROUND_MUSIC_URL_TEMPLATE = 'https://pixabay.com/music/search/{}/'
WAIT_TIME = 1  # seconds
DOWNLOAD_WAIT_TIME = 1  # seconds
OUTPUT_VIDEO_PATH = 'final_video.mp4'
TARGET_RESOLUTION = "1080x1920"
FONT_PATH = 'fonts/futurabold.ttf'
FONT_SIZE = 70
FONT_COLOR = 'white'
BACKGROUND_MUSIC_VOLUME = 0.4  # Volume for background music (0 to 1)
DOWNLOAD_DIRECTORY = os.getcwd() + '\\' + SAVE_DIRECTORY
VOICE = 'en_uk_003'

client = OpenAI(api_key=API_KEY)

chrome_prefs = {
    "profile.default_content_settings.popups": 0,
    "download.default_directory": DOWNLOAD_DIRECTORY,  # IMPORTANT - ENDING SLASH VITAL
    "directory_upgrade": True
}

options = Options()
options.add_experimental_option("prefs", chrome_prefs)

def initialize_webdriver():
    """Initialize the Chrome WebDriver."""
    return webdriver.Chrome(options=options)

def fetch_video_data(prompt):
    """Fetch video data from OpenAI API, including background music search phrases."""
    completion = client.chat.completions.create(
        model="gpt-4-turbo",
        response_format={"type": "json_object"},
        messages=[
            {
                "role": "user",
                "content": (
                    "You are a content generation assistant. Your task is to help users find suitable stock videos, images, and background music for their video projects. Make sure that each of the phrases are very different so that you dont end up with multiple of the same content."
                    "You will receive a video description prompt, and based on this, you will generate search phrases for video segments or images that can be searched on stock video and image sites. Make the phrases very short (two words)."
                    "Additionally, you will provide overlay text to be used for each segment and suggest appropriate background music. \n\n"
                    "Output the results in JSON format with the following schema:\n\n"
                    "{\n"
                    "  \"type\": \"object\",\n"
                    "  \"properties\": {\n"
                    "    \"segments\": {\n"
                    "      \"type\": \"array\",\n"
                    "      \"items\": {\n"
                    "        \"type\": \"object\",\n"
                    "        \"properties\": {\n"
                    "          \"segment\": {\n"
                    "            \"type\": \"string\",\n"
                    "            \"description\": \"Brief description of the video segment\"\n"
                    "          },\n"
                    "          \"content_type\": {\n"
                    "            \"type\": \"string\",\n"
                    "            \"description\": \"Specify whether the content should be a video or an image\"\n"
                    "          },\n"
                    "          \"search_phrase\": {\n"
                    "            \"type\": \"string\",\n"
                    "            \"description\": \"Search phrase for stock video or image sites\"\n"
                    "          },\n"
                    "          \"overlay_text\": {\n"
                    "            \"type\": \"string\",\n"
                    "            \"description\": \"Text to overlay on the video segment\"\n"
                    "          }\n"
                    "        },\n"
                    "        \"required\": [\"segment\", \"content_type\", \"search_phrase\", \"overlay_text\"]\n"
                    "      }\n"
                    "    },\n"
                    "    \"background_music_search_phrase\": {\n"
                    "      \"type\": \"string\",\n"
                    "      \"description\": \"Search phrase for background music that fits the overall theme of the video\"\n"
                    "    }\n"
                    "  },\n"
                    "  \"required\": [\"segments\", \"background_music_search_phrase\"]\n"
                    "}\n\n"
                    "Example Input: \"Create a promotional video for a travel agency highlighting a beach destination, local culture, and adventure activities.\"\n\n"
                    "Example Output:\n"
                    "{\n"
                    "  \"segments\": [\n"
                    "    {\n"
                    "      \"segment\": \"Opening scene with a beautiful sunrise over the ocean.\",\n"
                    "      \"content_type\": \"video\",\n"
                    "      \"search_phrase\": \"sunrise over ocean\",\n"
                    "      \"overlay_text\": \"Discover Your Perfect Beach Getaway\"\n"
                    "    },\n"
                    "    {\n"
                    "      \"segment\": \"Tourists enjoying the beach and sunbathing.\",\n"
                    "      \"content_type\": \"video\",\n"
                    "      \"search_phrase\": \"people sunbathing on beach\",\n"
                    "      \"overlay_text\": \"Relax and Unwind\"\n"
                    "    },\n"
                    "    {\n"
                    "      \"segment\": \"Local market with vibrant stalls and fresh produce.\",\n"
                    "      \"content_type\": \"video\",\n"
                    "      \"search_phrase\": \"local market with stalls\",\n"
                    "      \"overlay_text\": \"Experience the Local Culture\"\n"
                    "    },\n"
                    "    {\n"
                    "      \"segment\": \"Adventure activities like surfing and parasailing.\",\n"
                    "      \"content_type\": \"video\",\n"
                    "      \"search_phrase\": \"surfing and parasailing\",\n"
                    "      \"overlay_text\": \"Thrilling Adventures Await\"\n"
                    "    },\n"
                    "    {\n"
                    "      \"segment\": \"Closing scene with a stunning beach sunset.\",\n"
                    "      \"content_type\": \"video\",\n"
                    "      \"search_phrase\": \"beach sunset\",\n"
                    "      \"overlay_text\": \"Book Your Dream Vacation Today\"\n"
                    "    }\n"
                    "  ],\n"
                    "  \"background_music_search_phrase\": \"relaxing tropical music\"\n"
                    "}\n\n"
                    "Use this format and schema to generate appropriate search phrases, overlay text, and background music search phrase based on the given video description prompt."
                )
            },
            {
                "role": "user",
                "content": prompt
            }
        ]
    )
    
    return json.loads(completion.choices[0].message.content)


def get_downloaded_filename(directory, timeout=300):
    seconds = 0
    dl_wait = True
    files_before = set(os.listdir(directory))  # Existing files in the directory

    while dl_wait and seconds < timeout:
        time.sleep(1)
        files_after = set(os.listdir(directory))  # Updated list of files in directory
        new_files = files_after - files_before    # Check for new files
        if new_files:  # New file has been downloaded
            for file in new_files:
                if not file.endswith('.crdownload'):  # Ensure the file is fully downloaded
                    dl_wait = False
                    return file  # Return the name of the downloaded file
        seconds += 1

    return None

def download_file(url, save_directory, file_name=None):
    """Download a file from the given URL and save it to the specified directory."""
    try:
        if not os.path.exists(save_directory):
            os.makedirs(save_directory)
        
        response = requests.get(url, stream=True)
        
        if response.status_code == 200:
            if not file_name:
                file_name = url.split('/')[-2] + ".mp4"
            save_path = os.path.join(save_directory, file_name)
            
            with open(save_path, 'wb') as file:
                for chunk in response.iter_content(chunk_size=8192):
                    file.write(chunk)
            print(f"File downloaded successfully and saved to {save_path}")
            return save_path
        else:
            print(f"Failed to download file. HTTP status code: {response.status_code}")
    except Exception as e:
        print(f"An error occurred: {e}")
    return None

def search_and_download_video(segment, driver):
    """Search for a video based on the search phrase and download a random result."""
    phrase = segment['search_phrase']
    url = STOCK_VIDEO_URL_TEMPLATE.format(phrase)
    driver.get(url)
    print(url)
    time.sleep(WAIT_TIME)
    
    div_elements = driver.find_elements(By.CSS_SELECTOR, "div[data-testid='item']")
    if div_elements:
        #div_element = random.choice(div_elements)
        div_element = div_elements[0]
        try:
            download_button = div_element.find_element(By.CSS_SELECTOR, "a[title='Download']")
            download_url = download_button.get_attribute('href')
            downloaded_file_path = download_file(download_url, SAVE_DIRECTORY)
            if downloaded_file_path:
                return {'file_path': downloaded_file_path, 'overlay_text': segment['overlay_text']}
        except Exception as e:
            print(f"Error downloading video for phrase '{phrase}': {e}")
    return None

def search_and_download_background_music(driver, search_phrase):
    """Search for background music based on the search phrase and download it."""
    url = BACKGROUND_MUSIC_URL_TEMPLATE.format(search_phrase)
    driver.get(url)
    time.sleep(1)
    driver.find_element(By.XPATH, '//button[@id="onetrust-accept-btn-handler"]').click()
    download_button = driver.find_element(By.XPATH, '//button[@aria-label="Download"]')
    download_button.click()
    downloaded_file = get_downloaded_filename(DOWNLOAD_DIRECTORY)
    if downloaded_file:
        print("Downloaded file:", downloaded_file)
        save_path = os.path.join(DOWNLOAD_DIRECTORY, downloaded_file)
        return save_path
    else:
        print("Download failed or took too long.")
        raise Exception

def search_and_download_videos(video_data, driver):
    """Search for videos based on video data and download them sequentially."""
    downloaded_files = []
    for segment in video_data['segments']:
        result = search_and_download_video(segment, driver)
        if result:
            downloaded_files.append(result)
    return downloaded_files

def get_audio_duration(file_path):
    """Use FFmpeg to get the duration of an audio file."""
    result = subprocess.run(['ffmpeg', '-i', file_path, '-f', 'null', '-'], stderr=subprocess.PIPE, text=True)
    duration_match = re.search(r'Duration: (\d{2}):(\d{2}):(\d{2}\.\d{2}),', result.stderr)
    if duration_match:
        hours, minutes, seconds = map(float, duration_match.groups())
        total_seconds = hours * 3600 + minutes * 60 + seconds
        return total_seconds
    else:
        return 0

def merge_videos_with_text_ffmpeg(video_segments, music_path, output_path):
    """Merge videos and overlay text using FFmpeg, with background music and TTS audio for each video segment."""
    filter_complex = []
    inputs = []

    # Include the music file as an input (index 0)
    inputs.append(f"-i {music_path}")

    for i, segment in enumerate(video_segments):
        input_video = segment['file_path']
        text = segment['overlay_text']
        tts_audio_file = f"{SAVE_DIRECTORY}/segment_{i}_audio.mp3"
        tts(text, VOICE, tts_audio_file)

        # Add video and TTS audio to inputs
        inputs.append(f"-i {input_video}")
        inputs.append(f"-i {tts_audio_file}")

        # Get audio duration to set the video trim duration
        audio_duration = get_audio_duration(tts_audio_file)

        # Apply filters to video and scale, trimming to the duration of the audio
        video_index = 2 * i + 1
        audio_index = video_index + 1
        filter_complex.append(f"[{video_index}:v]scale=1080x1920,drawtext=text='{text}':fontfile={FONT_PATH}:fontcolor={FONT_COLOR}:fontsize={FONT_SIZE}:x=(w-text_w)/2:y=(h-text_h)/2,trim=duration={audio_duration}[v{i}]")
        filter_complex.append(f"[{audio_index}:a]asetpts=PTS-STARTPTS[a{i}]")

    concat_str = ''.join(f"[v{i}][a{i}]" for i in range(len(video_segments)))
    filter_complex.append(f"{concat_str}concat=n={len(video_segments)}:v=1:a=1[outv][outa]")

    filter_complex.append(f"[0:a]aformat=sample_fmts=fltp:sample_rates=44100:channel_layouts=stereo,volume={BACKGROUND_MUSIC_VOLUME}[bgmusic];[bgmusic][outa]amix=inputs=2:duration=shortest[audio]")

    command = f"ffmpeg {' '.join(inputs)} -filter_complex \"{';'.join(filter_complex)}\" -map \"[outv]\" -map \"[audio]\" -y {output_path} -shortest"
    
    subprocess.run(command, shell=True, check=True)

if __name__ == "__main__":
    driver = initialize_webdriver()
    
    try:
        video_data = fetch_video_data(PROMPT)
        video_segments = search_and_download_videos(video_data, driver)
        background_music_path = search_and_download_background_music(driver, video_data['background_music_search_phrase'])
        merge_videos_with_text_ffmpeg(video_segments, background_music_path, OUTPUT_VIDEO_PATH)
    finally:
        driver.quit()
