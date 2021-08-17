# Copyright (C) 2021 Alessandro Clerici Lorenzini and Zhifan Chen.
#
# This file is part of unimi-dl.
#
# unimi-dl is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# unimi-dl is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with unimi-dl.  If not, see <https://www.gnu.org/licenses/>.


from __future__ import annotations, with_statement
import logging
import re
import urllib.parse

from typing import Union, Tuple, Optional
from bs4 import BeautifulSoup
from bs4.element import NavigableString, Tag
import requests
from urllib.parse import urlparse

from .platform import Platform

API = "/v5/frm3/"

def get_ariel_session(email: str, password: str) -> requests.Session:
    s = requests.Session()
    login_url = 'https://elearning.unimi.it/authentication/skin/portaleariel/login.aspx?url=https://ariel.unimi.it/'
    payload = {
        'hdnSilent': 'true',
        'tbLogin': email,
        'tbPassword': password
    }
    s.post(login_url, data=payload)
    return s

class ArielSessionManager:
    """Manages Ariel's login session as singleton"""

    session = None # type: Union[None, requests.Session]
            
    @staticmethod
    def getSession(email: str = "", password: str = ""):
        """
        Returns the session.
        The first time it needs `email` and `password`, subsequent calls won't need them.
        Raises `requests.HTTPError` if at the first call `email` or `password` are wrong.
        """
        
        if ArielSessionManager.session == None:
            ArielSessionManager.session = requests.Session()
            login_url = 'https://elearning.unimi.it/authentication/skin/portaleariel/login.aspx?url=https://ariel.unimi.it/'
            payload = {
                'hdnSilent': 'true',
                'tbLogin': email,
                'tbPassword': password
            }
            response = ArielSessionManager.session.post(url=login_url, data=payload)
            response.raise_for_status()
        return ArielSessionManager.session

class Ariel(Platform):
    def __init__(self, email: str, password: str) -> None:
        super().__init__(email, password)
        self.session = ArielSessionManager.getSession(email=email, password=password)

        self.courses = [] # type: list[Course]
        self.logger = logging.getLogger(__name__)
        self.logger.info("Logging in")

    def get_courses(self) -> list[Course]:
        """Returns a list of `Course` of the accessible courses"""
        if not self.courses:
            myof_endpoint = "https://ariel.unimi.it/Offerta/myof" #endpoint per la propria offerta formativa
            r = self.session.get(myof_endpoint)

            self.courses = self._parse_courses(r.text)

        return self.courses.copy()
    
    def _parse_courses(self, html: str) -> list[Course]:
        """
        Parses the html page corresponding to the accessible courses by the student
        and retrieves the courses
        """
        courses = []

        page = BeautifulSoup(html, 'html.parser')
        courses_table = page.find("table", class_="table")
        if isinstance(courses_table, Tag):
            projects = courses_table.find_all("div", class_="ariel-project")
            for project in projects:
                if isinstance(project, Tag):
                    courses.append(self._createCourse(project))
        else: #TODO: custom Exception
            raise Exception("Error while parsing courses. Maybe Tag changed?")

        return courses

    def _createCourse(self, div: Tag) -> Course:
        """
        Parses a `div` with `class` = ariel-project getting `teachers' name,
        course's name, course's base root url and edition`
        """
        if "ariel-project" not in div["class"]: #TODO: customize exception
            raise Exception("div class doesn't match 'ariel-project'. Maybe changed?")

        def findAllTeachersName(div: Tag) -> list[str]:
            regexp = re.compile("/offerta/teacher/*") #find teachers' name
            els = div.find_all("a", href=regexp)
            teachers = []
            for el in els:
                teachers.append(el.get_text())
            return teachers

        def findCourseNameAndUrl(div: Tag) -> Tuple[str, str]:
            regexp = re.compile("https://*") #find course's name and url
            el = div.find("a", href=regexp)
            if isinstance(el, Tag):
                name = el.get_text()
                href = el["href"]
                if isinstance(href, list):
                    raise Exception("href shouldn't be a list")
                return name, href
            else:
                raise Exception("Error on finding course's name and url") #TODO: customize exception

        def findCourseEdition(div: Tag):
            regexp = re.compile("tag bg-F") #find course's edition
            el = div.find("span", class_=regexp)
            edition = ""

            if isinstance(el, Tag):
                if isinstance(el.parent, Tag):
                    edition = el.parent.get_text()

            return edition

        teachers = findAllTeachersName(div)
        name, url = findCourseNameAndUrl(div)
        edition = findCourseEdition(div)
        
        return Course(name, teachers, url, edition)

    def get_manifests(self, url: str) -> dict[str, str]:
        self.logger.info("Getting video page")
        video_page = self.session.get(url).text

        self.logger.info("Collecting manifests and video names")
        res = {}
        manifest_re = re.compile(
            r"https://.*?/mp4:.*?([^/]*?)\.mp4/manifest.m3u8")
        for i, manifest in enumerate(manifest_re.finditer(video_page)):
            title = urllib.parse.unquote(
                manifest[1]) if manifest[1] else urllib.parse.urlparse(url)[1]+str(i)
            while title in res:
                title += "_other"
            res[title] = manifest[0]
        return res

