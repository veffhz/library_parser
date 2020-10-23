from config import BOOK_DOWNLOAD_URL, BASE_URL, BOOK_URL


class BookUrl:
    book_id: int
    page: str
    file: str

    def __init__(self, book_id: int) -> None:
        self.book_id = book_id
        self.page = BOOK_URL.format(BASE_URL, book_id)
        self.file = BOOK_DOWNLOAD_URL.format(BASE_URL, book_id)


class BookInfo:
    author: str
    name: str
    book_url: BookUrl

    def __init__(self, name: str, author: str, book_url: BookUrl) -> None:
        self.name = name
        self.author = author
        self.book_url = book_url

    def make_book_name(self):
        return f'{self.book_url.book_id}. {self.name}'
