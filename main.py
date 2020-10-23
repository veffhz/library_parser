#!/usr/bin/env python
import os
import pathlib

import requests
from bs4 import BeautifulSoup
from pathvalidate import sanitize_filename
from requests import HTTPError

from helper import BookUrl, BookInfo
from config import PATH_DOWNLOADS, HEADER_SEPARATOR


def extract_book_header(text: str) -> (str, str):
    soup = BeautifulSoup(text, 'lxml')
    h1 = soup.select_one('div#content>h1')
    return h1.text.split(HEADER_SEPARATOR)


def combine_path(filename, path):
    valid_filename = sanitize_filename(filename)
    return pathlib.PurePath(path, f'{valid_filename}.txt')


def download_txt(book_info: BookInfo):
    response = requests.get(book_info.book_url.file, allow_redirects=False)
    response.raise_for_status()

    if response.is_redirect or response.is_permanent_redirect:
        print(f'redirect found: code {response.status_code}, stop.\n', )
        raise RuntimeError()

    filepath = combine_path(book_info.make_book_name(), PATH_DOWNLOADS)

    with open(filepath, 'wb') as file:
        file.write(response.content)

    print('done\n')


def download_page(book_url: BookUrl) -> BookInfo:
    response = requests.get(book_url.page, allow_redirects=False)
    response.raise_for_status()

    if response.is_redirect or response.is_permanent_redirect:
        print(f'redirect found: code {response.status_code}, stop.\n', )
        raise RuntimeError()

    book_name, book_author = extract_book_header(response.text)
    return BookInfo(book_name.strip(), book_author.strip(), book_url)


def main():
    print(f'create download dir {PATH_DOWNLOADS} if not exist\n')
    os.makedirs(PATH_DOWNLOADS, exist_ok=True)

    for no in range(1, 11):
        book_url = BookUrl(no)
        print(f'try lookup book: {book_url.page}')
        try:
            book_info = download_page(book_url)
            download_txt(book_info)
        except (HTTPError, RuntimeError) as e:
            print(e)


if __name__ == '__main__':
    main()
