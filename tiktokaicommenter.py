import os
import time
import unicodedata
import numpy as np
import openai
import json
import urllib
import whisper
from colorama import Fore, Back, Style
import skvideo.io
from urllib.parse import unquote
import requests
from selenium.webdriver import Keys
from TikTokApi import TikTokApi
import cv2
import undetected_chromedriver as uc
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup

configfile = json.load(open("config.json", "r"))

openai.api_key = configfile["openai_api_key"]

email = configfile["tiktok_username_email"]
password = configfile["tiktok_password"]


options = webdriver.ChromeOptions()
options.add_argument('--user-data-dir='+configfile["user_data_dir"])

driverlogged = uc.Chrome(options=options)
driverlogged.get('https://www.tiktok.com/')
searchurl = configfile["search_query"]


WebDriverWait(driverlogged,1000).until(EC.presence_of_element_located(("class name", "efubjyv0")))
def makecomment(transcript, video, description):
    completion = openai.ChatCompletion.create(
    model=configfile["openai_model_type"],
    messages=[
        {"role": "user", "content": """Make a comment for a video on the short form video platform, Tiktok.
The comment should directly appeal to the average Tiktok user, should be relevant to the video and gain the attention of the reader whom is of the characteristics of the average Tiktok user.
The goal to to get the greatest amount of likes and replies as possible, but do not make this goal obvious in the content of the response.
Strictly limit the content of the comment to at maximum, 150 characters.


This is the video:
"""+transcript+"""

The search term used to find the video was: """+unquote(searchurl.split("search?q=")[1])+"""

The description of the video is: """+description+"""

Use the content of the video data which is formated as a numpy array to help generate the comment, do not directly mention the video, you are to act as if you have watched the entirety of the video.
Also implement a description of the video which is formated as a numpy array to help generate the comment, do not directly mention the video, you are to act as you are a person whom has watched the video.
Make sure the comment is relevant to what can also be interpreted from the video, and the video itself.


This is the video:
"""+video}])
    arr = completion.choices[0]
    message = json.dumps(arr.get("message"))
    return json.loads((message).encode("utf8", "ignore"))["content"]

def transcribevideo(pathtofile):
    model = whisper.load_model("medium")
    result = model.transcribe(pathtofile, verbose=False)
    return result["text"]


def postcomment(comment, video):
    try:
        driverlogged.get(video)
        time.sleep(5)
        element = driverlogged.find_element("class name", "e1rzzhjk2")

        from selenium.webdriver.common.action_chains import ActionChains
        actions = ActionChains(driverlogged)
        actions.move_to_element(element).perform()
        actions.click(element).perform()
        actions.send_keys(comment.replace('"','')).perform()
        time.sleep(2)
        postbutton = driverlogged.find_element("class name", "e1rzzhjk6")
        actions.move_to_element(postbutton).perform()
        actions.click(postbutton).perform()
        time.sleep(3)
        print(Fore.GREEN + "Successfully posted comment: "+str(comment.encode("utf-8"))+Fore.RESET+" \nOn video: "+str(video)+Fore.RESET)
    except:
        pass

tiktok_ids = []
driver = uc.Chrome()
driver.get(searchurl)
time.sleep(3)
pageSource = driver.page_source.encode("utf-8","ignore")
try:
    driver.close()
    driver.quit()
except:
    pass
soup = BeautifulSoup(pageSource, 'html.parser')
allVids = soup.findAll("div", {"class": "e19c29qe9"})
for i in allVids: 
    try:
        if "/video/" in i.find("a")["href"]:
            tiktok_ids.append(str(i.find("a")["href"])+"|"+str(i.find("img")["src"]))
    except:
        continue

api = TikTokApi()
index = 0
for video in tiktok_ids:
    r = requests.get("https://api16-normal-c-useast1a.tiktokv.com/aweme/v1/feed/?aweme_id="+video.split("|")[0].split("/video/")[1]).json()
    urllib.request.urlretrieve(r["aweme_list"][0]["video"]["play_addr"]["url_list"][0], 'Download.mp4') 
    path = "Download.mp4"
    videodata = skvideo.io.vread(path)
    transcription = transcribevideo("Download.mp4")
    commentcreated = makecomment(str(transcription),str(videodata), str(r["aweme_list"][0]["desc"]))
    postcomment(commentcreated, video.split("|")[0])
    index+=1
