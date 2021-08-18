import logging

from pathlib import Path

from unimi_dl.platform.downloadable import Attachment

from json import dumps as json_dumps, load as json_load
from json.decoder import JSONDecodeError


class Downloads:
    def __init__(self, ariel: list[str] = [],
        panopto: list[str] = [],
        msstream: list[str]= []) -> None:
        self.ariel = ariel
        self.panopto = panopto
        self.msstream = msstream

class DownloadManager:
    """
    Manages the `downloaded.json`.
    If the `download.json` specified in `downloaded_path` doesn't exists, it will be created when `save()` will be called
    """
    def __init__(self, downloaded_path: str) -> None:
        self.path = Path(downloaded_path).expanduser()
        try:
            with(self.path.open("r") as downloaded_file):
                try:
                    downloaded_json = json_load(downloaded_file)
                    self.downloads = Downloads(downloaded_json["ariel"], downloaded_json["panopto"], downloaded_json["msstream"])
                except JSONDecodeError:
                    logging.warning(f"Not valid JSON. Ignoring...")
                    self.downloads = Downloads()
        except FileNotFoundError:
            logging.warning(f"{self.path} not found. It will be created")
            self.downloads = Downloads()

    def doDownload(self, platform: str, attachment: Attachment, path: str) -> None:
        """
        Downloads the `attachment` in the given `path` and saves it under `platform`
        TODO: to change, need a better way to handle type hinting
        """
        l = getattr(self.downloads, platform) # list[str]
        if attachment.download(path):
            l.append(attachment.url)
            setattr(self.downloads, platform, l)

    def save(self) -> None:
        """
        Writes the changes to the `self.path`
        """
        with(self.path.open("w") as downloaded_file):
            downloaded_file.write(json_dumps(self.downloads.__dict__))

    def getDownloads(self) -> Downloads:
        return self.downloads
