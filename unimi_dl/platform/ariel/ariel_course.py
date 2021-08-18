from bs4.element import Tag

from unimi_dl.platform.downloadable import Attachment
from unimi_dl.platform.course import Course
from unimi_dl.platform.course import Section
import unimi_dl.platform.ariel.utils as utils

class ArielSection(Section):
    """
    It's an implementation of a tree

    `self.root` is the root node of Section
    `self.parent` is the parent node of Section: if it's root then is None
    `self.name` is an identifier for the node
    `self.url` is the url associated to the node
    `self.base_url` is the base url of the node (the part till .it)
    `self.attachments` is a list of the attachments of the node. At the first call of getAttachments Section will try to retrieve all the attachments of the ArielNode and the children
    `self.subsections` is a dictionary with the name and the Section associated with it
    """
    def __init__(self, name: str, url: str, base_url: str, parent_section = None) -> None:
        super().__init__(name=name, url=url, base_url=base_url, parent_section=parent_section)

        self.has_retrieved = False #indicates if it already retrieved the available attachments
        
    def _parseToTree(self):
        """
        TODO: doesn't parse subsections
        """
        html = utils.getPageHtml(self.url)
        table = utils.findContentTable(html)
        
        trs = []
        if isinstance(table, Tag):
            trs = utils.findAllRows(table)

        for tr in trs:
            self.attachments = utils.findAllAttachments(tr, self.base_url) + self.attachments

    def getAttachments(self) -> list[Attachment]:
        if not self.has_retrieved:
            self._parseToTree()
            for child in self.subsections:
                self.attachments = child.getAttachments() + self.attachments

            self.has_retrieved = True

        return self.attachments.copy()

    def addChild(self, name: str, url: str):
        self.subsections.append(Section(
            name=name, url=url, base_url=self.base_url, parent_section=self))
        return True

class ArielCourse(Course):
    def __init__(self, name: str, teachers: list[str], url: str, edition: str) -> None:
        super().__init__(name=name, teachers=teachers, url=url, edition=edition)
        self.sections = [] # type: list[Section]

    def getSections(self) -> list[Section]:
        if not self.sections:
            self.sections = findAllSections(self.base_url)

        return self.sections

def findAllSections(base_url: str) -> list[Section]:
    """
    Finds all the sections of a given course specified in `base_url`
    """
    sections = []
    url = base_url + utils.API + utils.CONTENUTI
    html =  utils.getPageHtml(url)
    table = utils.findContentTable(html)

    if table == None:
        return sections

    trs = utils.findAllRows(table)

    for tr in trs:
        a = tr.find("a")
        if isinstance(a, Tag):
            href = utils.getTagHref(a)

            if href == "":
                raise Exception("href shouldn't be empty")

            section_url = base_url + utils.API + href
            name = a.get_text()

            sections.append(ArielSection(
                name=name,
                url=section_url,
                base_url=base_url))
    return sections
