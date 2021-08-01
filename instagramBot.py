from argparse import ArgumentParser
from glob import glob
from os.path import expanduser
from platform import system
from sqlite3 import OperationalError, connect

from instaloader import Instaloader, Profile
from itertools import islice
from math import ceil

X_percentage = 10 

try:
    from instaloader import ConnectionException, Instaloader
except ModuleNotFoundError:
    raise SystemExit("Instaloader not found.\n  pip install [--user] instaloader")


def get_cookiefile():
    default_cookiefile = {
        "Windows": "~/AppData/Roaming/Mozilla/Firefox/Profiles/User1/cookies.sqlite",
        "Darwin": "~/Library/Application Support/Firefox/Profiles/User1/cookies.sqlite",
    }.get(system(), "~/.mozilla/firefox/User1/cookies.sqlite")
    cookiefiles = glob(expanduser(default_cookiefile))
    if not cookiefiles:
        raise SystemExit("No Firefox cookies.sqlite file found. Use -c COOKIEFILE.")
    return cookiefiles[0]


def import_session(cookiefile, sessionfile):
    print("Using cookies from {}.".format(cookiefile))
    conn = connect(f"file:{cookiefile}?immutable=1", uri=True)
    try:
        cookie_data = conn.execute(
            "SELECT name, value FROM moz_cookies WHERE baseDomain='instagram.com'"
        )
    except OperationalError:
        cookie_data = conn.execute(
            "SELECT name, value FROM moz_cookies WHERE host LIKE '%instagram.com'"
        )
    instaloader = Instaloader(max_connection_attempts=1)
    instaloader.context._session.cookies.update(cookie_data)
    username = instaloader.test_login()
    if not username:
        raise SystemExit("Not logged in. Are you logged in successfully in Firefox?")
    print("Imported session cookie for {}.".format(username))
    instaloader.context.username = username
    instaloader.save_session_to_file(sessionfile)


if __name__ == "__main__":
    p = ArgumentParser()
    p.add_argument("-c", "--cookiefile")
    p.add_argument("-f", "--sessionfile")
    args = p.parse_args()
    try:
        import_session(args.cookiefile or get_cookiefile(), args.sessionfile)
    except (ConnectionException, OperationalError) as e:
        raise SystemExit("Cookie import failed: {}".format(e))
    
    L = Instaloader()

    while True:
        
        PROFILE = input("Insert profile name: ")
        profile = Profile.from_username(L.context, PROFILE)
        posts_sorted_by_likes = sorted(profile.get_posts(),
                                    key=lambda p: p.likes + p.comments,
                                    reverse=True)

        for post in islice(posts_sorted_by_likes, ceil(profile.mediacount * X_percentage / 100)):
            L.download_post(post, PROFILE)
