#!/usr/bin/env python2
"""Download images from a reddit.com subreddit."""

import re
import StringIO
from urllib2 import urlopen, HTTPError, URLError
from httplib import InvalidURL
from argparse import ArgumentParser
from os.path import exists as pathexists, join as pathjoin, basename as pathbasename, splitext as pathsplitext, basename as pathbasename, splitext as pathsplitext
from os import mkdir, getcwd
from reddit import getitems
from HTMLParser import HTMLParser

try:
    from gfycat.gfycat import gfycat
    GFYCAT_OPTION = True
except ImportError:
    GFYCAT_OPTION = False
    pass

# Used to extract src from Deviantart URLs
class DeviantHTMLParser(HTMLParser):
    """
    Parses the DeviantArt Web page in search for a link to the main image on page

    Attributes:
        IMAGE  - Direct link to image
    """
    def __init__(self):
        self.reset()
        self.IMAGE = None
    # Handles HTML Elements eg <img src="//blank.jpg" class="picture"/> ->
    #      tag => "img", attrs => [("src", "//blank.jpg"), ("class", "picture")]
    def handle_starttag(self, tag, attrs):
        # Only interested in img when we dont have the url
        if (tag == "a" or tag == "img") and self.IMAGE == None:
            # Check attributes for class
            for classAttr in attrs:
                # Check class is dev-content-normal
                if classAttr[0] == "class":
                    # Incase page doesnt have a download button
                    if classAttr[1] == "dev-content-normal":
                        for srcAttr in attrs:
                            if srcAttr[0] == "src":
                                self.IMAGE = srcAttr[1]
                    else:
                        return

_WRONGDATA_LOGFILE = '.wrong_type_pages.jsl'
def _log_wrongtype(_logfile=_WRONGDATA_LOGFILE, **kwa):
    if not _logfile:
        return
    import json
    data = json.dumps(kwa) + "\n"
    with open(_logfile, 'a', 1) as f:
        f.write(data)


class WrongFileTypeException(Exception):
    """Exception raised when incorrect content-type discovered"""


class FileExistsException(Exception):
    """Exception raised when file exists in specified directory"""


def extract_imgur_album_urls(album_url):
    """
    Given an imgur album URL, attempt to extract the images within that
    album

    Returns:
        List of qualified imgur URLs
    """
    response = urlopen(album_url)
    info = response.info()

    # Rudimentary check to ensure the URL actually specifies an HTML file
    if 'content-type' in info and not info['content-type'].startswith('text/html'):
        return []

    filedata = response.read()

    match = re.compile(r'\"hash\":\"(.[^\"]*)\"')

    items = []

    memfile = StringIO.StringIO(filedata)

    for line in memfile.readlines():
        results = re.findall(match, line)
        if not results:
            continue

        items += results

    memfile.close()
    # TODO : url may contain gif image.
    urls = ['http://i.imgur.com/%s.jpg' % (imghash) for imghash in items]

    return urls


def download_from_url(url, dest_file):
    """
    Attempt to download file specified by url to 'dest_file'

    Raises:
        WrongFileTypeException

            when content-type is not in the supported types or cannot
            be derived from the URL

        FileExceptionsException

            If the filename (derived from the URL) already exists in
            the destination directory.
    """
    # Don't download files multiple times!
    if pathexists(dest_file):
        raise FileExistsException('URL [%s] already downloaded.' % url)

    response = urlopen(url)
    info = response.info()

    # Work out file type either from the response or the url.
    if 'content-type' in info.keys():
        filetype = info['content-type']
    elif url.endswith('.jpg') or url.endswith('.jpeg'):
        filetype = 'image/jpeg'
    elif url.endswith('.png'):
        filetype = 'image/png'
    elif url.endswith('.gif'):
        filetype = 'image/gif'
    elif url.endswith('.mp4'):
        filetype = 'video/mp4'
    elif url.endswith('.webm'):
        filetype = 'video/webm'
    else:
        filetype = 'unknown'

    # Only try to download acceptable image types
    if not filetype in ['image/jpeg', 'image/png', 'image/gif','video/webm','video/mp4']:
        raise WrongFileTypeException('WRONG FILE TYPE: %s has type: %s!' % (url, filetype))

    filedata = response.read()
    filehandle = open(dest_file, 'wb')
    filehandle.write(filedata)
    filehandle.close()


