from typing import List

from config import BOOK_DOWNLOAD_URL, BASE_URL, BOOK_URL


class BookUrl:
    page: str
    file: str

    def __init__(self, book_id: int) -> None:
        self.page = BOOK_URL.format(BASE_URL, book_id)
        self.file = BOOK_DOWNLOAD_URL.format(BASE_URL, book_id)


class BookInfo:
    author: str
    name: str
    book_url: BookUrl
    image_url: str
    comments: List[str]
    genres: List[str]

    def __init__(self, name: str, author: str, book_url: BookUrl,
                 image_url: str, comments: List[str], genres: List[str]) -> None:
        self.name = name
        self.author = author
        self.book_url = book_url
        self.image_url = image_url
        self.comments = comments
        self.genres = genres

    def make_image_name(self) -> str:
        return self.image_url.split('/')[-1]
