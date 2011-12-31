I created this script to download the latest (and greatest) wallpapers off of image sub-reddits like wallpaper to keep my desktop wallpaper fresh and interesting. The main idea is that the script would download any JPEG formatted image that it found listed in the specified sub-reddit and download them to a folder.

An example of running this script to download images with a score greater than 50 from the wallpaper sub-reddit into a folder called wallpaper would be as follows:
    python redditdownload.py wallpaper wallpaper -s 50

And to run the same query but only get new images you don't already have, run the following:
    python redditdownload.py wallpaper wallpaper -s 50 -update

