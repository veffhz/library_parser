class RedirectReceivedError(Exception):
    """
    Http redirect exception
    """
    def __init__(self, code):
        self.message = f'redirect found: code {code}.'

    def __str__(self):
        return self.message
