"""Download files from a reddit.com subreddit."""

from urllib2 import urlopen
from json import JSONDecoder 
from argparse import ArgumentParser
from os.path import exists as pathexists, join as pathjoin
from os import mkdir

if __name__ == "__main__": 
    PARSER = ArgumentParser( description='Downloads files with specified externsion from the specified subreddit.')
    PARSER.add_argument( 'reddit', metavar='r', help='Subreddit name.')
    PARSER.add_argument( 'extension', metavar='e', help='File extension of interest.')
    PARSER.add_argument( 'dir', metavar='d', help='Dir to put downloaded files in.')
    ARGS = PARSER.parse_args()
 
    print 'Downloading items with exentions "%s" from "%s" subreddit' % (ARGS.extension, ARGS.reddit)
    
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
        # Only try to download files with extensions we are interested in.
        if ITEM['url'].endswith( ARGS.extension ):
            FILENAME = pathjoin( ARGS.dir, '%s.%s' % (ITEM['id'], ARGS.extension) )
            # Don't download files multiple times!
            if not pathexists( FILENAME ): 
                print '\tDownloading %s to %s.' % (ITEM['url'], FILENAME)
                RESPONSE = urlopen( ITEM['url'] )
                FILEDATA = RESPONSE.read()
                FILE = open( FILENAME, 'wb')
                FILE.write(FILEDATA)
                FILE.close()
                D += 1
            else:
                E += 1
        else:
            S += 1

    print 'Downloaded %d of %d (Skipped %d, Exists %d)' % (D, N, S, E)
        
