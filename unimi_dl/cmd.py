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
from io import TextIOWrapper
from json import dumps as json_dumps
import logging
import os
from unimi_dl.utility.download_manager import DownloadManager
from unimi_dl.utility.credentials_manager import CredentialsManager
from unimi_dl import LOCAL
import platform as pt
import sys
from unimi_dl.platform.ariel import Ariel
from requests import __version__ as reqv
import youtube_dl
from youtube_dl.version import __version__ as ytdv
from unimi_dl.platform.course import Course, Section
from unimi_dl.platform.downloadable import Attachment
from . import CREDENTIALS, DOWNLOADED, LOG, __version__ as udlv
from .multi_select import WrongSelectionError, multi_select
from .platform import getPlatform

def get_args() -> Namespace:
    parser = ArgumentParser(
        description=f"Unimi material downloader v. {udlv}")
    if not set(["--cleanup-downloaded", "--wipe-credentials"]) & set(sys.argv):
        parser.add_argument("url", metavar="URL", type=str,
                            help="URL of the video(s) to download")
    parser.add_argument("-p", "--platform", metavar="platform",
                        type=str, default="ariel", choices=["ariel", "panopto"],
                        help="platform to download the video(s) from (default: ariel)")
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
                       help=f"retrieve video names and manifests, but don't download anything nor update the downloaded list")
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

def cleanup_downloaded(downloaded_path: str) -> None:
    main_logger = logging.getLogger(__name__)
    downloaded_dict, downloaded_file = get_downloaded(downloaded_path)

    if len(downloaded_dict) == 0:
        main_logger.warning("The downloaded list is empty!")
        return
    choices = list(downloaded_dict.keys())
    entt = list(downloaded_dict.values())
    main_logger.debug("Prompting user")
    try:
        chosen = multi_select(choices, entries_text=entt,
                              selection_text="\nVideos to remove from the downloaded list: ")
    except WrongSelectionError:
        main_logger.error("Your selection is not valid")
        exit(1)
    main_logger.debug(f"{len(chosen)} names chosen")
    if len(chosen) != 0:
        for manifest in chosen:
            downloaded_dict.pop(manifest)
        downloaded_file.seek(0)
        downloaded_file.write(json_dumps(downloaded_dict))
        downloaded_file.truncate()
    downloaded_file.close()
    main_logger.info("Cleanup done")

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

    opts.url = opts.url.replace("\\", "")
    main_logger.debug(f"""MODE: {"SIMULATE" if opts.simulate else "ADD TO DOWNLOADED ONLY" if opts.add_to_downloaded_only else "DOWNLOAD"}
    Request info:
    URL: {opts.url}
    Platform: {opts.platform}
    Save: {opts.save}
    Ask: {opts.ask}
    All: {opts.all}
    Credentials: {opts.credentials}
    Output: {opts.output}""")

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
        cleanup_downloaded(DOWNLOADED)
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

    platform = getPlatform(email, password, opts.platform)
    if isinstance(platform, Ariel):
        courses = platform.getCourses()
        selected_courses = multi_select(courses, courses, "Scegli il corso: ") # type: list[Course]

        for course in selected_courses:
            entries = course.getSections()
            selected_sections = multi_select(entries, entries, "Scegli le sezioni: ") # type: list[Section]

            attachments = []
            for section in selected_sections:
                attachments = section.getAttachments() + attachments 

            selected_attachments = multi_select(
                entries=attachments,
                entries_text=attachments,
                selection_text="Scegli i file che vuoi scaricare ") # type: list[Attachment]

            for attachment in selected_attachments:
                if not opts.simulate:
                    download_manager.doDownload(
                        attachment=attachment,
                        dry_run=opts.add_to_downloaded_only,
                        path=opts.output,
                        platform=opts.platform
                    )
    else:
        pass

    download_manager.save()

#    all_manifest_dict = getPlatform(
#        email, password, opts.platform).get_manifests(opts.url)
#
#    if len(all_manifest_dict) == 0:
#        main_logger.warning("No videos found")
#    else:
#        if opts.all or opts.platform == "panopto":
#            manifest_dict = all_manifest_dict
#        else:
#            try:
#                selection = multi_select(
#                    list(all_manifest_dict.keys()), selection_text="\nVideos to download: ")
#            except WrongSelectionError:
#                main_logger.error("Your selection is not valid")
#                exit(1)
#            manifest_dict = {
#                name: all_manifest_dict[name] for name in selection}

#        if len(manifest_dict) > 0:
#            main_logger.info(f"Videos: {list(manifest_dict.keys())}")
#
#            downloaded_dict, downloaded_file = get_downloaded()
#
#            download(opts.output, manifest_dict, downloaded_dict,
#                     downloaded_file, opts.simulate, opts.add_to_downloaded_only)
#            downloaded_file.close()
    main_logger.debug(
        f"=============job end at {datetime.now()}=============\n")
