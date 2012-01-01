"""Download images from a reddit.com subreddit."""

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
    PARSER.add_argument('-num', metavar='n', default='0', type=int, required=False, help='Number of images to process.')
    PARSER.add_argument('-update', default=False, action='store_true', required=False, help='Run until you encounter a file already downloaded.')
    PARSER.add_argument('-sfw', default=False, action='store_true', required=False, help='Download safe for work images only.')
    ARGS = PARSER.parse_args()

    print 'Downloading images from "%s" subreddit' % (ARGS.reddit)

    ITEMS = getitems(ARGS.reddit, ARGS.last)
    nTotal = nDownloaded = nErrors = nSkipped = F = 0
    FINISHED = False

    # Create the specified directory if it doesn't already exist.
    if not pathexists(ARGS.dir):
        mkdir(ARGS.dir)

    while len(ITEMS) > 0 and not FINISHED:
        LAST = ''
        for ITEM in ITEMS:
            if ITEM['score'] < ARGS.score:
                print '\tSCORE: %s has score of %s which is lower than required score of %s.' % (ITEM['id'], ITEM['score'], ARGS.score)
                nSkipped += 1
            elif ARGS.sfw and ITEM['over_18']:
                print '\tNSFW: %s is marked as NSFW.' % ITEM['id']
                nSkipped += 1
            else:
                FILENAME = pathjoin(ARGS.dir, '%s.jpg' % (ITEM['id']))
                # Don't download files multiple times!
                if not pathexists(FILENAME):
                    try:
                        if 'imgur.com' in ITEM['url']:
                            # Change .png to .jpg for imgur urls.
                            if ITEM['url'].endswith('.png'):
                                ITEM['url'] = ITEM['url'].replace('.png', '.jpg')
                            # Add .jpg to imgur urls that are missing it.
                            elif '.jpg' not in ITEM['url']:
                                ITEM['url'] = '%s.jpg' % ITEM['url']
                            elif '.jpeg' not in ITEM['url']:
                                ITEM['url'] = '%s.jpg' % ITEM['url']

                        RESPONSE = urlopen(ITEM['url'])
                        INFO = RESPONSE.info()

                        # Work out file type either from the response or the url.
                        if 'content-type' in INFO.keys():
                            FILETYPE = INFO['content-type']
                        elif ITEM['url'].endswith('jpg'):
                            FILETYPE = 'image/jpeg'
                        elif ITEM['url'].endswith('jpeg'):
                            FILETYPE = 'image/jpeg'
                        else:
                            FILETYPE = 'unknown'

                        # Only try to download jpeg images.
                        if FILETYPE == 'image/jpeg':
                            FILEDATA = RESPONSE.read()
                            FILE = open(FILENAME, 'wb')
                            FILE.write(FILEDATA)
                            FILE.close()
                            print '\tDownloaded %s to %s.' % (ITEM['url'], FILENAME)
                            nDownloaded += 1
                        else:
                            print '\tWRONG FILE TYPE: %s has type: %s!' % (ITEM['url'], FILETYPE)
                            nSkipped += 1
                    except HTTPError as ERROR:
                            print '\tHTTP ERROR: Code %s for %s.' % (ERROR.code, ITEM['url'])
                            F += 1
                    except URLError as ERROR:
                            print '\tURL ERROR: %s!' % ITEM['url']
                            F += 1
                    except InvalidURL as ERROR:
                            print '\tInvalid URL: %s!' % ITEM['url']
                            F += 1
                else:
                    print '\tALREADY EXISTS: %s for %s already exists.' % (FILENAME, ITEM['url'])
                    nErrors += 1
                    if ARGS.update:
                        print '\tUpdate complete, exiting.'
                        FINISHED = True
                        break
            LAST = ITEM['id']
            nTotal += 1
            if ARGS.num > 0 and nTotal >= ARGS.num:
                print '\t%d images attempted , exiting.' % nTotal
                FINISHED = True
                break
        ITEMS = getitems(ARGS.reddit, LAST)

    print 'Downloaded %d of %d (Skipped %d, Exists %d)' % (nDownloaded, nTotal, nSkipped, nErrors)
