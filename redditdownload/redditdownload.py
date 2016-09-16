#!/usr/bin/env python2
"""Download images from a reddit.com subreddit."""


import os
import re
import io
import sys
import json
import logging
from urllib.request import urlopen
from urllib.error import HTTPError, URLError
from http.client import InvalidURL
from argparse import ArgumentParser
from os.path import (
    exists as pathexists, join as pathjoin, basename as pathbasename,
    splitext as pathsplitext)
from os import mkdir, getcwd
import time
from html.parser import HTMLParser

from .gfycat import gfycat
from .reddit import getitems
sys.path.append(os.path.join(os.path.dirname(__file__), 'imgur-downloader'))
from imgurdownloader import ImgurDownloader
from .parse_subreddit_list import parse_subreddit_list


_log = logging.getLogger('redditdownload')


def request(url, *ar, **kwa):
    _retries = kwa.pop('_retries', 4)
    _retry_pause = kwa.pop('_retry_pause', 0)
    res = None
    for _try in range(_retries):
        try:
            res = urlopen(url, *ar, **kwa)
        except Exception as exc:
            if _try == _retries - 1:
                raise
        else:
            break
    return res


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
        self.convert_charrefs = True

    # Handles HTML Elements eg <img src="//blank.jpg" class="picture"/> ->
    #      tag => "img", attrs => [("src", "//blank.jpg"), ("class", "picture")]
    def handle_starttag(self, tag, attrs):
        # Only interested in img when we dont have the url
        # first search for download button
        if tag == "a" and self.IMAGE is None:
            # filter the probably a-tag, or link-tag or download button
            # download link class content of from a-tag class
            download_link_class = 'dev-page-button dev-page-button-with-text dev-page-download'
            # use the same method like below
            for classAttr in attrs:
                if classAttr[0] == "class":
                    # Incase page doesnt have a download button
                    if download_link_class in classAttr[1]:
                        for srcAttr in attrs:
                            if srcAttr[0] == "href":
                                self.IMAGE = srcAttr[1]

        # if download button not found get original image
        elif (tag == "a" or tag == "img") and self.IMAGE is None:
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


# '.wrong_type_pages.jsl'
_WRONGDATA_LOGFILE = os.environ.get('WRONGDATA_LOGFILE')


def _log_wrongtype(_logfile=_WRONGDATA_LOGFILE, **kwa):
    if not _logfile:
        return

    data = json.dumps(kwa) + "\n"
    with open(_logfile, 'a', 1) as f:
        f.write(data)


class WrongFileTypeException(Exception):
    """Exception raised when incorrect content-type discovered"""


class FileExistsException(Exception):
    """Exception raised when file exists in specified directory"""


class URLDNEException(Exception):
    """ Exception raised when URL does not exist """


def extract_imgur_album_urls(album_url):
    """
    Given an imgur album URL, attempt to extract the images within that
    album

    Returns:
        List of qualified imgur URLs
    """
    response = request(album_url)
    info = response.info()

    # Rudimentary check to ensure the URL actually specifies an HTML file
    if 'content-type' in info and not info['content-type'].startswith('text/html'):
        return []

    filedata = response.read()

    match = re.compile(r'\"hash\":\"(.[^\"]*)\"')

    items = []

    try:
        memfile = io.StringIO(filedata)
    except:
        memfile = None

    if memfile == None:
    	return []

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
        raise FileExistsException('%s already downloaded.' % dest_file.split('/')[-1])

    response = request(url)
    info = response.info()
    # with open('repsonse-info.txt', 'w') as f:
    #     f.write(str(info))

    # Work out file type either from the response or the url.
    if 'content-type' in list(info.keys()):
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
    if filetype not in ['image/jpeg', 'image/png', 'image/gif', 'video/webm', 'video/mp4']:
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
    if 'imgur.com/a/' in url or 'imgur.com/gallery/' in url:
        return extract_imgur_album_urls(url)

    # use beautifulsoup4 to find real link
    # find vid url only
    try:
        from bs4 import BeautifulSoup
        html = urlopen(url).read()
        soup = BeautifulSoup(html, 'lxml')
        vid = soup.find('div', {'class': 'video-container'})
        vid_type = 'video/webm'  # or 'video/mp4'
        vid_url = vid.find('source', {'type': vid_type}).get('src')
        if vid_url.startswith('//'):
            vid_url = 'http:' + vid_url
        return vid_url

    except Exception:
        # do nothing for awhile
        pass
    # Change .png to .jpg for imgur urls.
    if url.endswith('.png'):
        url = url.replace('.png', '.jpg')
    else:
        # Extract the file extension
        ext = pathsplitext(pathbasename(url))[1]
        if ext == '.gifv':
            url = url.replace('.gifv', '.gif')
        if not ext:
            # Append a default
            url += '.jpg'
    return [url]