def process_imgur_url(url):
    """
    Given an imgur URL, determine if it's a direct link to an image or an
    album.  If the latter, attempt to determine all images within the album

    Returns:
        list of imgur URLs
    """
    if 'imgur.com/a/' in url:
        return extract_imgur_album_urls(url)

    # Change .png to .jpg for imgur urls.
    if url.endswith('.png'):
        url = url.replace('.png', '.jpg')
    else:
        # Extract the file extension
        ext = pathsplitext(pathbasename(url))[1]
        if ext == '.gifv':
            url = url.replace('.gifv','.gif')
        if not ext:
            # Append a default
            url += '.jpg'
    return [url]

def  process_deviant_url(url):
    """
    Given a DeviantArt URL, determine if it's a direct link to an image, or
    a standard DeviantArt Page. If the latter, attempt to acquire Direct link.

    Returns:
        deviantart image url
    """
    # We have it! Dont worry
    if url.endswith('.jpg'):
        return [url]
    else:
        # Get Page and parse for image link
        response = urlopen(url)
        filedata = response.read()
        parser = DeviantHTMLParser()
        try:
            parser.feed(filedata)
            if parser.IMAGE != None:
                return [parser.IMAGE]
            return [url]
        # Exceptions thrown when non-ascii chars are found
        except UnicodeDecodeError as ERROR:
            if parser.IMAGE != None:
                return [parser.IMAGE]
            else:
                return[url]
    # Dont return None!
    return [url]

def extract_urls(url):
    """
    Given an URL checks to see if its an imgur.com URL, handles imgur hosted
    images if present as single image or image album.

    Returns:
        list of image urls.
    """
    urls = []

    if 'imgur.com' in url:
        urls = process_imgur_url(url)
    elif 'deviantart.com' in url:
        urls = process_deviant_url(url)
    elif 'gfycat.com' in url and GFYCAT_OPTION:
        #choose the smallest file on gfycat
        gfycat_json = gfycat().more(url.split("gfycat.com/")[-1]).json()
        if gfycat_json["mp4Size"] < gfycat_json["webmSize"]:
            urls = [gfycat_json["mp4Url"]]
        else :
            urls = [gfycat_json["webmUrl"]]
    else:
        urls = [url]

    return urls

