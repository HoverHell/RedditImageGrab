"""Download images from a reddit.com subreddit."""

import re
from urllib2 import urlopen, HTTPError, URLError
from httplib import InvalidURL
from argparse import ArgumentParser
from os.path import exists as pathexists, join as pathjoin
from os import mkdir
from reddit import getitems

if __name__ == "__main__":
    PARSER = ArgumentParser(description='Downloads files with specified externsion from the specified subreddit.')
    PARSER.add_argument('reddit', metavar='r', help='Subreddit name.')
    PARSER.add_argument('dir', metavar='d', help='Dir to put downloaded files in.')
    PARSER.add_argument('-last', metavar='l', default='', required=False, help='ID of the last downloaded file.')
    PARSER.add_argument('-score', metavar='s', default='0', type=int, required=False, help='Minimum score of images to download.')
    PARSER.add_argument('-num', metavar='n', default='0', type=int, required=False, help='Number of images to download.')
    PARSER.add_argument('-update', default=False, action='store_true', required=False, help='Run until you encounter a file already downloaded.')
    PARSER.add_argument('-sfw', default=False, action='store_true', required=False, help='Download safe for work images only.')
    PARSER.add_argument('-nsfw', default=False, action='store_true', required=False, help='Download NSFW images only.')
    PARSER.add_argument('-regex', action='store', default=None, required=False, help='Use regex to filter based on title.')
    ARGS = PARSER.parse_args()

    print 'Downloading images from "%s" subreddit' % (ARGS.reddit)

    nTotal = nDownloaded = nErrors = nSkipped = nFailed = 0
    FINISHED = False

    # Create the specified directory if it doesn't already exist.
    if not pathexists(ARGS.dir):
        mkdir(ARGS.dir)

    # If a regex has been specified, compile the rule (once)
    reRule = None
    if ARGS.regex:
        reRule = re.compile(ARGS.regex)

    LAST = ARGS.last

    while not FINISHED:
        ITEMS = getitems(ARGS.reddit, LAST)
        if not ITEMS:
            # No more items to process
            break

        for ITEM in ITEMS:
            nTotal += 1

            if ITEM['score'] < ARGS.score:
                print '\tSCORE: %s has score of %s which is lower than required score of %s.' % (ITEM['id'], ITEM['score'], ARGS.score)
                nSkipped += 1
                continue
            elif ARGS.sfw and ITEM['over_18']:
                print '\tNSFW: %s is marked as NSFW.' % ITEM['id']
                nSkipped += 1
                continue
            elif ARGS.nsfw and not ITEM['over_18']:
                # TODO: too noisy!
                # print '\tNot NSFW, skipping %s' % (ITEM['id'])
                nSkipped += 1
                continue
            elif ARGS.regex and not re.match(reRule, ITEM['title']):
                # TODO: too noisy
                # print '\tRegex match failed'
                nSkipped += 1
                continue

            FILENAME = pathjoin(ARGS.dir, ITEM['id'])

            try:
                if 'imgur.com' in ITEM['url']:
                    if 'imgur.com/a/' in ITEM['url']:
                        print '\tUnsupported imgur album [%s]. Skipping.' % (ITEM['url'])
                        nSkipped += 1
                        continue

                    # Change .png to .jpg for imgur urls.
                    if ITEM['url'].endswith('.png'):
                        ITEM['url'] = ITEM['url'].replace('.png', '.jpg')
                    # Add .jpg to imgur urls that are missing it.
                    elif '.jpg' not in ITEM['url']:
                        ITEM['url'] = '%s.jpg' % ITEM['url']

                RESPONSE = urlopen(ITEM['url'])
                INFO = RESPONSE.info()

                # Work out file type either from the response or the url.
                if 'content-type' in INFO.keys():
                    FILETYPE = INFO['content-type']
                elif ITEM['url'].endswith('.jpg') or ITEM['url'].endswith('.jpeg'):
                    FILETYPE = 'image/jpeg'
                elif ITEM['url'].endswith('.png'):
                    FILETYPE = 'image/png'
                else:
                    FILETYPE = 'unknown'

                # Only try to download acceptable image types
                if not FILETYPE in ['image/jpeg', 'image/png']:
                    print '\tWRONG FILE TYPE: %s has type: %s!' % (ITEM['url'], FILETYPE)
                    nSkipped += 1
                    continue

                # Set file extension based on content-type
                if FILETYPE == 'image/jpeg':
                    FILENAME += '.jpg'
                elif FILETYPE == 'image/png':
                    FILENAME += '.png'

                # Don't download files multiple times!
                if pathexists(FILENAME):
                    print '\tURL [%s] already downloaded.' % (ITEM['url'])
                    nErrors += 1
                    if ARGS.update:
                        print '\tUpdate complete, exiting.'
                        FINISHED = True
                        break

                    continue

                FILEDATA = RESPONSE.read()
                FILE = open(FILENAME, 'wb')
                FILE.write(FILEDATA)
                FILE.close()
                print '\tDownloaded %s to %s.' % (ITEM['url'], FILENAME)
                nDownloaded += 1
            except HTTPError as ERROR:
                    print '\tHTTP ERROR: Code %s for %s.' % (ERROR.code, ITEM['url'])
                    nFailed += 1
            except URLError as ERROR:
                    print '\tURL ERROR: %s!' % ITEM['url']
                    nFailed += 1
            except InvalidURL as ERROR:
                    print '\tInvalid URL: %s!' % ITEM['url']
                    nFailed += 1

            if ARGS.num > 0 and nDownloaded >= ARGS.num:
                FINISHED = True
                break

        LAST = ITEM['id']

    print 'Downloaded %d files (Processed %d, Skipped %d, Exists %d)' % (nDownloaded, nTotal, nSkipped, nErrors)
