import requests
from pyquery import PyQuery as pq
import logging
import re
from fake_useragent import UserAgent
import json
import os

# 电影类型id
TYPE_URL = 'https://movie.douban.com/chart'
# 电影数量
COUNT_URL = 'https://movie.douban.com/j/chart/top_list_count?type={type}&interval_id=100%3A90'
# 电影数据
INFO_URL = 'https://movie.douban.com/j/chart/top_list?type={type}&interval_id=100%3A90&start={start}&limit={limit}'
LIMIT = 20
UA = UserAgent()
TYPES = {}
FILENAME = '{type}/{type}{start}.json'

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)


def scrape_page(url):
    logging.info('scraping %s', url)
    try:
        response = requests.get(url, timeout=10, headers={'User-Agent': UA.random})
        if response.status_code == 200:
            return response
        logging.error('get invalid status code %s while scraping %s', response.status_code, url)
    except Exception:
        logging.error('error occurred while scraping %s', url, exc_info=True)


def get_type_id():
    html = scrape_page(TYPE_URL).text
    doc = pq(html)
    types = doc('div.types a')
    pattern = re.compile(r'type_name=(.*?)&type=(.*?)&', re.S)
    show = ''
    collum = 0
    for item in types.items():
        result = re.findall(pattern, item.attr('href'))
        if result:
            collum += 1
            type_name, type_id = result[0]
            TYPES[type_id] = type_name
            show += (' | ' + type_name + ' ' + type_id)
            if not collum % 6:
                show += ' |\n'
    print(show)
    while True:
        type_id = input('\n请输入你想爬取的电影类型id：')
        if type_id in TYPES:
            return type_id
        print('id不存在,请输入正确的id')


def get_movies_count(type_id):
    return scrape_page(COUNT_URL.format(type=type_id)).json().get('total')


def scrape_index(type_id, start):
    url = INFO_URL.format(type=type_id, start=start, limit=LIMIT)
    return scrape_page(url)


def save_data(data, filename):
    with open(filename, 'w')as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def main():
    type_id = get_type_id()
    type_name = TYPES[type_id]
    count = get_movies_count(type_id)
    dirname = f'./{type_name}'
    os.path.exists(dirname) or os.makedirs(dirname)
    for start in range(0, count, 20):
        response = scrape_index(type_id, start)
        if not response:
            continue
        logging.info('saving data %s %s~%s', type_name, start, start + 20)
        save_data(response.json(), FILENAME.format(type=type_name, start=start))


if __name__ == '__main__':
    main()
