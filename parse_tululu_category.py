#!/usr/bin/env python
import argparse
import re
from typing import List
from urllib.parse import urljoin

from bs4 import BeautifulSoup

from config import SCI_FI_URL, BASE_URL, PAGES_LIMIT
from tululu import make_request, run_main


def extract_book_links(soup: BeautifulSoup) -> List[str]:
    divs = soup.select('div.bookimage')
    return [div.select_one('a')['href'] for div in divs
            if div.select_one('a')]


def download_page_links(books_url: str) -> List[str]:
    response = make_request(books_url)

    soup = BeautifulSoup(response.text, 'lxml')

    links = extract_book_links(soup)

    return [urljoin(BASE_URL, part_link) for part_link in links]


def download_page_ids(books_url: str) -> List[str]:
    response = make_request(books_url)

    soup = BeautifulSoup(response.text, 'lxml')

    links = extract_book_links(soup)
    return [re.sub('[^0-9]', '', part_link) for part_link in links]


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('--start_page', help='Start page number for parse', type=int, required=True)
    parser.add_argument('--end_page', help='End page number for parse', type=int, default=PAGES_LIMIT)
    return parser.parse_args()


def main():
    args = parse_args()

    total_ids = list()
    for page_no in range(args.start_page, args.end_page):
        book_ids = download_page_ids(SCI_FI_URL.format(page=page_no))
        total_ids.extend(book_ids)

    run_main(total_ids)


if __name__ == '__main__':
    main()
