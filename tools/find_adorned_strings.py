#!/usr/bin/env python3
# -*- Mode:Python; indent-tabs-mode:nil; tab-width:4; encoding:utf-8 -*-
#
# Copyright 2018 Aaron Whitehouse <aaron@whitehouse.kiwi.nz>
#
# This file is part of duplicity.
#
# Duplicity is free software; you can redistribute it and/or modify it
# under the terms of the GNU General Public License as published by the
# Free Software Foundation; either version 2 of the License, or (at your
# option) any later version.
#
# Duplicity is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with duplicity; if not, write to the Free Software Foundation,
# Inc., 59 Temple Place, Suite 330, Boston, MA 02111-1307 USA

# For predictable results in python/3 all string literals need to be marked as unicode, bytes or raw
# This code finds all adorned string literals (strings that are not marked with a u, b or r)

import sys
import tokenize
import token


def return_adorned_string_tokens(f):
    named_tokens = tokenize.tokenize(f.readline)
    for t in named_tokens:
        if t.type == token.STRING and t.string[0] == u'u' and t.string[1] in [u'"', u"'"]:
            yield t


def check_file_for_adorned(filename):
    string_list = []
    with open(filename, u'rb') as f:
        for s in return_adorned_string_tokens(f):
            string_list.append((filename, s.start, s.end, s.string))
    return string_list


if __name__ == u"__main__":
    import argparse

    parser = argparse.ArgumentParser(description=u'Find any adorned string literals in a Python file')
    parser.add_argument(u'file', help=u'The file to search')
    args = parser.parse_args()

    adorned_string_list = check_file_for_adorned(args.file)
    if len(adorned_string_list) == 0:
        print(u"There are no adorned strings in", args.file)
    else:
        print(u"There are adorned strings in", args.file)
        for adorned_string in adorned_string_list:
            print(adorned_string)
            python_file, string_start, string_end, string = adorned_string
            print(string_start, string)
