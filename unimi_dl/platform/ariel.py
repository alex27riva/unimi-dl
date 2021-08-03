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


from __future__ import annotations
import logging
import re
import urllib.parse

from bs4 import BeautifulSoup
import requests

from .platform import Platform


def get_ariel_session(email: str, password: str) -> requests.Session:
    s = requests.Session()
    login_url = 'https://elearning.unimi.it/authentication/skin/portaleariel/login.aspx?url=https://ariel.unimi.it/'
    s.post(login_url, data=payload)
    return s

class Ariel(Platform):
    def __init__(self, email: str, password: str) -> None:
        super().__init__(email, password)
        login_url = 'https://elearning.unimi.it/authentication/skin/portaleariel/login.aspx?url=https://ariel.unimi.it/'
        self.session = requests.Session()
        payload = {
            'hdnSilent': 'true',
            'tbLogin': email,
            'tbPassword': password
        }
        response = self.session.post(url=login_url, data=payload)

        self.logger = logging.getLogger(__name__)
        self.logger.info("Logging in")

    def get_courses(self) -> list[Course]:
        myof = "https://ariel.unimi.it/Offerta/myof" #url per la propria offerta formativa
        response = self.session.get(myof)

        page = BeautifulSoup(response.text, 'html.parser')

        courses_table = page.find("table", class_="table")
        projects = courses_table.find_all("div", class_="ariel-project")
        courses = []
        for project in projects:
            courses.append(self._createCourse(project))

        for course in courses:
            print(course)

        return courses

    def _createCourse(self, project) -> Course:
        regexp = re.compile("/offerta/teacher/*") #find teacher's name
        els = project.find_all("a", href=regexp)
        teachers = []
        for el in els:
            teachers.append(el.get_text())

        regexp = re.compile("https://*") #find course's name and link
        el = project.find("a", href=regexp)
        name = el.get_text()
        link = el["href"]

        
        regexp = re.compile("tag bg-F") #find course's edition
        el = project.find("span", class_=regexp)
        print(name)
        print(el.prettify())
        edition = el.parent.get_text()
        
        return Course(name, teachers, link, edition)

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

class Course:
    def __init__(self, name: str, teachers: list[str], link: str, edition: str) -> None:
        self.name = name
        self.teachers = teachers
        self.link = link
        self.edition = edition

    def __str__(self) -> str:
        return "Corso di '{name}' di '{teachers}' edizione '{edition}'".format(
            name=self.name, teachers=self.teachers, edition=self.edition)
