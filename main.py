#!/usr/bin/env python
import os
import pathlib

import requests

from config import PATH_DOWNLOADS, BOOK_DOWNLOAD_URL, BASE_URL


def extract_filename(header):
    return header.split("filename=")[1].split('"')[1]


def combine_path(filename):
    return pathlib.PurePath(PATH_DOWNLOADS, filename)


def download_file(url):
    response = requests.get(url, allow_redirects=False)
    response.raise_for_status()

    if response.is_redirect or response.is_permanent_redirect:
        print(f'redirect found: code {response.status_code}, stop.\n', )
        return

    os.makedirs(PATH_DOWNLOADS, exist_ok=True)

    filename = extract_filename(response.headers.get("Content-Disposition"))
    path = combine_path(filename)

    with open(path, 'wb') as file:
        file.write(response.content)

    print('done\n')


def make_url(next_id):
    return BOOK_DOWNLOAD_URL.format(BASE_URL, next_id)


def main():
    for no in range(1, 11):
        url = make_url(no)
        print(f'try download book: {url}')
        download_file(url)


if __name__ == '__main__':
    main()
