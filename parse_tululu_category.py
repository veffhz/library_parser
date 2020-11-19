#!/usr/bin/env python
import re
import argparse
from typing import List

from bs4 import BeautifulSoup

from config import SCI_FI_URL, PAGES_LIMIT
from config import DEFAULT_DESTINATION_FOLDER, DEFAULT_JSON_PATH, DEFAULT_EXPORT_FILENAME
from tululu import make_request, prepare_dirs, work_loop, save_file


def extract_book_links(soup: BeautifulSoup) -> List[str]:
    """
    Extract a tags from page html
    :param soup: BeautifulSoup instance
    :return: List of books urls
    """
    divs = soup.select('div.bookimage')
    return [div.select_one('a')['href'] for div in divs
            if div.select_one('a')]


def download_page_ids(books_url: str) -> List[str]:
    """
    Download books id's from books url
    :param books_url: Book url
    :return: List of books ids
    """
    response = make_request(books_url)

    soup = BeautifulSoup(response.text, 'lxml')

    links = extract_book_links(soup)
    return [re.sub(r'[^0-9]', '', link) for link in links]


def parse_args() -> argparse.Namespace:
    """
    Parse script arguments
    :return: namespace instance with args attributes
    """
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
    for page_number in range(args.start_page, args.end_page):
        book_ids = download_page_ids(SCI_FI_URL.format(page=page_number))
        total_book_ids.extend(book_ids)

    json_path = f'{args.json_path}/{args.export_filename}'

    paths = prepare_dirs(args.destination, json_path)
    books_info = work_loop(total_book_ids, paths, args.skip_txt, args.skip_imgs)
    save_file(books_info, json_path)


if __name__ == '__main__':
    main()
