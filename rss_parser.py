import asyncio
import time
from collections import deque
import feedparser
import winsound
from datetime import datetime
import os
from gtts import gTTS
from langdetect import detect
import requests

def text_to_speech(text, language='en'):
    tts = gTTS(text=text, lang=language, slow=False)
    tts.save("output.mp3")
    os.system("start output.mp3")  # Відтворення аудіофайлу

async def my_time_async():
    while True:
        try:
            pass
        except:
            await asyncio.sleep(10)
            continue

        winsound.PlaySound('audio/Ring01.wav', winsound.SND_FILENAME)
        value = input("time  > ")
        await asyncio.sleep(60 * int(value))

def my_time_sync():
    while True:
        try:
            pass
        except:
            time.sleep(10)
            continue

        winsound.PlaySound('audio/Ring01.wav', winsound.SND_FILENAME)
        value = input("time  > ")
        time.sleep(60 * int(value))

n_test_chars = 50 # 50 первых символов от текста новости

rss = {
    0 : 'rss censor: EN',
    1 : '',
    2 : '',
    3 : '',
    4 : '',
    5 : 'rss ГОЛОС АМЕРИКИ',
    6 : '', #'rss Радіо Свобода',
    7 : 'rss Украина - ГОЛОС АМЕРИКИ',
    8 : 'rss Наука, технологии и инновации - ГОЛОС АМЕРИКИ',
    9 : 'rss Экономика - ГОЛОС АМЕРИКИ',
    10 : 'rss Freelance.ua',
    11 : '',
    12 : 'rss Українська правда',   
    }

link = {
    0 : 'https://assets.censor.net/rss/censor.net/rss_en_news.xml',
    1 : '',
    2 : '',
    3 : '',
    4 : '',
    5 : 'https://www.golosameriki.com/api/zgj_te_yyq',
    6 : 'https://www.radiosvoboda.org/api/',
    7 : 'https://www.golosameriki.com/api/zu$_oeptyp',
    8 : 'https://www.golosameriki.com/api/zp$__e-vyy',
    9 : 'https://www.golosameriki.com/api/zp-_ve-yyt',
    10 : 'https://freelance.ua/orders/rss?t=1&cat_id=10&sub_id=0',
    11 : '',
    12 : 'https://www.pravda.com.ua/eng/rss/',
    13 : '',
    14 : '',
    15 : '',
    16 : '',
    17 : '',
    18 : '',
    19 : '',
    20 : '',
    }

posted_q  = {i: '' for i in range(20)}
httpx_client ={i: '' for i in range(20)}

async def rss_parser_async(httpx_client, posted_q, n_test_chars, rss_name, rss_link, update=1, first_start=True, send_message_func=None):
    '''parser of rss'''

    while True:
        try:
            response = await httpx_client.get(rss_link)
        except:
            await asyncio.sleep(10)
            continue

        feed = feedparser.parse(response.text)

        for entry in feed.entries[::-1]:
            summary = entry['summary']
            title = entry['title']

            now = datetime.now()
            current_time = now.strftime("%H:%M:%S")

            if '<div' or '<blockquote' in summary:
                news_text = f'{title}'
            else:
               news_text = f'{title}\n{summary}'

            if 'https://www.pravda.com.ua/rss/' == rss_link:
                news_text = news_text.encode('cp1251').decode('utf-8')

            head = news_text[:n_test_chars].strip()

            if head in posted_q:
                continue


            print_lock = asyncio.Lock()
            if send_message_func is None:
                if first_start == False:
                    async with print_lock: # syncc print fot all tasks
                        winsound.PlaySound('audio/Speech Misrecognition.wav', winsound.SND_FILENAME)
                        print(current_time, '', rss_name, '\n', news_text, '\n')
                        text_to_speech(news_text, language=detect(news_text))
                        await asyncio.sleep(30)
            else:
                await send_message_func(f'site busy\n{news_text}')

            posted_q.appendleft(head)

        first_start = False
        await asyncio.sleep(60 * update)

def rss_parser_sync(posted_q, n_test_chars, rss_name, rss_link, update=1, first_start=True, send_message_func=None):
    '''synchronous parser of rss'''

    while True:
        try:
            response = requests.get(rss_link)
        except:
            time.sleep(10)
            continue

        feed = feedparser.parse(response.text)

        for entry in feed.entries[::-1]:
            summary = entry['summary']
            title = entry['title']

            now = datetime.now()
            current_time = now.strftime("%H:%M:%S")

            if '<div' or '<blockquote' in summary:
                news_text = f'{title}'
            else:
               news_text = f'{title}\n{summary}'

            if 'https://www.pravda.com.ua/rss/' == rss_link:
                news_text = news_text.encode('cp1251').decode('utf-8')

            head = news_text[:n_test_chars].strip()

            if head in posted_q:
                continue

            if send_message_func is None:
                if first_start == False:
                    winsound.PlaySound('audio/Speech Misrecognition.wav', winsound.SND_FILENAME)
                    print(current_time, '', rss_name, '\n', news_text, '\n')
                    #text_to_speech(news_text, language=detect(news_text))
                    #time.sleep(30)
                    time.sleep(10)
            else:
                send_message_func(f'site busy\n{news_text}')

            posted_q.appendleft(head)

        first_start = False
        time.sleep(60 * update)

    
if __name__ == "__main__":
    # my_time_sync()
    rss_parser_sync(posted_q[0], n_test_chars, deque(maxlen=200), link[0])