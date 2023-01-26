import asyncio
import aiohttp
import requests as rq
from bs4 import BeautifulSoup
from aiohttp_retry import RetryClient, ExponentialRetry


categories_list = []
pagen_list = []
domain = 'https://parsinger.ru/html/'
amount = []


def get_soup(link):
    response = rq.get(link)
    response.encoding = 'utf-8'
    return BeautifulSoup(response.text, 'lxml')


def get_categories(soup):
    categories = soup.find('div', class_='nav_menu').find_all('a')
    categories = list(map(lambda x: domain + x['href'], categories))
    categories_list.extend(categories)


def get_pagen():
    for url in categories_list:
        resp = rq.get(url)
        soup_pagen = BeautifulSoup(resp.text, 'lxml')
        pagen = map(lambda x: domain + x['href'], soup_pagen.find('div', class_='pagen').find_all('a'))
        pagen_list.extend(list(pagen))


async def get_data(session, link):
    retry_options = ExponentialRetry(attempts=5)
    retry_client = RetryClient(raise_for_status=False, client_session=session, retry_options=retry_options, start_timeout=0.5)
    async with retry_client.get(link) as response:
        if response.ok:
            resp = await response.text()
            soup1 = BeautifulSoup(resp, 'lxml')
            items_cards = [domain + i['href'] for i in soup1.find_all('a', class_='name_item')]
            for item_url in items_cards:
                async with session.get(url=item_url) as response2:
                    resp2 = await response2.text()
                    soup2 = BeautifulSoup(resp2, 'lxml')
                    old_price = int(soup2.find('span', id='old_price').text.split()[0])
                    price = int(soup2.find('span', id='price').text.split()[0])
                    in_stock = int(soup2.find('span', id='in_stock').text.split(':')[-1].strip())
                    amount.append((old_price - price) * in_stock)


async def main():
    async with aiohttp.ClientSession() as session:
        tasks = []
        for link in pagen_list:
            task = asyncio.create_task(get_data(session, link))
            tasks.append(task)
        await asyncio.gather(*tasks)


soup = get_soup('https://parsinger.ru/html/index1_page_1.html')
get_categories(soup)
get_pagen()


asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
asyncio.run(main())


print(sum(amount))