class Attachment:
    def __init__(self, name: str, filetype: str, url: str, section_name: str, description: str="") -> None:
        self.section_name = section_name
        self.name = name
        self.url = urlparse(url).geturl()
        self.description = description
        self.filetype = filetype

    def download(self, path: str) -> bool:
        success = False

        if self.filetype == "video":
            print("Scaricando")
            import youtube_dl
            
            ydl_opts = {
                "v": "true",
                "nocheckcertificate": "true",
                "restrictfilenames": "true",
                "logger": logging.getLogger("youtube-dl")
            }
            ydl_opts["outtmpl"] = path + self.name + ".%(ext)s"
            with youtube_dl.YoutubeDL(ydl_opts) as ydl:
                ydl.download([self.url])
        return success

    def __repr__(self) -> str:
        return "{name}".format(name=self.name)

    def __str__(self) -> str:
        return "{name}".format(name=self.name)

class ArielNode:
    """
    It's an implementation of a tree

    `self.root` is the root node of ArielNode
    `self.parent` is the parent node of ArielNode: if it's root then is None
    `self.name` is an identifier for the node
    `self.url` is the url associated to the node
    `self.base_url` is the base url of the node (the part till .it)
    `self.attachments` is a list of the attachments of the node. At the first call of getAttachments ArielNode will try to retrieve all the attachments of the ArielNode and the children
    `self.children` is a dictionary with the name and the ArielNode associated with it
    """
    def __init__(self, name: str, url: str, base_url: str, parent:ArielNode=None) -> None:
        if parent == None:
            self.root = self
            self.parent = None
        else:
            self.root = parent.root
            self.parent = parent

        self.name = name
        self.url = urlparse(url).geturl()
        self.base_url = urlparse(base_url).geturl()
        self.attachments = [] # type: list[Attachment]
        self.children = {} # type: dict[str, ArielNode]

        self.has_retrieved = False #indicates if it already retrieved the available attachments
        
    def _parseToTree(self):

        html = getPageHtml(self.url)
        table = findContentTable(html)
        
        trs = []
        if isinstance(table, Tag):
            trs = findAllRows(table)

        for tr in trs:
            self.attachments = findAllAttachments(tr) + self.attachments

    def getAttachments(self) -> list[Attachment]:
        if not self.has_retrieved:
            self._parseToTree()
            for child in self.children.values():
                self.attachments = child.getAttachments() + self.attachments

        return self.attachments.copy()

    def addChild(self, name: str, url: str):
        self.children[name] = (ArielNode(
            name=name, url=url, base_url=self.base_url, parent=self))
        return True

