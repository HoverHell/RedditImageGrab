#!/usr/bin/python
# -*- coding: utf-8 -*-

from unittest import TestCase
from os import getcwd

from redditdownload import parse_args

class TestParseArgs(TestCase):
	def test_simple_args(self):		
		ARGS = parse_args(['funny'])
		self.assertEqual(ARGS.reddit,'funny')
		self.assertEqual(ARGS.dir, getcwd())
		
	def test_multiple_reddit_plus(self):
		ARGS = parse_args(['funny+anime'])
		self.assertEqual(ARGS.reddit,'funny+anime')
	
	def test_nsfw_sfw_arg(self):
		ARGS = parse_args(['--nsfw --sfw'])
		self.assertFalse(ARGS.nsfw)
		self.assertFalse(ARGS.sfw)