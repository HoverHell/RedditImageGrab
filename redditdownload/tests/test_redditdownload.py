#!/usr/bin/python
# -*- coding: utf-8 -*-

from unittest import TestCase
from os import getcwd

from redditdownload import parse_args

class TestParseArgs(TestCase):
	def test_simple_args(self):        
		parser = parse_args(['funny'])
		self.assertEqual(parser.reddit,'funny')
		self.assertEqual(parser.dir, getcwd())

