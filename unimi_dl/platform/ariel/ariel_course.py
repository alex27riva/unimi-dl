from bs4.element import Tag

from unimi_dl.platform.course import Course
from unimi_dl.platform.course import Section
from unimi_dl.platform.downloadable import Attachment

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
        if url.startswith("ThreadList.aspx"):
            url = base_url + utils.API + url
        super().__init__(name=name, url=url, base_url=base_url, parent_section=parent_section)
        self.has_retrieved = False #indicates if it already retrieved the available attachments
        
    def _parseToTree(self):
        """
        TODO: doesn't parse subsections
        """
        html = utils.getPageHtml(self.url)
        tables = utils.findAllContentTables(html)

        for table in tables:
            if isinstance(table, Tag):
                trs = utils.findAllRows(table)
                t = utils.findTableType(table)
                if t == "room": # get subsections
                    for tr in trs:
                        a_tags = utils.findAllATags(tr)
                        for a in a_tags:
                            href = a.get("href")
                            if isinstance(href, str):
                                self.addSection(name=a.get_text(), url=href)
                if t == "thread":
                    for tr in trs:
                        self.attachments = self.attachments + utils.findAllAttachments(tr, self.base_url)

    def getAttachments(self) -> list[Attachment]:
        if not self.has_retrieved:
            self._parseToTree()
            for child in self.subsections:
                self.attachments = self.attachments + child.getAttachments()
            self.has_retrieved = True
        return self.attachments.copy()

    def addSection(self, name: str, url: str):
        self.subsections.append(ArielSection(
            name=name, url=url, base_url=self.base_url, parent_section=self))
        return True

class ArielCourse(Course):
    def __init__(self, name: str, teachers: list[str], url: str, edition: str) -> None:
        super().__init__(name=name, teachers=teachers, url=url, edition=edition)
        self.sections = [] # type: list[Section]

    def getSections(self) -> list[Section]:
        if not self.sections:
            self.sections = utils.findAllSections(self.base_url)

        return self.sections