def process_deviant_url(url):
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
        response = request(url)
        filedata = response.read()
        parser = DeviantHTMLParser()
        try:
            parser.feed(filedata.decode('utf-8'))
            if parser.IMAGE is not None:
                return [parser.IMAGE]
            return [url]
        # Exceptions thrown when non-ascii chars are found
        except UnicodeDecodeError:
            if parser.IMAGE is not None:
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

    if 'deviantart.com' in url:
        urls = process_deviant_url(url)
    elif 'gfycat.com' in url:
        # this should handle fat.gfycat.com & zippy.gfycat.com links
        if url.endswith('.webm') or url.endswith('.mp4'):
            return [url]

        # choose the smallest file on gfycat
        gfy_json = gfycat().more(url.split("gfycat.com/")[-1]).json()
        # history_log(os.getcwd(), 'GFYCAT-JSON.txt', mode='write', write_data=gfycat_json) # debug
        if gfy_json["mp4Size"] < gfy_json["webmSize"]:
            urls = [gfy_json["mp4Url"]]
        else:
            urls = [gfy_json["webmUrl"]]
    else:
        urls = [url]

    return urls


def slugify(value):
    """
    Normalizes string, converts to lowercase, removes non-alpha characters,
    and converts spaces to hyphens.
    """
    # taken from http://stackoverflow.com/a/295466
    # with some modification
    import unicodedata
    value = unicodedata.normalize('NFKD', value).encode('ascii', 'ignore')
    value = str(re.sub(r'[^\w\s-]', '', value.decode('ascii')).strip())
    # value = re.sub(r'[-\s]+', '-', value) # not replacing space with hypen
    return value


def remove_extension(mystr):
    """ Returns filename found in mystr by locating image file extension """
    exts = ['.png', '.jpg', 'webm', '.jpeg', '.jfif', '.gif', 'gifv', '.bmp',
            '.tif', '.tiff', '.webp', '.bpg', '.bat',
            '.heif', '.exif', '.ppm', '.cgm', '.svg']
    for e in exts:
        ext_index = mystr.find(e)
        if ext_index != -1:
            return mystr[:ext_index]
    return mystr


def history_log(wdir=os.getcwd(), log_file='log_file.txt', mode='read', write_data=None):
    """Read or write python dictionary from or to a text file

    :param wdir: directory for text file to be saved to
    :param log_file: name of text file (include .txt extension)
    :param mode: 'read' or 'write' are valid
    :param write_data: data that'll get written in the log_file
    :type write_data: dictionary

    .. note:: Big thanks to https://github.com/rachmadaniHaryono for helping cleanup & fix security of this function.
    """
    mode_dict = {
        'read': 'r',
        'write': 'w',
        'append': 'a'
    }
    if mode in mode_dict:
        with open(os.path.join(wdir, log_file), mode_dict[mode]) as f:
            if mode == 'read':
                return json.loads(f.read())
            else:
                f.write(json.dumps(write_data))
                return True
    else:
        logging.debug('history_log func: invalid mode')


