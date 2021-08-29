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


from argparse import ArgumentParser, Namespace
from datetime import datetime
from getpass import getpass
from json import dumps as json_dumps
import logging
import os
from typing import List
from unimi_dl.utility.download_manager import DownloadManager
from unimi_dl.utility.credentials_manager import CredentialsManager
from unimi_dl import LOCAL, CREDENTIALS, DOWNLOADED, LOG, AVAILABLE_PLATFORMS
import platform as pt
import sys
from unimi_dl.platform.ariel import Ariel
from requests import __version__ as reqv
from youtube_dl.version import __version__ as ytdv
from unimi_dl.platform.course import Course, Section
from unimi_dl.platform.downloadable import Attachment
from . import  __version__ as udlv
from .multi_select import WrongSelectionError, multi_select
from .platform import getPlatform

def get_args() -> Namespace:
    parser = ArgumentParser(
        description=f"Unimi material downloader v. {udlv}")
    parser.add_argument("-u", "--url", metavar="url", type=str,
                        help="URL of the video(s) to download")
    parser.add_argument("-p", "--platform", metavar="platform",
                        type=str, default="all", choices=AVAILABLE_PLATFORMS,
                        help="platform to download the video(s) from (default: all)")
    parser.add_argument("-s", "--save", action="store_true",
                        help=f"saves credentials (unencrypted) in {CREDENTIALS}")
    parser.add_argument("--ask", action="store_true",
                        help=f"asks credentials even if stored")
    parser.add_argument("-c", "--credentials", metavar="PATH",
                        type=str, default=CREDENTIALS,
                        help="path of the credentials json to be used for logging into the platform")
    parser.add_argument("-o", "--output", metavar="PATH",
                        type=str, default=os.getcwd(), help="directory to download the video(s) into")
    parser.add_argument("-v", "--verbose", action="store_true")
    parser.add_argument("-a", "--all", action="store_true",
                        help="download all videos not already present")
    parser.add_argument('--version', action='version',
                        version=f"%(prog)s {udlv}")
    modes = parser.add_argument_group("other modes")
    modes.add_argument("--simulate", action="store_true",
                       help="retrieve video names and manifests, but don't download anything nor update the downloaded list")
    modes.add_argument("--add-to-downloaded-only",
                       action="store_true",help="retrieve video names and manifests and only update the downloaded list (no download)")
    modes.add_argument("--cleanup-downloaded", action="store_true",
                       help="interactively select what videos to clean from the downloaded list")
    modes.add_argument("--wipe-credentials",
                       action="store_true", help="delete stored credentials")

    opts = parser.parse_args()
    return opts


def log_setup(verbose: bool) -> None:
    # silencing spammy logger
    logging.getLogger("urllib3").setLevel(logging.WARNING)

    # setting up stdout handler
    stdout_handler = logging.StreamHandler(sys.stdout)
    if verbose:
        stdout_handler.setLevel(logging.INFO)
        stdout_handler.setFormatter(
            logging.Formatter("%(message)s"))
    else:
        stdout_handler.setLevel(logging.WARNING)
        stdout_handler.setFormatter(
            logging.Formatter("%(levelname)s: %(message)s"))

    # setting up file handler
    file_handler = logging.FileHandler(LOG)
    file_handler.setFormatter(logging.Formatter(
        "%(levelname)s[%(name)s]: %(message)s"))

    # finalizing
    logging.basicConfig(level=logging.DEBUG, handlers=[
                        file_handler, stdout_handler])

