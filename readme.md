# RedditImageGrab

I created this script to download the latest (and greatest) wallpapers
off of image subreddits like wallpaper to keep my desktop wallpaper
fresh and interesting. The main idea is that the script would download
any JPEG or PNG formatted image that it found listed in the specified
subreddit and download them to a folder.

# Usage:
    redditdownload.py [-h] [-last l] [-score s] [-num n] [-update] [-sfw] [-nsfw] [-regex REGEX] [-verbose] <subreddit> <dest_file>
Downloads files with specified extension from the specified subreddit.

positional arguments:

    <subreddit>    Subreddit name.
    <dest_file>    Dir to put downloaded files in.
optional arguments:

    -h, --help    show this help message and exit
    -last l       ID of the last downloaded file.
    -score s      Minimum score of images to download.
    -num n        Number of images to download.
    -update       Run until you encounter a file already downloaded.
    -sfw          Download safe for work images only.
    -nsfw         Download NSFW images only.
    -regex REGEX  Use Python regex to filter based on title.
    -verbose      Enable verbose output.
    --filename-format FILENAME_FORMAT
                  Specify filename format: reddit (default), title or url


# Examples

An example of running this script to download images with a score
greater than 50 from the wallpaper sub-reddit into a folder called
wallpaper would be as follows:

    python redditdownload.py wallpaper wallpaper -score 50

And to run the same query but only get new images you don't already
have, run the following:

    python redditdownload.py wallpaper wallpaper -score 50 -update

For getting some nice pictures of cats in your catsfolder (wich will be created if it
doesn't exist yet) run:

    python redditdownload.py cats ~/Pictures/catsfolder -score 1000 -num 5 -sfw -verbose

## Advanced Examples

Retrieve last 10 pics in the 'wallpaper' subreddit with the word
"sunset" in the title (note: case is ignored by (?i) predicate)

    python redditdownload.py wallpaper sunsets -regex '(?i).*sunset.*' -num 10
