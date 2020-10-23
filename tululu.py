#!/usr/bin/env python
import os
import pathlib
from typing import List
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup
from pathvalidate import sanitize_filename
from requests import HTTPError

from helper import BookUrl, BookInfo
from config import PATH_DOWNLOADS, HEADER_SEPARATOR, IMAGES_DOWNLOADS


def extract_book_header(soup: BeautifulSoup) -> (str, str):
    h1 = soup.select_one('div#content>h1')
    return h1.text.split(HEADER_SEPARATOR)


def extract_book_image(soup: BeautifulSoup) -> str:
    img = soup.select_one('div.bookimage img')
    return img['src']


def extract_book_genre(soup: BeautifulSoup) -> str:
    a = soup.select_one('span.d_book a')
    return a.text


def extract_book_comments(soup: BeautifulSoup) -> List[str]:
    divs = soup.select('div.texts')
    return [div.select_one('span.black').text for div in divs
            if div.select_one('span.black')]


def combine_path(filename: str, path: str, extension: str = None):
    valid_filename = sanitize_filename(filename)
    if extension:
        return pathlib.PurePath(path, f'{valid_filename}.{extension}')
    return pathlib.PurePath(path, f'{valid_filename}')


def make_request(url):
    response = requests.get(url, allow_redirects=False)
    response.raise_for_status()

    if response.is_redirect or response.is_permanent_redirect:
        print(f'redirect found: code {response.status_code}, stop.', )
        raise RuntimeError()

    return response


def download_file(url: str, filename: str, path: str, extension: str = None):
    response = make_request(url)

    filepath = combine_path(filename, path, extension)

    with open(filepath, 'wb') as file:
        file.write(response.content)

    print(f'downloaded file: {filepath}')


def download_page(book_url: BookUrl) -> BookInfo:
    response = make_request(book_url.page)

    soup = BeautifulSoup(response.text, 'lxml')

    book_name, book_author = extract_book_header(soup)
    image_part_url = extract_book_image(soup)

    image_url = urljoin(book_url.page, image_part_url)

    comments = extract_book_comments(soup)
    genre = extract_book_genre(soup)

    return BookInfo(
        book_name.strip(),
        book_author.strip(),
        book_url,
        image_url
    )


def prepare_dirs():
    print(f'create download dirs if not exist\n')
    os.makedirs(PATH_DOWNLOADS, exist_ok=True)
    os.makedirs(IMAGES_DOWNLOADS, exist_ok=True)


def main():
    prepare_dirs()

    for no in range(1, 11):
        book_url = BookUrl(no)
        try:
            print(f'\ntry lookup book: {book_url.page}')
            book_info = download_page(book_url)
            print(f'download book: {book_url.file}')
            download_file(book_info.book_url.file, book_info.make_book_name(), PATH_DOWNLOADS, 'txt')
            print(f'download image: {book_info.image_url}')
            download_file(book_info.image_url, book_info.make_image_name(), IMAGES_DOWNLOADS)
        except (HTTPError, RuntimeError) as e:
            print(e)


if __name__ == '__main__':
    main()