class Course:
    """Represents a teaching course. It's characterized by:
    `name`: the name of the course
    `teachers`: a list of teachers involved in the teaching of the course
    `link`: a link to the course's homepage
    `edition`: it's the edition of the course
    `section`: a dictionary containing the name of the section i.e. "Materiali didattici" or "Videoregistrazioni"
        and a tree-like representation of the course making it more easily browseable or retrieve files

    It allows you to retrieve all the attachments of the said course (be it a video or pdfs)"""

    def __init__(self, name: str, teachers: list[str], base_url: str, edition: str) -> None:
        self._name = name
        self._teachers = teachers
        self._base_url = base_url
        self._edition = edition
        self._sections = {} # type: dict[str, ArielNode]
        self._session = ArielSessionManager.getSession()

    @property
    def name(self):
        return self._name

    @property
    def teachers(self):
        return self._teachers
        
    @property
    def base_url(self):
        return self._base_url

    @property
    def edition(self):
        return self.edition

    @property
    def sections(self) -> dict[str, ArielNode]:
        if not self._sections:
            endpoint = "ThreadList.aspx?name=contenuti"
            url = self.base_url + API + endpoint
            html = getPageHtml(url)
            table = findContentTable(html)

            if table == None:
                self._sections = {}
                return self._sections

            trs = findAllRows(table)

            for tr in trs:
                a = tr.find("a")
                if isinstance(a, Tag):
                    href = a.get("href")

                    if isinstance(href, list):
                        raise Exception("href shouldn't be list")
                    if href is None:
                        raise Exception("href shouldn't be None")
                    new_url = self.base_url + API + href
                    name = a.get_text()

                    self._sections[name] = ArielNode(
                        name=name,
                        url=new_url,
                        base_url=self.base_url
                    )

        return self._sections.copy()

    @property
    def session(self):
        return self._session

    def getAvailableSections(self) -> list[str]:
        """
        Returns a list of the sections in the course's content page
        """
        return list(self.sections.keys())

    def getSectionAttachments(self, section: str) -> list[Attachment]:
        """Retrieves all the attachments of a section"""

        attachments = []
        ariel_node = self.sections.get(section)
        if ariel_node is not None:
            section_tree = self.sections.get(section)
            if section_tree is not None:
                print(section_tree.getAttachments())
                attachments = attachments + section_tree.getAttachments()
        return attachments

    def __str__(self) -> str:
        return "Corso di '{name}' di '{teachers}' edizione '{edition}'".format(
            name=self.name, teachers=self.teachers, edition=self.edition)

def findContentTable(html: str) -> Optional[Tag]:
    page = BeautifulSoup(html, "html.parser")
    tag = page.find("tbody")
    if isinstance(tag, NavigableString):
        return None

    return tag

def findAllRows(tbody: Tag) -> list[Tag]:
    result = []
    trs = tbody.find_all("tr")
    for tr in trs:
        if isinstance(tr, Tag):
            result.append(tr)
    return result

def findAllAttachments(tr: Tag) -> list[Attachment]:
    attachments = []
    attachments = attachments + findAllVideos(tr) + findAllDocuments(tr) 
    return attachments

def findAllVideos(tr: Tag) -> list[Attachment]:
    """
    Retrieves all the <video> in the `tr` abd creates an `Attachment` using:
        `name`: extracts the name from the `url`, which is the `manifest.m3u8`
        `url`: a http-valid url ending with `manifest.m3u8`
        `description`: the description of the post in which the video is located
        `filetype`: "video"
    """
    attachments = []
    videos = tr.find_all("video")
    for video in videos:
        url = ""
        if isinstance(video, Tag):
            url = findVideoUrl(video)
        name = (url.split(":")[2])[0:-14] #extracts the video name from the `manifest.m3u8`
        section_name = ""
        description = findPostDescription(tr)
        attachments.append(Attachment(
            name=name,
            url=url,
            section_name=section_name,
            description=description,
            filetype="video"
        ))

    return attachments

def findVideoUrl(video: Tag) -> str:
    url = ""
    source = video.find("source")
    if source is None or isinstance(source, NavigableString):
        return url
    url = source.get("src") 
    if isinstance(url, list):
        raise Exception("Video url shouldn't be a list")

    if url is None:
        url = ""

    return url

def findAllDocuments(tr: Tag) -> list[Attachment]:
    attachments = []
    a_tags = tr.find_all("a", class_=["filename"])
    for a in a_tags:
        if not isinstance(a, Tag):
            continue

        name = findDocumentName(a)
        url = findDocumentUrl(a)
        section_name = ""
        description = findPostDescription(tr)
        attachments.append(Attachment(
            name=name,
            url=url,
            section_name=section_name,
            description=description,
            filetype="document"
        ))

    return attachments

def findDocumentName(a: Tag) -> str:
    name = a.get_text()

    return name

def findDocumentUrl(a: Tag) -> str:
    url = ""
    href = a.get("href")
    if isinstance(href, str):
        url = href

    return url

def findPostDescription(tr: Tag) -> str:
    description = ""
    div = tr.find("div", class_="arielMessageBody")

    if isinstance(div, Tag):
        description = div.get_text()

    return description

def findMessageTitle(tr: Tag) -> str:
    title = ""
    h2 = tr.find("h2", class_=["arielTitle", "arielStick"])
    if isinstance(h2, Tag):
        spans = h2.select("span")
        for span in spans: #title should be the last `span` tag
            title = span.get_text()
    return title

def getPageHtml(url: str) -> str:
    session = ArielSessionManager.getSession()
    r = session.get(url)
    r.raise_for_status()
    return r.text
