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
from unimi_dl.platform.downloadable import Attachment
from unimi_dl.platform.course import Course

from .ariel import Ariel
from .panopto import Panopto
from .platform import Platform


class Platform:
    def __init__(self, email: str, password: str) -> None:
        self.email = email
        self.password = password

    def getCourses(self) -> list[Course]:
        """
        Returns a list of available Courses on the `Platform`
        """
        raise NotImplementedError

    def getAttachments(self, url: str) -> list[Attachment]:
        """
        Returns a list of `Attachment` available for download from `url`.
        Replaces the deprecated `get_manifests`
        """
        raise NotImplementedError

    def get_manifests(self, url: str) -> dict[str, str]:
        """ Returns a list of couples, each one containing a filename and relative
        manifest, fetched from {url} """
        raise NotImplementedError

    @staticmethod
    def getPlatform(email: str, password: str, platform: str) -> Platform:
        """ Factory method to create the appropriate Platform instance. """

        if platform == 'ariel':
            return Ariel(email, password)
        if platform == 'panopto':
            return Panopto(email, password)
        raise NotImplementedError
