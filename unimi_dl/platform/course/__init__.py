from __future__ import annotations

from urllib.parse import urlparse
from typing import Optional
from unimi_dl.platform.downloadable import Attachment

class Section:

    def __init__(self, name: str, url: str, base_url: str, parent_section = None) -> None:
        self.parent_section = parent_section # type: Optional[Section]
        self.name = name
        self.url = urlparse(url).geturl()
        self.base_url = urlparse(base_url).geturl()
        self.attachments = [] # type: list[Attachment]
        self.subsections = [] # type: list[Section]

    def getAllAttachments(self) -> list[Attachment]:
        """
        Get all attachments from `self` and `self.subsections`
        """
        raise NotImplementedError

    def getAttachments(self) -> list[Attachment]:
        raise NotImplementedError

    def getSubsections(self) -> list[Section]:
        raise NotImplementedError

    def __repr__(self) -> str:
        return self.__str__()

    def __str__(self) -> str:
        return self.name

class Course:
    """Represents a teaching course. It's characterized by:
    `name`: the name of the course
    `teachers`: a list of teachers involved in the teaching of the course
    `url`: a link to the course's homepage
    `edition`: it's the edition of the course
    `section`: a dictionary containing the name of the section i.e. "Materiali didattici" or "Videoregistrazioni"
        and a tree-like representation of the course making it more easily browseable or retrieve files

    It allows you to retrieve all the attachments of the said course (be it a video or pdfs)"""

    def __init__(self, name: str, teachers: list[str], url: str, edition: str) -> None:
        self.name = name
        self.teachers = teachers
        self.base_url = url
        self.edition = edition
        self.sections = {}

    def getSections(self) -> list[Section]:
        """
        Retrieves all the `Section` of the `Course`
        """
        raise NotImplementedError

    def __repr__(self) -> str:
        return f"""Corso di '{self.name}'"""

    def __str__(self) -> str:
        return \
        f"""Corso di '{self.name}' di 
        {self.teachers}
        edizione '{self.edition}'"""

