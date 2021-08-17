from urllib.parse import urlparse

from .utils import download_by_requests
from .utils import download_by_ydl

class Attachment:
    def __init__(self, name: str, filetype: str, url: str, section_name: str, description: str="") -> None:
        self.section_name = section_name
        self.name = name
        self.url = urlparse(url).geturl()
        self.description = description
        self.filetype = filetype
        if self.filetype == "video":
            self._download = download_by_ydl
        elif self.filetype == "document":
            self._download = download_by_requests
        else:
            raise NotImplementedError(f"{self.filetype} filetype download not supported")

    def download(self, path_prefix: str) -> bool:
        import os
        path = os.path.join(path_prefix, self.name)
        print(f"Downloading '{path}'")
        return self._download(self.url, path)

    def __repr__(self) -> str:
        return "{name}".format(name=self.name)

    def __str__(self) -> str:
        return "{name}".format(name=self.name)