if __name__ == "__main__":
    PARSER = ArgumentParser(description='Downloads files with specified extension from the specified subreddit.')
    PARSER.add_argument('reddit', metavar='<subreddit>', help='Subreddit name.')
    PARSER.add_argument('dir', metavar='<dest_file>',nargs='?', default=getcwd(), help='Dir to put downloaded files in.')
    PARSER.add_argument('-last', metavar='l', default='', required=False, help='ID of the last downloaded file.')
    PARSER.add_argument('-score', metavar='s', default=0, type=int, required=False, help='Minimum score of images to download.')
    PARSER.add_argument('-num', metavar='n', default=0, type=int, required=False, help='Number of images to download.')
    PARSER.add_argument('-update', default=False, action='store_true', required=False, help='Run until you encounter a file already downloaded.')
    PARSER.add_argument('-sfw', default=False, action='store_true', required=False, help='Download safe for work images only.')
    PARSER.add_argument('-nsfw', default=False, action='store_true', required=False, help='Download NSFW images only.')
    PARSER.add_argument('-regex', default=None, action='store', required=False, help='Use Python regex to filter based on title.')
    PARSER.add_argument('-verbose', default=False, action='store_true', required=False, help='Enable verbose output.')
    if GFYCAT_OPTION:
        PARSER.add_argument('--mirror-gfycat', default=False, action='store_true', required=False, help='Download available mirror in gfycat.com.')
    PARSER.add_argument('--filename-format', default='reddit',required=False, help='Specify filename format: "reddit" for reddit id (default) or "url" for file url')
    ARGS = PARSER.parse_args()

    print 'Downloading images from "%s" subreddit' % (ARGS.reddit)

    TOTAL = DOWNLOADED = ERRORS = SKIPPED = FAILED = 0
    FINISHED = False

    # Create the specified directory if it doesn't already exist.
    if not pathexists(ARGS.dir):
        mkdir(ARGS.dir)

    # If a regex has been specified, compile the rule (once)
    RE_RULE = None
    if ARGS.regex:
        RE_RULE = re.compile(ARGS.regex)

    LAST = ARGS.last

    while not FINISHED:
        ITEMS = getitems(ARGS.reddit, LAST)
        if not ITEMS:
            # No more items to process
            break

        for ITEM in ITEMS:
            TOTAL += 1

            if ITEM['score'] < ARGS.score:
                if ARGS.verbose:
                    print '    SCORE: %s has score of %s which is lower than required score of %s.' % (ITEM['id'], ITEM['score'], ARGS.score)

                SKIPPED += 1
                continue
            elif ARGS.sfw and ITEM['over_18']:
                if ARGS.verbose:
                    print '    NSFW: %s is marked as NSFW.' % (ITEM['id'])

                SKIPPED += 1
                continue
            elif ARGS.nsfw and not ITEM['over_18']:
                if ARGS.verbose:
                    print '    Not NSFW, skipping %s' % (ITEM['id'])

                SKIPPED += 1
                continue
            elif ARGS.regex and not re.match(RE_RULE, ITEM['title']):
                if ARGS.verbose:
                    print '    Regex match failed'

                SKIPPED += 1
                continue

            FILECOUNT = 0
            URLS = extract_urls(ITEM['url'])
            for URL in URLS:
                try:
                    # Find gfycat if requested
                    if URL.endswith('gif') and ARGS.mirror_gfycat:
                        check = gfycat().check(URL)
                        if check.get("urlKnown") :
                            URL = check.get('webmUrl')

                    # Trim any http query off end of file extension.
                    FILEEXT = pathsplitext(URL)[1]
                    if '?' in FILEEXT:
                        FILEEXT = FILEEXT[:FILEEXT.index('?')]

                    # Only append numbers if more than one file.
                    FILENUM = ('_%d' % FILECOUNT if len(URLS) > 1 else '')
                    if ARGS.filename_format == 'url' :
                        FILENAME = '%s%s%s' % (pathsplitext(pathbasename(URL))[0], FILENUM, FILEEXT)
                    else:
                        FILENAME = '%s%s%s' % (ITEM['id'], FILENUM, FILEEXT)
                    FILEPATH = pathjoin(ARGS.dir, FILENAME)
                                            
                    # Improve debuggability list URL before download too.
                    print '    Attempting to download URL [%s] as [%s].' % (URL.encode('utf-8'), FILENAME.encode('utf-8'))

                    # Download the image
                    download_from_url(URL, FILEPATH)

                    # Image downloaded successfully!
                    print '    Sucessfully downloaded URL [%s] as [%s].' % (URL, FILENAME)
                    DOWNLOADED += 1
                    FILECOUNT += 1

                    if ARGS.num > 0 and DOWNLOADED >= ARGS.num:
                        FINISHED = True
                        break
                except WrongFileTypeException as ERROR:
                    print '    %s' % (ERROR)
                    _log_wrongtype(url=URL, target_dir=ARGS.dir,
                       _filecount=FILECOUNT, _downloaded=DOWNLOADED,
                       _filename=FILENAME)
                    SKIPPED += 1
                except FileExistsException as ERROR:
                    print '    %s' % (ERROR)
                    ERRORS += 1
                    if ARGS.update:
                        print '    Update complete, exiting.'
                        FINISHED = True
                        break
                except HTTPError as ERROR:
                    print '    HTTP ERROR: Code %s for %s.' % (ERROR.code, URL)
                    FAILED += 1
                except URLError as ERROR:
                    print '    URL ERROR: %s!' % (URL)
                    FAILED += 1
                except InvalidURL as ERROR:
                    print '    Invalid URL: %s!' % (URL)
                    FAILED += 1

            if FINISHED:
                break

        LAST = ITEM['id']

    print 'Downloaded %d files (Processed %d, Skipped %d, Exists %d)' % (DOWNLOADED, TOTAL, SKIPPED, ERRORS)
