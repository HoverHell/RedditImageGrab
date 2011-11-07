"""Download files from a reddit.com subreddit."""

from urllib2 import urlopen
from json import JSONDecoder 
from argparse import ArgumentParser
from os.path import exists as pathexists, join as pathjoin
from os import mkdir

if __name__ == "__main__": 
    PARSER = ArgumentParser( description='Downloads files with specified externsion from the specified subreddit.')
    PARSER.add_argument( 'reddit', metavar='r', help='Subreddit name.')
    PARSER.add_argument( 'dir', metavar='d', help='Dir to put downloaded files in.')
    ARGS = PARSER.parse_args()
 
    print 'Downloading images from "%s" subreddit' % (ARGS.reddit)
    
    JSON = urlopen( 'http://www.reddit.com/r/%s.json' % ARGS.reddit ).read()
    DECODER = JSONDecoder()
    DATA = DECODER.decode( JSON )

    ITEMS = [ x['data'] for x in DATA['data']['children'] ]

    # Create the specified directory if it doesn't already exist.
    if not pathexists( ARGS.dir ):
        mkdir( ARGS.dir )

    N = len( ITEMS )
    D = E = S = 0
    for ITEM in ITEMS:
        FILENAME = pathjoin( ARGS.dir, '%s.jpg' % (ITEM['id'] ) )
        # Don't download files multiple times!
        if not pathexists( FILENAME ): 
            RESPONSE = urlopen( ITEM['url'] )
            INFO = RESPONSE.info()
            
            # Work out file type either from the response or the url.
            if 'content-type' in INFO.keys():
                FILETYPE = INFO['content-type']
            elif ITEM['url'].endswith( 'jpg' ):
                FILETYPE = 'image/jpeg'
            elif ITEM['url'].endswith( 'jpeg' ):
                FILETYPE = 'image/jpeg'
            else:
                FILETYPE = 'unknown'
                 
            # Only try to download jpeg images.
            if FILETYPE == 'image/jpeg':
                FILEDATA = RESPONSE.read()
                FILE = open( FILENAME, 'wb')
                FILE.write(FILEDATA)
                FILE.close()
                print '\tDownloaded %s to %s.' % (ITEM['url'],FILENAME)
                D += 1
            else:
                print '\tWRONG FILE TYPE: %s has type: %s!' % (ITEM['url'],INFO['content-type'])
                S += 1
        else:
            print '\tALREADY EXISTS: %s for %s already exists.' % (FILENAME,ITEM['url'])
            E += 1

    print 'Downloaded %d of %d (Skipped %d, Exists %d)' % (D, N, S, E)
        
