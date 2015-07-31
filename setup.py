#!/usr/bin/env python

from os import path, getcwd
from setuptools import setup, find_packages
from apt.package import Package
from IPython.core.release import long_description

with open(path.join(getcwd(), 'readme.md')) as f:
    long_description = f.read()


setup(name='RedditImageGrab',
      version='0.1',
      description='Downloads JPEG images from sub-reddits of reddit.com',
      long_description=long_description,
      packages=find_packages(),
      package_data = {'': ['*.md']}, 

      # metadata for upload to PyPI
      author='HoverHell',
      author_email='hoverhell@gmail.com',
      keywords="reddit image downloader",
      url='https://github.com/HoverHell/RedditImageGrab',


     )
