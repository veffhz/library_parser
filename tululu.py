#!/usr/bin/env python
import os
import json
import pathlib
from typing import List
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup
from requests import HTTPError
from pathvalidate import sanitize_filename

from config import BOOK_DOWNLOAD_URL, BASE_URL, BOOK_URL
from config import BOOK_PATH_DOWNLOADS, IMAGE_PATH_DOWNLOADS
from config import JSON_PATH, SKIP_IMGS, SKIP_TXT, HEADER_SEPARATOR


def extract_book_header(soup: BeautifulSoup) -> (str, str):
    h1 = soup.select_one('div#content>h1')
    return h1.text.split(HEADER_SEPARATOR)


def extract_book_image(soup: BeautifulSoup) -> str:
    img = soup.select_one('div.bookimage img')
    return img['src']


def extract_book_genres(soup: BeautifulSoup) -> List[str]:
    a_tags = soup.select('span.d_book a')
    return [a.text for a in a_tags]


def extract_book_comments(soup: BeautifulSoup) -> List[str]:
    divs = soup.select('div.texts')
    return [div.select_one('span.black').text for div in divs
            if div.select_one('span.black')]


def combine_path(filename: str, path: str, extension: str = None) -> str:
    valid_filename = sanitize_filename(filename)
    if extension:
        return str(pathlib.PurePath(path, f'{valid_filename}.{extension}'))
    return str(pathlib.PurePath(path, f'{valid_filename}'))


def make_request(url):
    response = requests.get(url, allow_redirects=False, verify=False)
    response.raise_for_status()

    if response.is_redirect or response.is_permanent_redirect:
        print(f'redirect found: code {response.status_code}, stop.', )
        raise RuntimeError()

    return response


def download_file(url: str, filename: str, path: str, extension: str = None) -> str:
    print(f'begin download: {url}')

    response = make_request(url)

    file_path = combine_path(filename, path, extension)

    with open(file_path, 'wb') as file:
        file.write(response.content)

    print(f'downloaded file to {file_path}')
    return file_path


def download_book_page(page_url: str) -> dict:
    response = make_request(page_url)

    soup = BeautifulSoup(response.text, 'lxml')

    book_name, book_author = extract_book_header(soup)
    image_part_url = extract_book_image(soup)

    image_url = urljoin(page_url, image_part_url)

    comments = extract_book_comments(soup)
    genres = extract_book_genres(soup)

    return {
        'title': book_name.strip(),
        'book_author': book_author.strip(),
        'image_url': image_url,
        'comments': comments,
        'genres': genres
    }


def prepare_dirs():
    print('create download dirs if not exist\n')
    os.makedirs(BOOK_PATH_DOWNLOADS, exist_ok=True)
    os.makedirs(IMAGE_PATH_DOWNLOADS, exist_ok=True)


def save_file(books_info: List[dict]):
    with open(JSON_PATH, 'w') as export_file:
        json.dump(books_info, export_file, ensure_ascii=False, indent=4)


def make_image_name(image_url) -> str:
    return image_url.split('/')[-1]


def work_loop(ids):
    books_info = list()

    for book_id in ids:
        page_url = BOOK_URL.format(BASE_URL, book_id)
        file_url = BOOK_DOWNLOAD_URL.format(BASE_URL, book_id)

        try:
            print(f'\ntry lookup book: {page_url}')

            book_info = download_book_page(page_url)

            book_path = download_file(
                file_url, book_info['title'], BOOK_PATH_DOWNLOADS, 'txt'
            ) if not SKIP_TXT else ''

            book_info['book_path'] = book_path

            img_src = download_file(
                book_info['image_url'], make_image_name(book_info['image_url']), IMAGE_PATH_DOWNLOADS
            ) if not SKIP_IMGS else ''

            book_info['img_src'] = img_src

            books_info.append(book_info)

        except (HTTPError, RuntimeError) as e:
            print(e)

    return books_info


def run_main(ids):
    prepare_dirs()
    books_info = work_loop(ids)
    save_file(books_info)