def main():
    opts = get_args()
    if not os.path.isdir(LOCAL):
        os.makedirs(LOCAL)
    log_setup(opts.verbose)
    main_logger = logging.getLogger(__name__)

    main_logger.debug(
        f"=============job start at {datetime.now()}=============")
    main_logger.debug(f"""Detected system info:
    unimi-dl: {udlv}
    OS: {pt.platform()}
    Release: {pt.release()}
    Version: {pt.version()}
    Local: {LOCAL}
    Python: {sys.version}
    Requests: {reqv}
    YoutubeDL: {ytdv}
    Downloaded file: {DOWNLOADED}""")

    main_logger.debug(f"""MODE: {"SIMULATE" if opts.simulate else "ADD TO DOWNLOADED ONLY" if opts.add_to_downloaded_only else "DOWNLOAD"}
    Request info:
    Platform: {opts.platform}
    Save: {opts.save}
    Ask: {opts.ask}
    All: {opts.all}
    Credentials: {opts.credentials}
    Output: {opts.output}""")

    if opts.url is not None:
        opts.url = opts.url.replace("\\", "") #sanitize url

    platforms = opts.platform
    if platforms == "all":
        platforms = AVAILABLE_PLATFORMS

    if not isinstance(platforms, List):
        platforms = [platforms]

    # get credentials
    credentials_manager = CredentialsManager(opts.credentials)
    credentials = credentials_manager.getCredentials()
    email = credentials.email
    password = credentials.password
    if opts.ask or email is None or password is None:
        main_logger.info(f"Asking credentials")
        print(f"Insert credentials")
        email = input(f"username/email: ")
        password = getpass(f"password (input won't be shown): ")
        if opts.save:
            credentials_manager.setCredentials(email, password)

    download_manager = DownloadManager(DOWNLOADED)

    if opts.cleanup_downloaded:
        main_logger.debug("MODE: DOWNLOADED CLEANUP")
        for platform in platforms:
            downloaded = download_manager.getDownloadFrom(platform)
            to_delete = multi_select(downloaded, entries_text=downloaded,
                                  selection_text=f"\nVideos to remove from the '{platform}' downloaded list: ")
            download_manager.wipeDownloaded(platform, to_delete)
        main_logger.debug(
            f"=============job end at {datetime.now()}=============\n")
        exit(0)
    elif opts.wipe_credentials:
        main_logger.debug("MODE: WIPE CREDENTIALS")
        main_logger.debug("Prompting user")
        choice = input(
            "Are you sure you want to delete stored credentials? [y/N]: ").lower()
        if choice == "y" or choice == "yes":
            credentials_manager.wipeCredentials()
            main_logger.info("Credentials file deleted")
        else:
            main_logger.info("Credentials file kept")

        main_logger.debug(
            f"=============job end at {datetime.now()}=============\n")
        exit(0)

    for platform in platforms:
        p = getPlatform(email, password, opts.platform)
        if isinstance(p, Ariel):
            courses = p.getCourses()
            selected_courses = multi_select(courses, courses, "Scegli il corso: ") # type: list[Course]

            for course in selected_courses:
                entries = course.getSections()
                selected_sections = multi_select(entries, entries, "Scegli le sezioni: ") # type: list[Section]
                for section in selected_sections:
                    show(opts.simulate, opts.add_to_downloaded_only,
                        platform, opts.output, download_manager, section)
        elif platform == "panopto" and opts.url is not None:
            attachments = p.getAttachments(opts.url)
            show(opts.simulate, opts.add_to_downloaded_only,
                platform, opts.output, download_manager,
                additional_attachments=attachments)

        else:
            print("not supported platform")
            exit(1)

    download_manager.save()

    main_logger.debug(
        f"=============job end at {datetime.now()}=============\n")

def show(simulate: bool, add_to_downloaded_only: bool,
    platform: str, output: str, download_manager: DownloadManager,
    section: Section = None, additional_attachments: list[Attachment] = []):
    sections = []
    if section is not None:
        sections = section.getSubsections()
    choices = sections + section.getAttachments() + additional_attachments # type: ignore
    selected_choices = multi_select(
        entries=choices,
        entries_text=choices,
        selection_text="Scegli un file o una sezione ")

    for choice in selected_choices:
        if isinstance(choice, Section):
            show(simulate, add_to_downloaded_only, platform, output,
                download_manager, choice)

        if isinstance(choice, Attachment):
            if not simulate:
                download_manager.doDownload(
                    attachment=choice,
                    dry_run=add_to_downloaded_only,
                    path=output,
                    platform=platform
)
