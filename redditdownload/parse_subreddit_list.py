# -*- coding: utf-8 -*-
"""
Created on Tue Aug 30 15:26:13 2016

@author: jtara1

General syntax for subreddits.txt:
: (colon character) denotes folder name
subreddit url or word denotes subreddit

For more examples see https://github.com/jtara1/RedditImageGrab/commit/8e4787ef9ac43ca694fc663be026f69a568bb622

Example of expected input and output:

subreddits.txt = "
pc-wallpapers:
https://www.reddit.com/r/wallpapers/
/r/BackgroundArt/

nature_pics:
http://www.reddit.com/r/EarthPorn/

:
Mountain
"

parse_subreddit_list('/MyPath/subreddits.txt', '/MyPath/') = [
('wallpapers', '/MyPath/pc-wallpaper/wallpapers'),
('BackgroundArt', '/MyPath/pc-wallpaper/BackgroundArt'),
('EarthPorn', '/MyPath/nature-pics/EarthPorn'),
('Mountain', '/MyPath/Mountain')
]
"""

import re
import os
from os import getcwd, mkdir

def parse_subreddit_list(file_path, base_path=getcwd()):
    """Gets list of subreddits from a file & returns folder for media from each subreddit

    :param file_path: path of text file to load subreddits from (relative or full path)
    :param base_path: base path that gets returned with each subreddit

    :return: list containing tuples of subreddit & its associated folder to get media saved to
    :rtype: list
    """
    try:
        file = open(file_path, 'r')
    except IOError as e:
        print(e)
        raise IOError

    output = []

    folder_regex = re.compile('([a-zA-Z0-9_\- ]*):\n')
    subreddit_regex = re.compile('(?:https?://)?(?:www.)?reddit.com/r/([a-zA-Z0-9_]*)')
    subreddit_regex2 = re.compile('(?:/r/)?([a-zA-Z0-9_]*)')

    if not os.path.isdir(base_path):
        mkdir(base_path)

    # iterate through the lines using regex to check if line is subreddit or folder title
    path = base_path
    for line in file:
        if line == '\n':
            continue
        folder_match = re.match(folder_regex, line)
        if folder_match:
            if folder_match.group(1) != '':
                path = os.path.join(base_path, line[:-2])
                if not os.path.isdir(path):
                    mkdir(path)
            else:
                path = base_path
            continue

        subreddit_match = re.match(subreddit_regex, line)
        if not subreddit_match:
            subreddit_match = re.match(subreddit_regex2, line)
            if not subreddit_match:
                print('No match at position %s' % file.tell() )
                print('parse_subreddit_list Error: No match found, skipping this iteration.')
                continue

        subreddit = subreddit_match.group(1)
        final_path = os.path.join(path, subreddit)
        if not os.path.isdir(final_path):
            mkdir(final_path)
        output.append((subreddit, final_path))

    return output
