#!/usr/bin/env python
import re
import argparse
from typing import List
from urllib.parse import urljoin

from bs4 import BeautifulSoup

from config import SCI_FI_URL, BASE_URL, PAGES_LIMIT
from config import DEFAULT_DESTINATION_FOLDER, DEFAULT_JSON_PATH, DEFAULT_EXPORT_FILENAME
from tululu import make_request, run_main


def extract_book_links(soup: BeautifulSoup) -> List[str]:
    divs = soup.select('div.bookimage')
    return [div.select_one('a')['href'] for div in divs
            if div.select_one('a')]


def download_page_links(books_url: str) -> List[str]:
    """
    Deprecated, not used
    :param books_url:
    :return:
    """
    response = make_request(books_url)

    soup = BeautifulSoup(response.text, 'lxml')

    links = extract_book_links(soup)

    return [urljoin(BASE_URL, link) for link in links]


def download_page_ids(books_url: str) -> List[str]:
    response = make_request(books_url)

    soup = BeautifulSoup(response.text, 'lxml')

    links = extract_book_links(soup)
    return [re.sub('[^0-9]', '', link) for link in links]


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('--start_page', help='Start page number for parse', type=int, required=True)
    parser.add_argument('--end_page', help='End page number for parse', type=int, default=PAGES_LIMIT)
    parser.add_argument('--destination', help='Destination folder for download',
                        type=str, default=DEFAULT_DESTINATION_FOLDER)
    parser.add_argument('--export_filename', help='Filename for json file with results',
                        type=str, default=DEFAULT_EXPORT_FILENAME)
    parser.add_argument('--json_path', help='Destination folder for save result',
                        type=str, default=DEFAULT_JSON_PATH)
    parser.add_argument('--skip_imgs', default=False, action='store_true')
    parser.add_argument('--skip_txt', default=False, action='store_true')
    return parser.parse_args()


def main():
    args = parse_args()

    total_book_ids = list()
    for page_no in range(args.start_page, args.end_page):
        book_ids = download_page_ids(SCI_FI_URL.format(page=page_no))
        total_book_ids.extend(book_ids)

    json_path = f'{args.json_path}/{args.export_filename}'

    run_main(
        total_book_ids, args.destination, args.skip_txt,
        args.skip_imgs, json_path
    )


if __name__ == '__main__':
    main()
