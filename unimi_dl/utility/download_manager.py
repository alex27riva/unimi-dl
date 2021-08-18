import logging

from pathlib import Path
from typing import Optional

from unimi_dl.platform.downloadable import Attachment

from json import dumps as json_dumps, load as json_load
from json.decoder import JSONDecodeError

logger = logging.getLogger(__name__)

class Downloads:
    def __init__(self, ariel: Optional[list[str]] = [],
        panopto: Optional[list[str]] = [],
        msstream: Optional[list[str]] = []) -> None:

        if ariel is None:
            ariel = []

        if panopto is None:
            panopto = []

        if msstream is None:
            msstream = []

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
                    downloaded_json = json_load(downloaded_file) # type: dict[str, list[str]]
                    ariel = downloaded_json.get("ariel") # avoid KeyError
                    panopto = downloaded_json.get("panopto")
                    msstream = downloaded_json.get("msstream")
                    self.downloaded = Downloads(ariel, panopto, msstream)
                except JSONDecodeError:
                    logging.warning(f"Not valid JSON . Ignoring...")
                    self.downloaded = Downloads()
        except FileNotFoundError:
            logging.warning(f"{self.path} not found. It will be created")
            self.downloaded = Downloads()

    def doDownload(self, platform: str, attachment: Attachment, path: str, dry_run:bool = False, force:bool = False) -> None:
        """
        Downloads the `attachment` in the given `path` and saves it under `platform`.
        If `dry_run` is True then the `attachment` is only added to the downloaded list but not effectively downloaded
        TODO: to change, need a better way to handle type hinting
        """
        l = getattr(self.downloaded, platform) # list[str]
        if attachment.url not in l or force:
            if dry_run or attachment.download(path):
                l.append(attachment.url)
                setattr(self.downloaded, platform, l)
        else:
            logger.warning(f"{attachment} already downloaded")


    def save(self) -> None:
        """
        Writes the changes to the `self.path`
        """
        with(self.path.open("w") as downloaded_file):
            downloaded_file.write(json_dumps(self.downloaded.__dict__))

    def wipeDownloaded(self) -> None:
        new_downloaded = Downloads()
        with(self.path.open("w") as downloaded_file):
            downloaded_file.write(json_dumps(new_downloaded.__dict__))
        self.downloaded = new_downloaded

    def getDownloads(self) -> Downloads:
        return self.downloaded
