I created this script to download the latest (and greatest) wallpapers
off of image subreddits like wallpaper to keep my desktop wallpaper
fresh and interesting. The main idea is that the script would download
any JPEG or PNG formatted image that it found listed in the specified
subreddit and download them to a folder.

An example of running this script to download images with a score
greater than 50 from the wallpaper sub-reddit into a folder called
wallpaper would be as follows:

    python redditdownload.py wallpaper wallpaper -score 50

And to run the same query but only get new images you don't already
have, run the following:

    python redditdownload.py wallpaper wallpaper -score 50 -update

Advanced Examples
=================

Retrieve last 10 pics in the 'wallpaper' subreddit with the word
"sunset" in the title (note: case is ignored by (?i) predicate)

    python redditdownload.py wallpaper sunsets -regex '(?i).*sunset.*' -num 10
