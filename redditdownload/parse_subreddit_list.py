# -*- coding: utf-8 -*-
"""
Created on Tue Aug 30 15:26:13 2016

@author: jtara1

General syntax for subreddits.txt:
: (color character) denotes folder name
subreddit url or word denotes subreddit

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

parse_subreddit_list('/path/to/subreddits.txt') = [
('wallpapers', '/folder_path/pc-wallpaper/wallpapers'),
('BackgroundArt', '/folder_path/pc-wallpaper/BackgroundArt'),
('EarthPorn', '/folder_path/nature-pics/EarthPorn'),
('Mountain', '/folder_path/Mountain')
]
"""
import re
import os
from os import getcwd, mkdir

def parse_subreddit_list(file_path, root_path=''):
    """ 
        INPUT: file (full path) of list of subreddits, & root_path for root save location
        OUTPUT: list of tuples with full subreddit url and save path (see docstring on line 1 for e.g.)
    """
    try:    
        file = open(file_path, 'r')
    except Exception as e:
        print(e)
        
    output = []
    
    folder_regex = re.compile('([a-zA-Z0-9_\- ]*):\n')
    subreddit_regex = re.compile('(?:https?://)?(?:www.)?reddit.com/r/([a-zA-Z0-9_]*)')
    subreddit_regex2 = re.compile('(?:/r/)?([a-zA-Z0-9_]*)')
    
    if root_path != '':
        folder_path = root_path
    elif root_path == '':
        folder_path = getcwd()
    
    if not os.path.isdir(folder_path):
        mkdir(folder_path)
        
    # iterate through the lines using regex to check if line is subreddit or folder title
    path = folder_path
    for line in file:
        if line == '\n':
            break
        folder_match = re.match(folder_regex, line)
        if folder_match:
            if folder_match.group(1) != '':
                path = os.path.join(folder_path, line[:-2])
                if not os.path.isdir(path):
                    mkdir(path)
            else:
                path = folder_path
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