# option = input("> ")
        # if (option == "6"):
        #     pass
        # if (option == "6"):
        #     try:
        #         volume = int(input("Введіть гучність (0 - 100): "))
        #     except ValueError:
        #         print("Помилка: Будь ласка, введіть число.")
        # if (option == "8"):
        #     print("Вихід...")
        #     exit(0)

        #     while keyboard.is_pressed('alt'):
        #         time.sleep(REAC_SYS)
        #         if keyboard.is_pressed('q'):
        #             if status == 'off':
        #                 "do nothing"
        #                 status = 'on'

# App with a green ball in the center that moves when you press the HAT buttons

                #self.shutdown() # Викликаємо метод для чистого закриття


DEBUG = False  # True = sync, False = async

def process_feed(feed, posted_q, n_test_chars, rss_name, rss_link, first_start, send_message_func=None):
    from datetime import datetime
    import winsound

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
            if not first_start:
                winsound.PlaySound('audio/Speech Misrecognition.wav', winsound.SND_FILENAME)
                print(current_time, '', rss_name, '\n', news_text, '\n')
        else:
            # Для sync-версії send_message_func не використовується
            pass

        posted_q.appendleft(head)

# --- Асинхронний метод ---
async def rss_parser_async(httpx_client, posted_q, n_test_chars, rss_name, rss_link, update=1, first_start=True, send_message_func=None):
    while True:
        try:
            response = await httpx_client.get(rss_link)
        except:
            await asyncio.sleep(10)
            continue

        import feedparser
        feed = feedparser.parse(response.text)
        process_feed(feed, posted_q, n_test_chars, rss_name, rss_link, first_start, send_message_func)
        first_start = False
        await asyncio.sleep(60 * update)

# --- Синхронний метод ---
def rss_parser_sync(httpx_client, posted_q, n_test_chars, rss_name, rss_link, update=1, first_start=True):
    import feedparser
    while True:
        try:
            response = httpx_client.get(rss_link)
        except:
            time.sleep(10)
            continue

        feed = feedparser.parse(response.text)
        process_feed(feed, posted_q, n_test_chars, rss_name, rss_link, first_start)
        first_start = False
        time.sleep(60 * update)

# --- Запуск ---
if __name__ == "__main__":
    from collections import deque
    import httpx

    for i in range(len(rss)):
        posted_q[i] = deque(maxlen=200)
        if DEBUG:
            httpx_client[i] = httpx.Client()
        else:
            httpx_client[i] = httpx.AsyncClient()

    if DEBUG:
        # Синхронний запуск
        for i in range(len(rss)):
            if rss[i] != '':
                rss_parser_sync(httpx_client[i], posted_q[i], n_test_chars, rss[i], link[i])
    else:
        # Асинхронний запуск
        async def start():
            for i in range(len(rss)-1):
                if rss[i] != '':
                    task[i] = asyncio.create_task(rss_parser_async(httpx_client[i], posted_q[i], n_test_chars, rss[i], link[i]))
            task[len(rss)-1] = asyncio.create_task(my_time())
            for i in range(len(rss)):
                if rss[i] != '':
                    await task[i]
        asyncio.run(start())