import asyncio
import os
import re

import aiohttp
import asyncpg
import psycopg2


from source.DB_SETTINGS import async_settings, settings
from random import choice

from bs4 import BeautifulSoup

from source.request_params import PROXY_TUPLE, HEADERS



BASE_URL = 'https://www.sciencedirect.com/'

SEARCH_URL_ADD = 'browse/journals-and-books?page='
SUBDOMAIN_FIND = '&contentType=JL&accessType=openAccess&accessType=containsOpenAccess&subject='


def next_proxy():
    current_proxy = choice(PROXY_TUPLE)
    return current_proxy

def next_headers():
    current_headers = choice(HEADERS)
    return current_headers


def get_all_subdomains():
    conn = psycopg2.connect(settings)
    cur = conn.cursor()
    cur.execute('SELECT name, url FROM subdomains')
    all_subdomains = []
    for record in cur:
        all_subdomains.append((record[0], record[1]))
    return all_subdomains


async def async_request(session, url):
    proxy = next_proxy()
    headers = next_headers()
    # print('Get request in ', url, 'proxy is ', proxy)
    # proxy=f'http://{proxy}',
    async with session.get(url,  headers={'user-agent':headers}, allow_redirects = True) as response:
        # print('success')
        return await response.text()


def url_generator(subdomain_url, page):
    return f'{BASE_URL}{SEARCH_URL_ADD}{page}{SUBDOMAIN_FIND}{subdomain_url}'


async def get_journals_from_subdomain(session, subdomain_name, subdomain_url):
    print(f'SUBDOMAIN IS {subdomain_name}')
    pages = 2
    current_page = 1
    all_journals_in_subdomain = {}

    while current_page <= pages:
    
        request_url = url_generator(subdomain_url, current_page)
        page_text = await async_request(session, request_url)
        if current_page == 1:
            (journals_from_one_page, pages) = await page_parser(page_text, is_first=True)
        else:
            journals_from_one_page = await page_parser(page_text)
        all_journals_in_subdomain.update(journals_from_one_page)
        current_page += 1

    
    for journal in all_journals_in_subdomain:
        print(f'Journal is {journal}   Url is {all_journals_in_subdomain[journal]}')



async def pagination_count(bs_page):
    pagination_label = bs_page.find('span', class_='pagination-pages-label')
    if pagination_label:
        re_pattern = re.compile('([0-9]+)$')
        search_result = re_pattern.search(pagination_label.text)
        return int(search_result.group())

    return 1


async def find_journals(bs_page):

    all_journals_on_page = bs_page.find_all('a', 'js-publication-title')
    journals = {}

    for journal in all_journals_on_page:
        journals[journal.get_text()] = journal.get('href')
    # print(journals)
    return journals



async def page_parser(page_text, is_first=False):
    print("Acta Biomaterialia" in page_text)
    bs_page = BeautifulSoup(page_text, 'html.parser')
    journals_dict = await find_journals(bs_page)
    if is_first:
        pages = await pagination_count(bs_page)
        return (journals_dict, pages)

    return journals_dict





async def main(subdomains):
   
    async with aiohttp.ClientSession() as session:
        tasks = []
        for subdomain in subdomains:
            print('   Creating task for subdomain ', subdomain)
            task = await asyncio.Task(get_journals_from_subdomain(session, *subdomain))
            tasks.append(task)
        loop = asyncio.get_event_loop()
        loop.run_until_complete(main(asyncio.gather(*tasks)))


if __name__ == '__main__':
    subdomains = get_all_subdomains()
    # print(f'Subdomains is {subdomains}')
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main(subdomains))
    
