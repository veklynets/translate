import rss_parser as t1
import asyncio
import httpx

task = {i: '' for i in range(40)}

# rss_parser

async def start():
    for i in range(len(t1.rss)):
        if t1.rss[i] != '':
            task[i] = asyncio.create_task(t1.rss_parser_async(t1.httpx_client[i], 
                                                                t1.posted_q[i], t1.n_test_chars,
                                                                t1.rss[i], t1.link[i])) 
    task[len(t1.rss)+1] = asyncio.create_task(t1.my_time_async())
    
    for i in range(len(task)):
        if task[i] != '':
            await task[i]


for i in range(len(t1.rss)):
    t1.posted_q[i] = t1.deque(maxlen=200) # Очередь из уже опубликованных постов, чтобы их не дублировать     
    t1.httpx_client[i] = httpx.AsyncClient()
asyncio.run(start())
# rss_parser