def parse_args(args):
    PARSER = ArgumentParser(description='Downloads files with specified extension'
                            'from the specified subreddit.')
    PARSER.add_argument('subreddit', metavar='<subreddit>',
                        help='Subreddit or subreddit list file name.')
    PARSER.add_argument('dir', metavar='<dest_file>', nargs='?',
                        default=getcwd(), help='Dir to put downloaded files in.')
    PARSER.add_argument('--multireddit', default=False, action='store_true',
                        required=False,
                        help='Take multirredit instead of subreddit as input.'
                        'If so, provide /user/m/multireddit-name as argument')
    PARSER.add_argument('--subreddit-list', metavar='srl', default=False, type=str,
                        required=False, nargs=1,
                        help='name of text file containing list of subreddits')
    PARSER.add_argument('--last', metavar='l', default='', required=False,
                        help='ID of the last downloaded file.')
    PARSER.add_argument('--score', metavar='s', default=0, type=int, required=False,
                        help='Minimum score of images to download.')
    PARSER.add_argument('--num', metavar='n', default=1000, type=int, required=False,
                        help='Number of images to download. Set to 0 to disable the limit')
    PARSER.add_argument('--update', default=False, action='store_true', required=False,
                        help='Run until you encounter a file already downloaded.')
    PARSER.add_argument('--sfw', default=False, action='store_true', required=False,
                        help='Download safe for work images only.')
    PARSER.add_argument('--nsfw', default=False, action='store_true', required=False,
                        help='Download NSFW images only.')
    PARSER.add_argument('--filename-format', default='reddit', required=False,
                        help='Specify filename format: reddit (default), title or url')
    PARSER.add_argument('--title-contain', metavar='TEXT', required=False,
                        help='Download only if title contain text (case insensitive)')
    PARSER.add_argument('--regex', default=None, action='store', required=False,
                        help='Use Python regex to filter based on title.')
    PARSER.add_argument('--verbose', default=False, action='store_true',
                        required=False, help='Enable verbose output.')
    PARSER.add_argument('--skipAlbums', default=False, action='store_true',
                        required=False, help='Skip all albums')
    PARSER.add_argument('--mirror-gfycat', default=False, action='store_true', required=False,
                        help='Download available mirror in gfycat.com.')
    PARSER.add_argument('--sort-type', default=None, help='Sort the subreddit.')

    # TODO fix if regex, title contain activated

    parsed_argument = PARSER.parse_args(args)

    if parsed_argument.sfw is True and parsed_argument.nsfw is True:
        # negate both argument if both argument exist
        parsed_argument.sfw = parsed_argument.nsfw = False

    return parsed_argument


def parse_reddit_argument(reddit_args):
    if '+' not in reddit_args:
        return 'Downloading images from "%s" subreddit' % (reddit_args)
    elif len('Downloading images from "%s" subreddit' % (reddit_args)) > 80:
        # other print format if the line is more than 80 chars
        return 'Downloading images from subreddits:\n{}'.format('\n'.join(reddit_args.split('+')))
    else:
        # print in one line but with nicer format
        return 'Downloading images from "%s" subreddit' % (', '.join(reddit_args.split('+')))


