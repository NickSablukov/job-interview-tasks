"""
    Поиск телефонных номеров на html страницах
    (писался после работы, сымарное время 1.5-2 часа + пол часика тестирование)

    перед работой поставь aiohttp beautifulsoup4

    `pip3 install aiohttp beautifulsoup4`

"""

import asyncio
import logging
import ssl
import re
import sys
import aiohttp
import typing

from bs4 import BeautifulSoup

MOSCOW_CODE = 499

logging.basicConfig(
    format='%(levelname)s \t: %(message)s',
    stream=sys.stdout, level=logging.INFO
)
logger = logging.getLogger()

# Тут еще стоит подумать, я написал регялярку, но по хорошему бы просмотреть список кодов россии и проверять
# через него
# С кодом города или сотового оператора, обязательно с 7 или 8
# Неведомая магия с регулярками, но с ними всегда так )))
phone_format = re.compile(
    "((8|7)( | |-|\()*\d{3}( | |-|\))*" + '( | |-|\))*'.join(['\d'] * 7) + ')|(( | |-|)*(\d{3}( | |-|\))*\d{2}( | |-|\))\d{2}))'
)


async def find_numbers(link: typing.AnyStr, numbers_catalog: typing.Dict):

    logging.info('Working from "%s"' % link)

    try:
        numbers = numbers_catalog.setdefault(link, set())
        async with aiohttp.ClientSession() as session:
            response = await session.get(link, ssl=ssl.SSLContext())
            html_content = await response.read()

            text = _clear_html(html_content)
            phone_numbers = [_clean_phone(n[0]) for n in phone_format.findall(text) if n[0]]
            numbers.update(phone_numbers)

    except Exception as e:
        logger.exception('Ошибка при обработке "%s"' % link)


def _clear_html(html):
    # Тут можно поиграться, откуда брать номера и тд, я убираю скрипт, а то дергал не то

    not_search_tags = ('script',)
    soup = BeautifulSoup(html, features="html.parser")
    for tag_name in not_search_tags:
        for el in soup(tag_name):
            el.decompose()

    text = soup.get_text()
    text = text.replace('\xc2\xa0', '')

    return text


def _clean_phone(value: typing.AnyStr, prefix: typing.AnyStr='+7'):
    phone_number = re.sub('\D', '', value)
    if len(phone_number) == 7:
        phone_number = '%s%s' % (MOSCOW_CODE, phone_number)

    phone_number = phone_number[-10:]
    return prefix + phone_number


if __name__ == '__main__':

    # Ссылок еще накидал для теста
    links = [
        'https://hands.ru/company/about',
        'https://repetitors.info',
        'http://aleksandrovsk-sakh.spravker.ru/denezhnye-perevody/',
        'https://www.topnomer.ru/mts/number/direct/',
        'https://www.topnomer.ru/blog/mobilnye-nomera-rossii-kody-po-regionam.html',
        'https://www.iphones.ru/iNotes/330467',
        'https://www.estaxi.ru/taxi/15616',
        'http://webstyle.sfu-kras.ru/napisanie-nomerov-telefonov'
    ]

    loop = asyncio.get_event_loop()
    catalog = {}

    logging.info('Start  phone number downloader for %s links' % len(links))
    tasks = [loop.create_task(find_numbers(link, catalog)) for link in links]
    wait_tasks = asyncio.wait(tasks)

    try:
        loop.run_until_complete(wait_tasks)
    finally:
        loop.close()

    logger.info('Result:')
    for link, phones in catalog.items():
        logger.info('%s' % link)
        for phone in phones:
            logger.info('%s' % phone)

