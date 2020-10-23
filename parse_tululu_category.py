#!/usr/bin/env python
from typing import List
from urllib.parse import urljoin

from bs4 import BeautifulSoup

from config import SCI_FI_URL, BASE_URL
from tululu import make_request


def extract_book_links(soup: BeautifulSoup) -> List[str]:
    divs = soup.select('div.bookimage')
    return [div.select_one('a')['href'] for div in divs
            if div.select_one('a')]


def download_page(books_url: str) -> List[str]:
    response = make_request(books_url)

    soup = BeautifulSoup(response.text, 'lxml')

    links = extract_book_links(soup)

    return [urljoin(BASE_URL, part_link) for part_link in links]


def main(pages_limit=4):
    total_links = list()
    for page_no in range(1, pages_limit + 1):
        book_links = download_page(SCI_FI_URL.format(page=page_no))
        total_links.extend(book_links)


if __name__ == '__main__':
    main()
