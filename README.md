[![Build Status](https://travis-ci.org/HoverHell/RedditImageGrab.svg?branch=master)](https://travis-ci.org/HoverHell/RedditImageGrab)

# RedditImageGrab

I created this script to download the latest (and greatest) wallpapers
off of image subreddits like wallpaper to keep my desktop wallpaper
fresh and interesting. The main idea is that the script would download
any JPEG or PNG formatted image that it found listed in the specified
subreddit and download them to a folder.

## jtara1 Fork

### Features and Changes:



* Adapted to Python 3 mostly by merge from [ohyou/RedditImageGrab](https://github.com/ohyou/RedditImageGrab) along with some additional fixes

* \-\-num cli argument now counts by reddit submission rather than individual image

    * added submodule `imgur-downloader` which enabled the above feature among other things


* file `._history.txt` contains reddit id of last downloaded and is identified by `subreddit` & `ARGS.sort_type`, e.g.:

    > {'wallpapers': {'topmonth': {'last\-id': '4x4so2'}}}

* positional argument, `<subreddit>`, can now autodetect whether value points to subreddit name or subreddit list file


* `--subreddit-list srl-filename` cli argument added where srl is the filename containing list of subreddits to process

    * added function to process subreddit list for subreddit links & associated save location for each

    * at this time, the same cli arguments are used for all subreddits in list, but save folder can be altered

    * examples for subreddits.txt added, in folder `subreddit-list-examples`

* updated progress report variables such as DOWNLOADED and ERRORS to accommodate for processing a list of subreddits

* `--restart` cli arg added which begins downloading from the beginning of the subreddit rather than resuming from last download ID.

### Fixes:

* `--filename-format` cli arg should work as expected

* `gfycat.py` failed to download direct links to .webm & .mp4 files

* `gfycat.py` failed to process gfycat links that did not exist

## Issues

* needs more testing

## Requirements:

 * Python 3
 * Optional requirements: listed in setup.py under extras_require.

## Usage:

See `./redditdl.py --help` for uptodate details.


ordering = ('key', )

    redditdl.py [-h] [--multireddit] [--last l] [--score s] [--num n]
                     [--update] [--sfw] [--nsfw]
                     [--filename-format FILENAME_FORMAT] [--title-contain TEXT]
                     [--regex REGEX] [--verbose] [--skipAlbums]
                     [--mirror-gfycat] [--sort-type SORT_TYPE]
                     <subreddit> [<dest_file>]


Downloads files with specified extension from the specified subreddit.

main arguments:

    subreddit <subreddit>       Subreddit or subreddit list file name.
    dir <dest_file>             Dir to put downloaded files in.

optional arguments:

    -h, --help            show this help message and exit
    --subbreddit-list srl-filename
                          Take a list of subreddits from a text file, srl = subreddits.txt
    --multireddit         Take multirredit instead of subreddit as input. If so,
                        provide /user/m/multireddit-name as argument
    --last l              ID of the last downloaded file.
    --score s             Minimum score of images to download.
    --num n               Number of images to download.
    --update              Run until you encounter a file already downloaded.
    --sfw                 Download safe for work images only.
    --nsfw                Download NSFW images only.
    --regex REGEX         Use Python regex to filter based on title.
    --verbose             Enable verbose output.
    --skipAlbums          Skip all albums
    --mirror-gfycat       Download available mirror in gfycat.com.
    --filename-format FILENAME_FORMAT
                        Specify filename format: reddit (default), title or url
    --sort-type         Sort the subreddit.
    --restart           Begin downloading from beginning of subreddit rather than resuming from last dl subreddit submission.


## Examples

An example of running this script to download images with a score
greater than 50 from the wallpaper sub-reddit into a folder called
wallpaper would be as follows:

    python3 redditdl.py wallpaper wallpaper --score 50

And to run the same query but only get new images you don't already
have, run the following:

    python3 redditdl.py wallpaper wallpaper --score 50 -update

For getting some nice pictures of cats in your catsfolder (wich will be created if it
doesn't exist yet) run:

    python3 redditdl.py cats ~/Pictures/catsfolder --score 1000 --num 5 --sfw --verbose


### Advanced Examples

Retrieve pics from last 10 submission in the 'wallpaper' subreddit with the word
"sunset" in the title (note: case is ignored by (?i) predicate)

    python3 redditdl.py wallpaper sunsets --regex '(?i).*sunset.*' --num 10

Download top week post from subreddit 'animegifs' and use gfycat gif mirror (if available)

	python3 redditdl.py animegifs --sort-type topweek --mirror-gfycat


### Sorting

Available sorting are following : hot, new, rising, controversial, top, gilded

'top' and 'controversial' sorting can also be extended using available
time limit extension (hour, day, week, month, year, all).

example : tophour, topweek, topweek, controversialhour, controversialweek etc
