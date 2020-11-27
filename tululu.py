import os
import json
import pathlib
import uuid
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
    """Extract book title from html."""
    h1 = soup.select_one('div#content>h1')
    return h1.text.split(HEADER_SEPARATOR)


def extract_book_image_url(soup: BeautifulSoup) -> str:
    """Extract book image from html."""
    img = soup.select_one('div.bookimage img')
    return img['src']


def extract_book_genres(soup: BeautifulSoup) -> List[str]:
    """Extract book genres from html."""
    a_tags = soup.select('span.d_book a')
    return [a.text for a in a_tags]


def extract_book_comments(soup: BeautifulSoup) -> List[str]:
    """Extract book comments from html."""
    spans = soup.select('div.texts > span.black:first-of-type')
    return [span.text for span in spans]


def get_id_prefix():
    """Generate a random 8 symbols ID."""
    return str(uuid.uuid4())[:8]


def combine_path(filename: str, path: str, extension: str = None) -> str:
    """Combine path, filename and file extension with unique name."""
    valid_filename = sanitize_filename(filename)
    _id = get_id_prefix()
    if extension:
        return str(pathlib.PurePath(path, f'{valid_filename}_{_id}.{extension}'))

    dot_position = valid_filename.rfind('.')
    valid_filename = (
        f'{valid_filename[:dot_position]}'
        f'_{_id}.'
        f'{valid_filename[dot_position + 1:]}'
    )

    return str(pathlib.PurePath(path, valid_filename))


def make_request(url: str, verify_ssl: bool = False) -> Response:
    """Get request to url and return response, if if status ok."""
    response = requests.get(url, allow_redirects=False, verify=verify_ssl)
    response.raise_for_status()

    if response.is_redirect or response.is_permanent_redirect:
        raise RedirectReceivedError(response.status_code)

    return response


def download_file(url: str, filename: str, path: str, extension: str = None) -> str:
    """Download file with specified params"""
    response = make_request(url)

    file_path = combine_path(filename, path, extension)

    with open(file_path, 'wb') as file:
        file.write(response.content)

    return file_path


def download_book_page(page_url: str) -> dict:
    """Download html with book title, author, image, comments and genres."""
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
    """Create destination and json path dirs."""
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


def save_file(books: List[dict], json_path: str) -> None:
    """Save list of books info to json file."""
    with open(json_path, 'w') as export_file:
        json.dump(books, export_file, ensure_ascii=False, indent=4)


def download_books_list(book_ids: List[str], paths: dict, skip_txt_download: bool, skip_images_download: bool) -> List[dict]:
    """Iterate by books ids and download."""
    books = list()

    for book_id in book_ids:
        page_url = BOOK_URL.format(BASE_URL, book_id)
        file_url = BOOK_DOWNLOAD_URL.format(BASE_URL, book_id)

        try:
            print(f'\ntry lookup book: {page_url}')

            book = download_book_page(page_url)

            if not skip_txt_download:
                print(f'begin download: {file_url}')

                book_path = download_file(
                    file_url, book['title'], paths['books_path'], 'txt'
                )

                print(f'downloaded file to {book_path}')
                book['book_path'] = book_path

            if not skip_images_download:
                image_filename = book['image_url'].split('/')[-1]

                print(f'begin download: {book["image_url"]}')

                img_src = download_file(
                    book['image_url'], image_filename, paths['images_path']
                )

                print(f'downloaded file to {img_src}')
                book['img_src'] = img_src

            books.append(book)

        except (HTTPError, RedirectReceivedError) as e:
            print(e)

    return books
