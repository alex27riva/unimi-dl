import re

from typing import Tuple, Optional

from bs4 import BeautifulSoup
from bs4.element import NavigableString, Tag

from unimi_dl.platform.course import Section
import unimi_dl.platform.ariel.ariel_course as ariel_course

from ..session_manager.unimi import UnimiSessionManager
from ..downloadable import Attachment

API = "/v5/frm3/" #API version of ariel
OFFERTA_FORMATIVA = "https://ariel.unimi.it/Offerta/myof" #offerta formativa
CONTENUTI = "ThreadList.aspx?name=contenuti" #contents endpoint of a course

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

def findAllAttachments(tr: Tag, base_url: str) -> list[Attachment]:
    attachments = []
    attachments = attachments + findAllVideos(tr) + findAllDocuments(tr, base_url) 
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

def findAllDocuments(tr: Tag, base_url: str) -> list[Attachment]:
    attachments = []
    a_tags = tr.find_all("a", class_=["filename"])
    for a in a_tags:
        if not isinstance(a, Tag):
            continue

        name = findDocumentName(a)
        url = base_url + API + getTagHref(a)[8:] #excluding ../frm3 from the url
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

def getTagHref(tag: Tag) -> str:
    href = tag.get("href")

    if not isinstance(href, str):
        href = ""

    return href

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
            if isinstance(span, Tag):
                title = span.get_text()
    return title

def getPageHtml(url: str) -> str:
    session = UnimiSessionManager.getSession()
    r = session.get(url)
    r.raise_for_status()
    return r.text

def findAllCourses() -> list[Tuple[str, list[str], str, str]]:
    """
    Parses the html page corresponding to the accessible courses by the student
    and retrieves the courses
    """
    courses = []
    html = getPageHtml(OFFERTA_FORMATIVA)

    page = BeautifulSoup(html, 'html.parser')
    courses_table = page.find("table", class_="table")
    if isinstance(courses_table, Tag):
        projects = courses_table.find_all("div", class_="ariel-project")
        for project in projects:
            if isinstance(project, Tag):
                courses.append(createCourse(project))
    else: #TODO: custom Exception
        raise Exception("Error while parsing courses. Maybe Tag changed?")

    return courses

def createCourse(div: Tag) -> Tuple[str, list[str], str, str]:
    """
    Parses a `div` with `class` = ariel-project getting `teachers' name,
    course's name, course's base root url and edition`

    Returns a `name` of course, list of `teacher`, `url` of the course and `edition` of the course
    """
    if "ariel-project" not in div["class"]: #TODO: customize exception
        raise Exception("div class doesn't match 'ariel-project'. Maybe changed?")

    teachers = findAllTeachersName(div)
    name, url = findCourseNameAndUrl(div)
    edition = findCourseEdition(div)
    return name, teachers, url, edition

def findAllTeachersName(div: Tag) -> list[str]:
    regexp = re.compile("/offerta/teacher/*") #find teachers' name
    els = div.find_all("a", href=regexp)
    teachers = []
    for el in els:
        if isinstance(el, Tag):
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

def findAllSections(base_url: str) -> list[Section]:
    """
    Finds all the sections of a given course specified in `base_url`
    """
    sections = []
    url = base_url + API + CONTENUTI
    html =  getPageHtml(url)
    table = findContentTable(html)

    if table == None:
        return sections

    trs = findAllRows(table)

    for tr in trs:
        a = tr.find("a")
        if isinstance(a, Tag):
            href = getTagHref(a)

            if href == "":
                raise Exception("href shouldn't be empty")

            section_url = base_url + API + href
            name = a.get_text()

            sections.append(ariel_course.ArielSection(
                name=name,
                url=section_url,
                base_url=base_url))
    return sections
