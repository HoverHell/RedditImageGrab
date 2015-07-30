#!/usr/bin/env python

from distutils.core import setup

setup(name='RedditImageGrab',
      version='0.1',
      description='Downloads JPEG images from sub-reddits of reddit.com',
      author='HoverHell',
      author_email='hoverhell@gmail.com',
      url='https://github.com/HoverHell/RedditImageGrab',
      packages=['img_scrap_stuff', 'reddit', 'redditdownload', 'scrap_wrongies'],
     )
