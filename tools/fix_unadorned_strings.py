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
# This code finds all unadorned string literals (strings that are not marked with a u, b or r)

import tokenize
import token


def return_unadorned_string_tokens(f):
    named_tokens = tokenize.tokenize(f.readline)
    for t in named_tokens:
        if t.type == token.STRING and t.string[0] in ['"', "'"]:
            yield t


def check_file_for_unadorned(filename):
    string_list = []
    with open(filename, 'rb') as f:
        for s in return_unadorned_string_tokens(f):
            string_list.append((filename, s.start, s.end, s.string))
    return string_list


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description='Fix any unadorned string literals in a Python file')
    parser.add_argument('file', help='The file to search')
    args = parser.parse_args()

    lines = open(args.file, "r").readlines()
    lines = [list(line) for line in lines]

    unadorned_string_list = check_file_for_unadorned(args.file)
    if len(unadorned_string_list) == 0:
        print("There are no unadorned strings in", args.file)
    else:
        print("There are unadorned strings in", args.file, "\n")

        locs = {}
        for unadorned_string in unadorned_string_list:
            print(unadorned_string)
            python_file, string_start, string_end, strings = unadorned_string
            linenum = int(string_start[0]) - 1
            colnum = int(string_start[1])
            if linenum in locs:
                locs[linenum].insert(0, colnum)
            else:
                locs[linenum] = [colnum]

        for linenum in sorted(locs.keys()):
            for colnum in locs[linenum]:
                lines[linenum].insert(colnum, 'u')
            print("{}: {}: {}".format(linenum, len(locs[linenum]), ''.join(lines[linenum][:-1])))

        lines = [''.join(line) for line in lines]
        open(args.file, "w").writelines(lines)