def main(args):
    ARGS = parse_args(args if len(args)>0 else sys.argv[1:])

    logging.basicConfig(level=logging.INFO)

    # value at first index is of current subreddit, second index is total
    TOTAL, DOWNLOADED, ERRORS, SKIPPED, FAILED =  [0,0], [0,0], [0,0], [0,0], [0,0]
    PROG_REPORT = [TOTAL, DOWNLOADED, ERRORS, SKIPPED, FAILED]

    # Create the specified directory if it doesn't already exist.
    if not pathexists(ARGS.dir):
        mkdir(ARGS.dir)

    # If a regex has been specified, compile the rule (once)
    RE_RULE = None
    if ARGS.regex:
        RE_RULE = re.compile(ARGS.regex)

    # compile reddit comment url to check if url is one of them
    reddit_comment_regex = re.compile(r'.*reddit\.com\/r\/(.*?)\/comments')

    start_time = None
    ITEM = None

    sort_type = ARGS.sort_type
    if sort_type:
        sort_type = sort_type.lower()

    # check to see if ARGS.subreddit is subreddit or subreddit-list
    if os.path.isfile(ARGS.subreddit) and os.path.splitext(ARGS.subreddit)[1] != '':
        print('I see a srl')
        ARGS.subreddit_list = ARGS.subreddit

    if ARGS.subreddit_list:
        # ARGS.subreddit_list = ARGS.subreddit_list[0] # can't remember why I did this -jtara1
        subreddit_file = ARGS.subreddit_list
        print('subreddit_file: %s' % (subreddit_file))
        subreddit_list = parse_subreddit_list(subreddit_file, ARGS.dir)
        if ARGS.verbose:
            print('subreddit_list = %s' % subreddit_list)
    elif not ARGS.subreddit_list:
        subreddit_list = [(ARGS.subreddit, ARGS.dir)]

    # iterate through subreddit(s)
    for index, section in enumerate(subreddit_list):
        (ARGS.subreddit, ARGS.dir) = section
        FINISHED = False

        if ARGS.verbose:
            print ('index: %s %s %s' % (index, ARGS.subreddit, ARGS.dir))

        # this file will keep track of last-id of sort_type of subreddit downloaded from
        log_file = '._history.txt'
        try:
            log_data = history_log(ARGS.dir, log_file, 'read')
            last_id = log_data[ARGS.subreddit][ARGS.sort_type]['last-id']
        except Exception as e:
            last_id = ''
            log_data = {
                ARGS.subreddit: {
                    ARGS.sort_type: {
                        'last-id': ''
                    }
                }
            }
            history_log(ARGS.dir, log_file, 'write', log_data)
            if ARGS.verbose:
                print ('Did not load last-id from %s file, created new %s' % (log_file, log_file))

        TOTAL[0], DOWNLOADED[0], ERRORS[0], SKIPPED[0], FAILED[0], FILECOUNT = 0, 0, 0, 0, 0, 0

        # ITEMS loop - begin the loop to get reddit submissions & download media from them
        while not FINISHED:
            if ARGS.verbose:
                print()
                # print('Begining ITEMS loop')
                # print('last_id: %s' % last_id)

            ITEMS = getitems(
                ARGS.subreddit, multireddit=ARGS.multireddit, previd=last_id,
                reddit_sort=sort_type)

            # debug ITEMS variable value
            if ARGS.verbose:
               history_log(os.getcwd(), 'ITEMS.txt', 'write', ITEMS)

            # measure time and set the program to wait 4 second between request
            # as per reddit api guidelines
            end_time = time.clock()

            if start_time is not None:
                elapsed_time = end_time - start_time

                if elapsed_time <= 4:  # throttling
                    time.sleep(4 - elapsed_time)

            start_time = time.clock()

            # No more items to process
            if not ITEMS:
                if ARGS.verbose:
                    print('No more ITEMS for this %s of this %s' %
                            (ARGS.subreddit, ARGS.sort_type))
                break

            for ITEM in ITEMS:
                TOTAL[0] += 1

                # not downloading if url is reddit comment
                if ('reddit.com/r/' + ARGS.subreddit + '/comments/' in ITEM['url'] or
                        re.match(reddit_comment_regex, ITEM['url']) is not None):
                    continue

                if ITEM['score'] < ARGS.score:
                    if ARGS.verbose:
                        print('    SCORE: {} has score of {}'.format(ITEM['id'], ITEM['score']))
                        'which is lower than required score of {}.'.format(ARGS.score)

                    SKIPPED[0] += 1
                    continue
                elif ARGS.sfw and ITEM['over_18']:
                    if ARGS.verbose:
                        print('    NSFW: %s is marked as NSFW.' % (ITEM['id']))

                    SKIPPED[0] += 1
                    continue
                elif ARGS.nsfw and not ITEM['over_18']:
                    if ARGS.verbose:
                        print('    Not NSFW, skipping %s' % (ITEM['id']))

                    SKIPPED[0] += 1
                    continue
                elif ARGS.regex and not re.match(RE_RULE, ITEM['title']):
                    if ARGS.verbose:
                        print('    Regex match failed')

                    SKIPPED[0] += 1
                    continue
                elif ARGS.skipAlbums and 'imgur.com/a/' in ITEM['url']:
                    if ARGS.verbose:
                        print('    Album found, skipping %s' % (ITEM['id']))

                    SKIPPED[0] += 1
                    continue

                if ARGS.title_contain and ARGS.title_contain.lower() not in ITEM['title'].lower():
                    if ARGS.verbose:
                        print('    Title not contain "{}",'.format(ARGS.title_contain))
                        'skipping {}'.format(ITEM['id'])

                    SKIPPED[0] += 1
                    continue

                try:
                    URLS = extract_urls(ITEM['url'])
                except URLError as e:
                    print('URLError %s' % e)
                    continue
                except Exception as e:
                    _log.exception("%s", e)
                    continue
                for URL in URLS:
                    try:
                        # Find gfycat if requested
                        if URL.endswith('gif') and ARGS.mirror_gfycat:
                            check = gfycat().check(URL)
                            if check.get("urlKnown"):
                                URL = check.get('webmUrl')

                        # Trim any http query off end of file extension.
                        FILEEXT = pathsplitext(URL)[1]
                        if '?' in FILEEXT:
                            FILEEXT = FILEEXT[:FILEEXT.index('?')]

                        # Only append numbers if more than one file
                        FILENUM = ('_%d' % FILECOUNT if len(URLS) > 1 else '')

                        # create filename based on given input from user
                        if ARGS.filename_format == 'url':
                            FILENAME = '%s%s%s' % (pathsplitext(pathbasename(URL))[0], '', FILEEXT)
                        elif ARGS.filename_format == 'title':
                            FILENAME = '%s%s%s' % (slugify(ITEM['title']), FILENUM, FILEEXT)

                            if len(FILENAME) >= 256:
                                shortened_item_title = slugify(ITEM['title'])[:256-len(FILENAME)]
                                FILENAME = '%s%s%s' % (shortened_item_title, FILENUM, FILEEXT)
                        else:
                            FILENAME = '%s%s%s' % (ITEM['id'], FILENUM, FILEEXT)

                        # join file with directory
                        FILEPATH = pathjoin(ARGS.dir, FILENAME)

                        # Improve debuggability list URL before download too.
                        # url may be wrong so skip that
                        if URL.encode('utf-8') == 'http://':
                            raise URLError('Url is empty')

                        # Download the image
                        try:
                            dl = skp = 0
                            if 'imgur.com' in URL:
                                save_path=os.path.join(os.getcwd(), ARGS.dir)
                                downloader=ImgurDownloader(URL, save_path,
                                                             remove_extension(FILENAME),
                                                             delete_dne=True, debug=False)
                                (dl, skp) = downloader.save_images()
                            else:
                                download_from_url(URL, FILEPATH)
                                dl = 1
                            # Image downloaded successfully!
                            if ARGS.verbose:
                                print('Saved %s as %s' % (URL, FILENAME))
                            DOWNLOADED[0] += 1
                            SKIPPED[0] += skp
                            FILECOUNT += 1

                        except Exception as e:
                            print (e)
                            ERRORS[0] += 1

                        if ARGS.num and (DOWNLOADED[0]) >= ARGS.num:
                            print('    Download num limit reached, exiting.')
                            FINISHED = True
                            break
                    except WrongFileTypeException as ERROR:
                        _log_wrongtype(url=URL, target_dir=ARGS.dir,
                                       filecount=FILECOUNT, _downloaded=DOWNLOADED[0],
                                       filename=FILENAME)
                        SKIPPED[0] += 1
                    except FileExistsException as ERROR:
                        ERRORS[0] += 1
                        if ARGS.update:
                            print('    Update complete, exiting.')
                            FINISHED = True
                            break
                    except HTTPError as ERROR:
                        FAILED[0] += 1
                    except URLError as ERROR:
                        FAILED[0] += 1
                    except InvalidURL as ERROR:
                        FAILED[0] += 1
                    except Exception as exc:
                        FAILED[0] += 1

                # keep track of last_id id downloaded
                last_id = ITEM['id'] if ITEM is not None else None
                if last_id:
                    log_data[ARGS.subreddit][ARGS.sort_type]['last-id'] = last_id
                    history_log(ARGS.dir, log_file, mode='write', write_data=log_data)

                # break out of URL loop to end of ITEMS loop
                if FINISHED:
                    break

            # update variables in PROG_REPORT in SUBREDDIT loop
            for var in PROG_REPORT:
                var[1] += var[0]

    print('Downloaded from %i reddit submissions' % (DOWNLOADED[1]))
    print('(Processed %i, Skipped %i, Errors %i)' % (TOTAL[1], SKIPPED[1], ERRORS[1]))

    return DOWNLOADED[1]


if __name__ == "__main__":
    main("")
