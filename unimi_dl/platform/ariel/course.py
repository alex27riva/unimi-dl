from unimi_dl.platform.ariel.utils import findAllSections
from unimi_dl.platform.downloadable import Attachment
from .utils import Section 

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

    def getSections(self) -> dict[str, Section]:
        if not self.sections:
            self.sections = findAllSections(self.base_url)

        return self.sections

    def getSectionAttachments(self, section_name: str) -> list[Attachment]:
        """Retrieves all the attachments of a section"""

        attachments = []
        section = self.sections.get(section_name)
        if section is not None:
            attachments = attachments + section.getAttachments()
        return attachments

    def __str__(self) -> str:
        return "Corso di '{name}' di '{teachers}' edizione '{edition}'".format(
            name=self.name, teachers=self.teachers, edition=self.edition)
