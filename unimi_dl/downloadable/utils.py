import logging
from unimi_dl.platform.session_manager.unimi import UnimiSessionManager

def download_by_ydl(url: str, path: str) -> bool:
    import youtube_dl

    ydl_opts = {
        "v": "true",
        "nocheckcertificate": "true",
        "restrictfilenames": "true",
        "logger": logging.getLogger("youtube-dl")
    }
    ydl_opts["outtmpl"] = path + ".%(ext)s"
    with youtube_dl.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])

    return True

def download_by_requests(url: str, path: str) -> bool:

    session = UnimiSessionManager.getSession()
    r = session.get(url)

    with(open(path, "wb") as file):
        file.write(r.content)

    return True
