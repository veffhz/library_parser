#!/usr/bin/env python
import os
import json
import pathlib
from typing import List
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup
from requests import HTTPError, Response
from pathvalidate import sanitize_filename

from config import BOOK_DOWNLOAD_URL, BASE_URL, BOOK_URL
from config import HEADER_SEPARATOR
from exceptions import RedirectReceivedError


def extract_book_header(soup: BeautifulSoup) -> (str, str):
    """
    Extract book title from html
    :param soup: BeautifulSoup instance
    :return: Tuple of title headers
    """
    h1 = soup.select_one('div#content>h1')
    return h1.text.split(HEADER_SEPARATOR)


def extract_book_image_url(soup: BeautifulSoup) -> str:
    """
    Extract book image from html
    :param soup: BeautifulSoup instance
    :return: Book image url
    """
    img = soup.select_one('div.bookimage img')
    return img['src']


def extract_book_genres(soup: BeautifulSoup) -> List[str]:
    """
    Extract book genres from html
    :param soup: BeautifulSoup instance
    :return: List of book's genres
    """
    a_tags = soup.select('span.d_book a')
    return [a.text for a in a_tags]


def extract_book_comments(soup: BeautifulSoup) -> List[str]:
    """
    Extract book comments from html
    :param soup: BeautifulSoup instance
    :return: List of book's comments
    """
    divs = soup.select('div.texts')
    return [div.select_one('span.black').text for div in divs
            if div.select_one('span.black')]


def combine_path(filename: str, path: str, extension: str = None) -> str:
    """
    Combine path, filename and file extension
    :param filename: filename
    :param path: file path
    :param extension: file extension
    :return: Path to file
    """
    valid_filename = sanitize_filename(filename)
    if extension:
        return str(pathlib.PurePath(path, f'{valid_filename}.{extension}'))
    return str(pathlib.PurePath(path, f'{valid_filename}'))


def make_request(url: str, verify_ssl: bool = False) -> Response:
    """
    Get request to url and return response, if if status ok
    :param url: url to make request
    :param verify_ssl: Flag to check https
    :return: Response instance
    """
    response = requests.get(url, allow_redirects=False, verify=verify_ssl)
    response.raise_for_status()

    if response.is_redirect or response.is_permanent_redirect:
        raise RedirectReceivedError(response.status_code)

    return response


def download_file(url: str, filename: str, path: str, extension: str = None) -> str:
    """
    Download file with specified params
    :param url: url to download
    :param filename: file name to save file
    :param path: path to save file
    :param extension: file extension to save file
    :return: downloaded file path
    """
    print(f'begin download: {url}')

    response = make_request(url)

    file_path = combine_path(filename, path, extension)

    with open(file_path, 'wb') as file:
        file.write(response.content)

    print(f'downloaded file to {file_path}')
    return file_path


def download_book_page(page_url: str) -> dict:
    """
    Download html with book title, author, image, comments and genres
    :param page_url: url of book page
    :return: Dict with book info {'title': '', 'book_author': '', 'image_url': '', 'comments': '','genres': ''}
    """
    response = make_request(page_url)

    soup = BeautifulSoup(response.text, 'lxml')

    book_name, book_author = extract_book_header(soup)
    image_part_url = extract_book_image_url(soup)

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


def prepare_dirs(destination: str, json_path: str) -> dict:
    """
    Create destination and json path dirs
    :param destination: Path to save books files
    :param json_path: Path to save json file
    :return:
    """
    print('create download dirs if not exist\n')

    books_path = f'{destination}/books'
    images_path = f'{destination}/images'
    os.makedirs(books_path, exist_ok=True)
    os.makedirs(images_path, exist_ok=True)
    os.makedirs(os.path.dirname(json_path), exist_ok=True)
    return {
        'books_path': books_path,
        'images_path': images_path,
    }


def save_file(books_info: List[dict], json_path: str) -> None:
    """
    Save list of books info to json file
    :param books_info: List of books info
    :param json_path: Path to save json file
    :return:
    """
    with open(json_path, 'w') as export_file:
        json.dump(books_info, export_file, ensure_ascii=False, indent=4)


def download_books_list(book_ids: List[str], paths: dict, skip_txt_download: bool, skip_images_download: bool) -> List[dict]:
    """
    Iterate by books ids and download
    :param book_ids: List of books ids
    :param paths: Dict with paths for download files
    :param skip_txt_download: Flag for skip download txt files
    :param skip_images_download: Flag for skip download image files
    :return: Result list of downloaded books info
    """
    books_info = list()

    for book_id in book_ids:
        page_url = BOOK_URL.format(BASE_URL, book_id)
        file_url = BOOK_DOWNLOAD_URL.format(BASE_URL, book_id)

        try:
            print(f'\ntry lookup book: {page_url}')

            book_info = download_book_page(page_url)

            book_path = download_file(
                file_url, book_info['title'], paths['books_path'], 'txt'
            ) if not skip_txt_download else ''

            book_info['book_path'] = book_path

            image_filename = book_info['image_url'].split('/')[-1]

            img_src = download_file(
                book_info['image_url'], image_filename, paths['images_path']
            ) if not skip_images_download else ''

            book_info['img_src'] = img_src

            books_info.append(book_info)

        except (HTTPError, RedirectReceivedError) as e:
            print(e)

    return books_info
