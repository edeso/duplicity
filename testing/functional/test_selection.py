# -*- Mode:Python; indent-tabs-mode:nil; tab-width:4; encoding:utf-8 -*-
#
# Copyright 2014 Aaron Whitehouse <aaron@whitehouse.kiwi.nz>
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


import io
import os
import platform
import sys
import unittest

from . import FunctionalTestCase, CmdError
from duplicity import log


class IncludeExcludeFunctionalTest(FunctionalTestCase):
    u"""
    This contains methods used in the tests below for testing the include, exclude and various filelist features.
    """

    # These tests assume the following files and logic, with:
    # "is" meaning that the file is included specifically
    # "ia" meaning that the file should be included automatically because its parent is included
    # "ic" meaning that the folder is included because its contents are included
    # "es" meaning that the file is excluded specifically
    # "ea" meaning that the file should be excluded automatically because its parent is excluded
    # select2 (es)
    # --- 1.doc (ea)
    # --- 1.py (is)
    # --- 1 (is)
    # ------ 1sub1 (ia)
    # --------- 1sub1sub1 (ia)
    # ------------ 1sub1sub1_file.txt (ia)
    # --------- 1sub1sub2 (es)
    # ------------ 1sub1sub2_file.txt (ea)
    # --------- 1sub1sub3 (ia)
    # ------------ 1sub1sub3_file.txt (es)
    # ------ 1sub2 (ic)
    # --------- 1sub2sub1 (is)
    # --------- 1sub2sub2 (ea)
    # --------- 1sub2sub3 (es)  # Not necessary as also ea, but to ensure there are no issues doing so
    # ------ 1sub3 (ia)
    # --------- 1sub3sub1 (es)
    # --------- 1sub3sub2 (es)
    # --------- 1sub3sub3 (ia)
    # --- 2 (ic)
    # ------ 2sub1 (is)
    # --------- 2sub1sub1 (ia)
    # ------------ 2sub1sub1_file.txt (ia)
    # --------- 2sub1sub2 (es)
    # --------- 2sub1sub3 (es)
    # ------ 2sub2 (ea)
    # --------- 2sub2sub1 (ea)
    # --------- 2sub2sub2 (ea)
    # --------- 2sub2sub3 (ea)
    # ------ 2sub3 (ea)
    # --------- 2sub3sub1 (ea)
    # --------- 2sub3sub3 (ea)
    # --------- 2sub3sub2 (ea)
    # --- 3 (is)
    # ------ 3sub1 (es)
    # --------- 3sub1sub1 (ea)
    # --------- 3sub1sub2 (ea)
    # --------- 3sub1sub3 (ea)
    # ------ 3sub2 (ia)
    # --------- 3sub2sub1 (ia)
    # --------- 3sub2sub2 (ia)
    # --------- 3sub2sub3 (ia)
    # ------ 3sub3 (is)  # Not necessary as also ia, but to ensure there are no issues doing so
    # --------- 3sub3sub1 (ia)
    # --------- 3sub3sub2 (es, ic)
    # ------------ 3sub3sub2_file.txt (is)
    # --------- 3sub3sub3 (ia)
    # --- trailing_space  (ea)  # Note this is "trailing_space ". Excluded until trailing_space test, when (is)
    # ------ trailing_space sub1 (ea)  # Excluded until trailing_space test, when (ia)
    # ------ trailing_space sub2 (ea)  # Excluded until trailing_space test, when (es, ic)
    # --------- trailing_space sub2_file.txt (ea)  # Excluded until trailing_space test, when (is)

    complete_directory_tree = [
        [u"1", u"2", u"3", u"trailing_space ", u"1.doc", u"1.py"],
        [u"1sub1", u"1sub2", u"1sub3"],
        [u"1sub1sub1", u"1sub1sub2", u"1sub1sub3"],
        [u"1sub1sub1_file.txt"],
        [u"1sub1sub2_file.txt"],
        [u"1sub1sub3_file.txt"],
        [u"1sub2sub1", u"1sub2sub2", u"1sub2sub3"],
        [u"1sub3sub1", u"1sub3sub2", u"1sub3sub3"],
        [u"2sub1", u"2sub2", u"2sub3"],
        [u"2sub1sub1", u"2sub1sub2", u"2sub1sub3"],
        [u"2sub1sub1_file.txt"],
        [u"2sub2sub1", u"2sub2sub2", u"2sub2sub3"],
        [u"2sub3sub1", u"2sub3sub2", u"2sub3sub3"],
        [u"3sub1", u"3sub2", u"3sub3"],
        [u"3sub1sub1", u"3sub1sub2", u"3sub1sub3"],
        [u"3sub2sub1", u"3sub2sub2", u"3sub2sub3"],
        [u"3sub3sub1", u"3sub3sub2", u"3sub3sub3"],
        [u"3sub3sub2_file.txt"],
        [u"trailing_space sub1", u"trailing_space sub2"],
        [u"trailing_space sub2_file.txt"]
    ]

    expected_restored_tree = [[u"1", u"2", u"3", u"1.py"],
                              [u"1sub1", u"1sub2", u"1sub3"],
                              [u"1sub1sub1", u"1sub1sub3"],
                              [u"1sub1sub1_file.txt"],
                              [u"1sub2sub1"],
                              [u"1sub3sub3"],
                              [u"2sub1"],
                              [u"2sub1sub1"],
                              [u"2sub1sub1_file.txt"],
                              [u"3sub2", u"3sub3"],
                              [u"3sub2sub1", u"3sub2sub2", u"3sub2sub3"],
                              [u"3sub3sub1", u"3sub3sub2", u"3sub3sub3"],
                              [u"3sub3sub2_file.txt"]]

    expected_restored_tree_with_trailing_space = [[u"1", u"2", u"3", u"trailing_space ", u"1.py"],
                                                  [u"1sub1", u"1sub2", u"1sub3"],
                                                  [u"1sub1sub1", u"1sub1sub3"],
                                                  [u"1sub1sub1_file.txt"],
                                                  [u"1sub2sub1"],
                                                  [u"1sub3sub3"],
                                                  [u"2sub1"],
                                                  [u"2sub1sub1"],
                                                  [u"2sub1sub1_file.txt"],
                                                  [u"3sub2", u"3sub3"],
                                                  [u"3sub2sub1", u"3sub2sub2", u"3sub2sub3"],
                                                  [u"3sub3sub1", u"3sub3sub2", u"3sub3sub3"],
                                                  [u"3sub3sub2_file.txt"],
                                                  [u"trailing_space sub1", u"trailing_space sub2"],
                                                  [u"trailing_space sub2_file.txt"]]

    def directory_tree_to_list_of_lists(self, parent_directory):
        u"""
        This takes a folder as an input and returns a list with its contents. If the directory has subdirectories, it
        returns a list of lists with the contents of those subdirectories.
        """
        directory_list = []
        for root, dirs, files in os.walk(parent_directory):
            to_add = []
            if dirs:
                dirs.sort()  # So that we can easily compare to what we expect
                to_add = dirs
            if files:
                files.sort()  # So that we can easily compare to what we expect
                to_add += files
            if to_add:
                directory_list.append(to_add)
        return directory_list


class TestCheckTestFiles(IncludeExcludeFunctionalTest):
    u""" Tests the testfiles required by the exclude/include tests are as expected. """

    def test_files_are_as_expected(self):
        u"""Test that the contents of testfiles/select are as expected."""
        testfiles = self.directory_tree_to_list_of_lists(u"testfiles/select2")
        self.assertEqual(testfiles, self.complete_directory_tree)


class TestFilesFrom(IncludeExcludeFunctionalTest):
    u""" Tests behaviours when --files-from is used """

    # all the files in testfiles/select2 which are named with numbers
    testfiles_numbers = [u"2",
                         u"2/2sub3",
                         u"2/2sub3/2sub3sub2",
                         u"2/2sub3/2sub3sub1",
                         u"2/2sub3/2sub3sub3",
                         u"2/2sub1",
                         u"2/2sub1/2sub1sub3",
                         u"2/2sub1/2sub1sub2",
                         u"2/2sub1/2sub1sub1",
                         u"2/2sub1/2sub1sub1/2sub1sub1_file.txt",
                         u"2/2sub2",
                         u"2/2sub2/2sub2sub3",
                         u"2/2sub2/2sub2sub1",
                         u"2/2sub2/2sub2sub2",
                         u"1.doc",
                         u"1.py",
                         u"1",
                         u"1/1sub3",
                         u"1/1sub3/1sub3sub2",
                         u"1/1sub3/1sub3sub1",
                         u"1/1sub3/1sub3sub3",
                         u"1/1sub1",
                         u"1/1sub1/1sub1sub2",
                         u"1/1sub1/1sub1sub2/1sub1sub2_file.txt",
                         u"1/1sub1/1sub1sub3",
                         u"1/1sub1/1sub1sub3/1sub1sub3_file.txt",
                         u"1/1sub1/1sub1sub1",
                         u"1/1sub1/1sub1sub1/1sub1sub1_file.txt",
                         u"1/1sub2",
                         u"1/1sub2/1sub2sub3",
                         u"1/1sub2/1sub2sub2",
                         u"1/1sub2/1sub2sub1",
                         u"3",
                         u"3/3sub3",
                         u"3/3sub3/3sub3sub3",
                         u"3/3sub3/3sub3sub1",
                         u"3/3sub3/3sub3sub2",
                         u"3/3sub3/3sub3sub2/3sub3sub2_file.txt",
                         u"3/3sub2",
                         u"3/3sub2/3sub2sub1",
                         u"3/3sub2/3sub2sub3",
                         u"3/3sub2/3sub2sub2",
                         u"3/3sub1",
                         u"3/3sub1/3sub1sub3",
                         u"3/3sub1/3sub1sub1",
                         u"3/3sub1/3sub1sub2"]

    def test_error_on_files_from_absolute_path(self):
        u""" Check expected failure on absolute paths """
        with io.open(u"testfiles/files_from.txt", u"w") as f:
            f.write(u"/testfiles/select2/1/1sub1/1sub1sub1/1sub1sub1_file.txt\n"
                    u"/testfiles/select2/1/1sub1/1sub1sub2/1sub1sub2_file.txt\n"
                    u"/testfiles/select2/1/1sub1/1sub1sub3/1sub1sub3_file.txt\n"
                    u"/testfiles/select2/2/2sub1/2sub1sub1/2sub1sub1_file.txt\n"
                    u"/testfiles/select2/3/3sub3/3sub3sub2/3sub3sub2_file.txt")
        with self.assertRaises(CmdError) as context:
            self.backup(u"full", u"testfiles/select2",
                        options=[u"--files-from", u"testfiles/files_from.txt"])
        self.assertEqual(context.exception.exit_status, log.ErrorCode.absolute_files_from)

    def test_error_on_files_from_empty(self):
        u""" Check expected failure if file list is empty """
        with io.open(u"testfiles/files_from.txt", u"w") as f:
            pass
        with self.assertRaises(CmdError) as context:
            self.backup(u"full", u"testfiles/select2",
                        options=[u"--files-from", u"testfiles/files_from.txt"])
        self.assertEqual(context.exception.exit_status, log.ErrorCode.empty_files_from)

    def test_files_from_no_selections(self):
        u""" Simplest use case, with no additional selection functions """
        with io.open(u"testfiles/files_from.txt", u"w") as f:
            f.write(u"1.doc\n"
                    u"1.py")
        self.backup(u"full", u"testfiles/select2",
                    options=[u"--files-from", u"testfiles/files_from.txt"])
        self.restore()
        restore_path = u"testfiles/restore_out"
        restored = self.directory_tree_to_list_of_lists(restore_path)
        self.assertEqual(restored, [[u"1.doc", u"1.py"]])

    def test_files_from_implicit_parents(self):
        u""" Confirm that parent directories get included implicitly """
        with io.open(u"testfiles/files_from.txt", u"w") as f:
            f.write(u"1/1sub1/1sub1sub1/1sub1sub1_file.txt\n"
                    u"1/1sub1/1sub1sub2/1sub1sub2_file.txt\n"
                    u"1/1sub1/1sub1sub3/1sub1sub3_file.txt\n"
                    u"2/2sub1/2sub1sub1/2sub1sub1_file.txt\n"
                    u"3/3sub3/3sub3sub2/3sub3sub2_file.txt")
        self.backup(u"full", u"testfiles/select2",
                    options=[u"--files-from", u"testfiles/files_from.txt"])
        self.restore()
        restore_path = u"testfiles/restore_out"
        restored = self.directory_tree_to_list_of_lists(restore_path)
        self.assertEqual(restored, [[u"1", u"2", u"3"],
                                    [u"1sub1"], [u"1sub1sub1", u"1sub1sub2", u"1sub1sub3"],
                                    [u"1sub1sub1_file.txt"], [u"1sub1sub2_file.txt"], [u"1sub1sub3_file.txt"],
                                    [u"2sub1"], [u"2sub1sub1"], [u"2sub1sub1_file.txt"],
                                    [u"3sub3"], [u"3sub3sub2"], [u"3sub3sub2_file.txt"]])

    def test_files_from_trailing_space(self):
        u""" Check that trailing space is preserved """
        with io.open(u"testfiles/files_from.txt", u"w") as f:
            f.write(u"trailing_space /trailing_space sub1\n"
                    u"trailing_space /trailing_space sub2/trailing_space sub2_file.txt")
        self.backup(u"full", u"testfiles/select2",
                    options=[u"--files-from", u"testfiles/files_from.txt"])
        self.restore()
        restore_path = u"testfiles/restore_out"
        restored = self.directory_tree_to_list_of_lists(restore_path)
        self.assertEqual(restored, [[u"trailing_space "],
                                    [u"trailing_space sub1", u"trailing_space sub2"],
                                    [u"trailing_space sub2_file.txt"]])

    def test_files_from_trailing_space_folder(self):
        u""" Check that trailing space is preserved where it isn't delimited
        by another path component or implied by another path in the same file
        """
        with io.open(u"testfiles/files_from.txt", u"w") as f:
            f.write(u"trailing_space ")
        self.backup(u"full", u"testfiles/select2",
                    options=[u"--files-from", u"testfiles/files_from.txt"])
        self.restore()
        restore_path = u"testfiles/restore_out"
        restored = self.directory_tree_to_list_of_lists(restore_path)
        self.assertEqual(restored, [[u"trailing_space "]])

    def test_files_from_with_exclusions(self):
        u""" Apply some --exclude rules to a backup fileset defined by --files-from"""
        with io.open(u"testfiles/files_from.txt", u"w") as f:
            f.write(u"\n".join(self.testfiles_numbers))
        self.backup(u"full", u"testfiles/select2",
                    options=[u"--files-from", u"testfiles/files_from.txt",
                             u"--exclude", u"testfiles/select2/2",
                             u"--exclude", u"testfiles/select2/3",
                             u"--exclude", u"**.txt"])
        self.restore()
        restore_path = u"testfiles/restore_out"
        restored = self.directory_tree_to_list_of_lists(restore_path)
        self.assertEqual(restored, [[u"1", u"1.doc", u"1.py"],
                                    [u"1sub1", u"1sub2", u"1sub3"],
                                    [u"1sub1sub1", u"1sub1sub2", u"1sub1sub3"],
                                    [u"1sub2sub1", u"1sub2sub2", u"1sub2sub3"],
                                    [u"1sub3sub1", u"1sub3sub2", u"1sub3sub3"]])

    def test_files_from_with_inclusions(self):
        u""" Apply some --exclude rules to a backup fileset defined by --files-from"""
        with io.open(u"testfiles/files_from.txt", u"w") as f:
            f.write(u"\n".join(self.testfiles_numbers))
        self.backup(u"full", u"testfiles/select2",
                    options=[u"--files-from", u"testfiles/files_from.txt",
                             u"--include", u"testfiles/select2/1.*",
                             u"--include", u"**.txt",
                             u"--exclude", u"**"])
        self.restore()
        restore_path = u"testfiles/restore_out"
        restored = self.directory_tree_to_list_of_lists(restore_path)
        self.assertEqual(restored, [[u"1", u"2", u"3", u"1.doc", u"1.py"],
                                    [u"1sub1"], [u"1sub1sub1", u"1sub1sub2", u"1sub1sub3"],
                                    [u"1sub1sub1_file.txt"], [u"1sub1sub2_file.txt"], [u"1sub1sub3_file.txt"],
                                    [u"2sub1"], [u"2sub1sub1"], [u"2sub1sub1_file.txt"],
                                    [u"3sub3"], [u"3sub3sub2"], [u"3sub3sub2_file.txt"]])

    def test_files_from_multiple_filelists(self):
        u""" Use filelists for both --files-from and --include-filelist """
        with io.open(u"testfiles/files_from.txt", u"w") as f:
            f.write(u"\n".join(self.testfiles_numbers))
        with io.open(u"testfiles/include.txt", u"w") as f:
            f.write(u"testfiles/select2/1/1sub2\n"
                    u"testfiles/select2/1/1sub3\n"
                    u"testfiles/select2/2/2sub2\n"
                    u"testfiles/select2/2/2sub3\n"
                    u"testfiles/select2/3/3sub1\n"
                    u"testfiles/select2/3/3sub2\n"
                    u"testfiles/select2/trailing_space*")  # last include does nothing due to --files-from
        self.backup(u"full", u"testfiles/select2",
                    options=[u"--files-from", u"testfiles/files_from.txt",
                             u"--include-filelist", u"testfiles/include.txt",
                             u"--exclude", u"**"])
        self.restore()
        restore_path = u"testfiles/restore_out"
        restored = self.directory_tree_to_list_of_lists(restore_path)
        self.assertEqual(restored, [[u"1", u"2", u"3"],
                                    [u"1sub2", u"1sub3"],
                                    [u"1sub2sub1", u"1sub2sub2", u"1sub2sub3"],
                                    [u"1sub3sub1", u"1sub3sub2", u"1sub3sub3"],
                                    [u"2sub2", u"2sub3"],
                                    [u"2sub2sub1", u"2sub2sub2", u"2sub2sub3"],
                                    [u"2sub3sub1", u"2sub3sub2", u"2sub3sub3"],
                                    [u"3sub1", u"3sub2"],
                                    [u"3sub1sub1", u"3sub1sub2", u"3sub1sub3"],
                                    [u"3sub2sub1", u"3sub2sub2", u"3sub2sub3"]])

    def test_files_from_null_separator(self):
        u""" Using nulls to separate --files-from """
        with io.open(u"testfiles/files_from.txt", u"w") as f:
            f.write(u"\0".join(self.testfiles_numbers))
        self.backup(u"full", u"testfiles/select2",
                    options=[u"--null-separator",
                             u"--files-from", u"testfiles/files_from.txt",
                             u"--include", u"testfiles/select2/1/1sub2",
                             u"--include", u"testfiles/select2/1/1sub3",
                             u"--include", u"testfiles/select2/2/2sub2",
                             u"--include", u"testfiles/select2/2/2sub3",
                             u"--include", u"testfiles/select2/3/3sub1",
                             u"--include", u"testfiles/select2/3/3sub2",
                             u"--exclude", u"**"])
        self.restore()
        restore_path = u"testfiles/restore_out"
        restored = self.directory_tree_to_list_of_lists(restore_path)
        self.assertEqual(restored, [[u"1", u"2", u"3"],
                                    [u"1sub2", u"1sub3"],
                                    [u"1sub2sub1", u"1sub2sub2", u"1sub2sub3"],
                                    [u"1sub3sub1", u"1sub3sub2", u"1sub3sub3"],
                                    [u"2sub2", u"2sub3"],
                                    [u"2sub2sub1", u"2sub2sub2", u"2sub2sub3"],
                                    [u"2sub3sub1", u"2sub3sub2", u"2sub3sub3"],
                                    [u"3sub1", u"3sub2"],
                                    [u"3sub1sub1", u"3sub1sub2", u"3sub1sub3"],
                                    [u"3sub2sub1", u"3sub2sub2", u"3sub2sub3"]])


class TestIncludeExcludeOptions(IncludeExcludeFunctionalTest):
    u""" This tests the behaviour of the duplicity binary when the include/exclude options are passed directly """

    def test_include_exclude_basic(self):
        u""" Test --include and --exclude work in the basic case """
        self.backup(u"full", u"testfiles/select2",
                    options=[u"--include", u"testfiles/select2/3/3sub3/3sub3sub2/3sub3sub2_file.txt",
                             u"--exclude", u"testfiles/select2/3/3sub3/3sub3sub2",
                             u"--include", u"testfiles/select2/3/3sub2/3sub2sub2",
                             u"--include", u"testfiles/select2/3/3sub3",
                             u"--exclude", u"testfiles/select2/3/3sub1",
                             u"--exclude", u"testfiles/select2/2/2sub1/2sub1sub3",
                             u"--exclude", u"testfiles/select2/2/2sub1/2sub1sub2",
                             u"--include", u"testfiles/select2/2/2sub1",
                             u"--exclude", u"testfiles/select2/1/1sub3/1sub3sub2",
                             u"--exclude", u"testfiles/select2/1/1sub3/1sub3sub1",
                             u"--exclude", u"testfiles/select2/1/1sub2/1sub2sub3",
                             u"--include", u"testfiles/select2/1/1sub2/1sub2sub1",
                             u"--exclude", u"testfiles/select2/1/1sub1/1sub1sub3/1sub1sub3_file.txt",
                             u"--exclude", u"testfiles/select2/1/1sub1/1sub1sub2",
                             u"--exclude", u"testfiles/select2/1/1sub2",
                             u"--include", u"testfiles/select2/1.py",
                             u"--include", u"testfiles/select2/3",
                             u"--include", u"testfiles/select2/1",
                             u"--exclude", u"testfiles/select2/**"])
        self.restore()
        restore_path = u"testfiles/restore_out"
        restored = self.directory_tree_to_list_of_lists(restore_path)
        self.assertEqual(restored, self.expected_restored_tree)

    def test_include_exclude_trailing_whitespace(self):
        u"""Test that folders with trailing whitespace in the names work correctly when passing as include/exclude"""
        # Note that, because this only passes items in as a list of options, this test does not test whether duplicity
        # would correctly interpret commandline options with spaces. However, bin/duplicity uses sys.argv[1:], which
        # should return a list of strings after having correctly processed quotes etc.
        self.backup(u"full", u"testfiles/select2",
                    options=[u"--include", u"testfiles/select2/trailing_space /trailing_space "
                                           u"sub2/trailing_space sub2_file.txt",
                             u"--exclude", u"testfiles/select2/trailing_space /trailing_space sub2",
                             u"--include", u"testfiles/select2/trailing_space ",
                             u"--include", u"testfiles/select2/3/3sub3/3sub3sub2/3sub3sub2_file.txt",
                             u"--exclude", u"testfiles/select2/3/3sub3/3sub3sub2",
                             u"--include", u"testfiles/select2/3/3sub2/3sub2sub2",
                             u"--include", u"testfiles/select2/3/3sub3",
                             u"--exclude", u"testfiles/select2/3/3sub1",
                             u"--exclude", u"testfiles/select2/2/2sub1/2sub1sub3",
                             u"--exclude", u"testfiles/select2/2/2sub1/2sub1sub2",
                             u"--include", u"testfiles/select2/2/2sub1",
                             u"--exclude", u"testfiles/select2/1/1sub3/1sub3sub2",
                             u"--exclude", u"testfiles/select2/1/1sub3/1sub3sub1",
                             u"--exclude", u"testfiles/select2/1/1sub2/1sub2sub3",
                             u"--include", u"testfiles/select2/1/1sub2/1sub2sub1",
                             u"--exclude", u"testfiles/select2/1/1sub1/1sub1sub3/1sub1sub3_file.txt",
                             u"--exclude", u"testfiles/select2/1/1sub1/1sub1sub2",
                             u"--exclude", u"testfiles/select2/1/1sub2",
                             u"--include", u"testfiles/select2/1.py",
                             u"--include", u"testfiles/select2/3",
                             u"--include", u"testfiles/select2/1",
                             u"--exclude", u"testfiles/select2/**"])
        self.restore()
        restore_path = u"testfiles/restore_out"
        restored = self.directory_tree_to_list_of_lists(restore_path)
        self.assertEqual(restored, self.expected_restored_tree_with_trailing_space)


class TestIncludeExcludeFilterModes(IncludeExcludeFunctionalTest):
    u"""
    Direct use of --include/--exclude with --filter-* mode switches used.
    """

    def test_error_on_redundant_filter_option(self):
        u""" Test for explicit specification of default filter options _only_.
        """
        with self.assertRaises(CmdError) as context:
            self.backup(u"full", u"testfiles/select2",
                        options=[u"--filter-globbing", u"--filter-strictcase",
                                 u"--include", u"testfiles/dir1/fifo",
                                 u"--include", u"testfiles/dir1/symbolic_link",
                                 u"--include", u"testfiles/dir1/largefile",
                                 u"--exclude", u"testfiles/dir1"])
        self.assertEqual(context.exception.exit_status, log.ErrorCode.redundant_filter)

    def test_error_on_trailing_filter_option(self):
        u""" Test --filter-* as the last file selection option, which has no
        effect and should result in an error.
        """
        with self.assertRaises(CmdError) as context:
            self.backup(u"full", u"testfiles/select2",
                        options=[u"--include", u"testfiles/dir1/fifo",
                                 u"--include", u"testfiles/dir1/symbolic_link",
                                 u"--include", u"testfiles/dir1/largefile",
                                 u"--exclude", u"testfiles/dir1",
                                 u"--filter-literal"])
        self.assertEqual(context.exception.exit_status, log.ErrorCode.trailing_filter)

    def test_include_exclude_basic_with_modes(self):
        u""" Test --include and --exclude work in the same way as done by
        TestIncludeExcludeSelectOptions, but when --filter-* switches in a way
        which should not change the outcome (with this specific file set).
        """
        self.backup(u"full", u"testfiles/select2",
                    options=[u"--include", u"testfiles/select2/3/3sub3/3sub3sub2/3sub3sub2_file.txt",
                             u"--filter-literal",
                             u"--exclude", u"testfiles/select2/3/3sub3/3sub3sub2",
                             u"--include", u"testfiles/select2/3/3sub2/3sub2sub2",
                             u"--include", u"testfiles/select2/3/3sub3",
                             u"--exclude", u"testfiles/select2/3/3sub1",
                             u"--exclude", u"testfiles/select2/2/2sub1/2sub1sub3",
                             u"--exclude", u"testfiles/select2/2/2sub1/2sub1sub2",
                             u"--include", u"testfiles/select2/2/2sub1",
                             u"--filter-globbing",
                             u"--exclude", u"testfiles/select2/1/1sub3/1sub3sub2",
                             u"--exclude", u"testfiles/select2/1/1sub3/1sub3sub1",
                             u"--exclude", u"testfiles/select2/1/1sub2/1sub2sub3",
                             u"--include", u"testfiles/select2/1/1sub2/1sub2sub1",
                             u"--exclude", u"testfiles/select2/1/1sub1/1sub1sub3/1sub1sub3_file.txt",
                             u"--exclude", u"testfiles/select2/1/1sub1/1sub1sub2",
                             u"--exclude", u"testfiles/select2/1/1sub2",
                             u"--filter-regexp",
                             u"--include", u"testfiles/select2/1.py$",
                             u"--filter-literal",
                             u"--include", u"testfiles/select2/3",
                             u"--include", u"testfiles/select2/1",
                             u"--filter-globbing",
                             u"--exclude", u"testfiles/select2/**"])
        self.restore()
        restore_path = u"testfiles/restore_out"
        restored = self.directory_tree_to_list_of_lists(restore_path)
        self.assertEqual(restored, self.expected_restored_tree)

    def test_include_exclude_trailing_whitespace_with_modes(self):
        u"""
        Test that folders with trailing whitespace in the names work correctly
        when passing as include/exclude, specifically in literal mode.
        """
        # Note that, because this only passes items in as a list of options, this test does not test whether duplicity
        # would correctly interpret commandline options with spaces. However, bin/duplicity uses sys.argv[1:], which
        # should return a list of strings after having correctly processed quotes etc.
        self.backup(u"full", u"testfiles/select2",
                    options=[u"--filter-literal",
                             u"--include", u"testfiles/select2/trailing_space /trailing_space sub2/trailing_space "
                                           u"sub2_file.txt",
                             u"--exclude", u"testfiles/select2/trailing_space /trailing_space sub2",
                             u"--include", u"testfiles/select2/trailing_space ",
                             u"--include", u"testfiles/select2/3/3sub3/3sub3sub2/3sub3sub2_file.txt",
                             u"--exclude", u"testfiles/select2/3/3sub3/3sub3sub2",
                             u"--include", u"testfiles/select2/3/3sub2/3sub2sub2",
                             u"--include", u"testfiles/select2/3/3sub3",
                             u"--exclude", u"testfiles/select2/3/3sub1",
                             u"--exclude", u"testfiles/select2/2/2sub1/2sub1sub3",
                             u"--exclude", u"testfiles/select2/2/2sub1/2sub1sub2",
                             u"--include", u"testfiles/select2/2/2sub1",
                             u"--exclude", u"testfiles/select2/1/1sub3/1sub3sub2",
                             u"--exclude", u"testfiles/select2/1/1sub3/1sub3sub1",
                             u"--exclude", u"testfiles/select2/1/1sub2/1sub2sub3",
                             u"--include", u"testfiles/select2/1/1sub2/1sub2sub1",
                             u"--exclude", u"testfiles/select2/1/1sub1/1sub1sub3/1sub1sub3_file.txt",
                             u"--exclude", u"testfiles/select2/1/1sub1/1sub1sub2",
                             u"--exclude", u"testfiles/select2/1/1sub2",
                             u"--include", u"testfiles/select2/1.py",
                             u"--include", u"testfiles/select2/3",
                             u"--include", u"testfiles/select2/1",
                             u"--filter-globbing",
                             u"--exclude", u"testfiles/select2/**"])
        self.restore()
        restore_path = u"testfiles/restore_out"
        restored = self.directory_tree_to_list_of_lists(restore_path)
        self.assertEqual(restored, self.expected_restored_tree_with_trailing_space)

    u"""
    Test all --filter-* modes in combination, with selection patterns which
    utilise the specific capabilities of each.
    """
    # this is slightly different from TestIncludeExcludeFilterModes which use
    # filter mode switches for which they are used (mostly) to no effect, to
    # produce the already defined expected_restore_tree structure.
    def test_literal_multiple_mode_switches(self):
        self.backup(u"full", u"testfiles/select2",
                    options=[u"--include", u"testfiles/select2/**doc",
                             u"--exclude", u"testfiles/select2/1/*/*/*.txt",
                             u"--filter-literal",
                             u"--exclude", u"testfiles/select2/2/2sub1/2sub1sub1/2sub1sub1_file.txt",
                             u"--filter-regexp",
                             u"--include", u"testfiles/select2/1/1sub[13]/1sub[13]sub[123]",
                             u"--include", u"testfiles/select2/2/2sub1/2sub1sub[12]",
                             u"--filter-literal",
                             u"--include", u"testfiles/select2/trailing_space /trailing_space sub2/trailing_space "
                                           u"sub2_file.txt",
                             u"--include", u"testfiles/select2/3/3sub3/3sub3sub2/3sub3sub2_file.txt",
                             u"--filter-globbing",
                             u"--exclude", u"testfiles/select2/*"])
        self.restore()
        restore_path = u"testfiles/restore_out"
        restored = self.directory_tree_to_list_of_lists(restore_path)
        self.assertEqual(restored, [[u"1", u"2", u"3", u"trailing_space ", u"1.doc"],
                                    [u"1sub1", u"1sub3"],
                                    [u"1sub1sub1", u"1sub1sub2", u"1sub1sub3"],
                                    [u"1sub3sub1", u"1sub3sub2", u"1sub3sub3"],
                                    [u"2sub1"], [u"2sub1sub1", u"2sub1sub2"],
                                    [u"3sub3"], [u"3sub3sub2"], [u"3sub3sub2_file.txt"],
                                    [u"trailing_space sub2"],
                                    [u"trailing_space sub2_file.txt"]])

    u"""
    Same  as test_literal_multiple_mode_switches, but without case sensitivity
    as specified using the existing ignorecase: prefix, at least for those file
    selection options support it.
    """
    def test_literal_multiple_mode_switches_with_ignorecase_prefix(self):
        self.backup(u"full", u"testfiles/select2",
                    options=[u"--include", u"ignorecase:tEStfiles/sElect2/**doc",
                             u"--exclude", u"ignorecase:testfIles/seLEct2/1/*/*/*.txt",
                             u"--filter-literal",
                             u"--exclude", u"testfiles/select2/2/2sub1/2sub1sub1/2sub1sub1_file.txt",
                             u"--filter-regexp",
                             u"--include", u"testfiles/select2/1/1sub[13]/1sub[13]sub[123]",
                             u"--include", u"testfiles/select2/2/2sub1/2sub1sub[12]",
                             u"--filter-literal",
                             u"--include", u"testfiles/select2/trailing_space /trailing_space "
                                           u"sub2/trailing_space sub2_file.txt",
                             u"--include", u"testfiles/select2/3/3sub3/3sub3sub2/3sub3sub2_file.txt",
                             u"--filter-globbing",
                             u"--exclude", u"ignorecase:TestFiles/SELECT2/*"])
        self.restore()
        restore_path = u"testfiles/restore_out"
        restored = self.directory_tree_to_list_of_lists(restore_path)
        self.assertEqual(restored, [[u"1", u"2", u"3", u"trailing_space ", u"1.doc"],
                                    [u"1sub1", u"1sub3"],
                                    [u"1sub1sub1", u"1sub1sub2", u"1sub1sub3"],
                                    [u"1sub3sub1", u"1sub3sub2", u"1sub3sub3"],
                                    [u"2sub1"], [u"2sub1sub1", u"2sub1sub2"],
                                    [u"3sub3"], [u"3sub3sub2"], [u"3sub3sub2_file.txt"],
                                    [u"trailing_space sub2"],
                                    [u"trailing_space sub2_file.txt"]])

    u"""
    Same as test_literal_multiple_mode_switches(), but without case sensitivity
    for *all* selection options using the --filter-ignorecase command line option.
    """
    def test_literal_multiple_mode_switches_with_filter_ignorecase(self):
        self.backup(u"full", u"testfiles/select2",
                    options=[u"--filter-ignorecase",
                             u"--include", u"tEStfiles/sElect2/**doc",
                             u"--exclude", u"testfIles/seLEct2/1/*/*/*.txt",
                             u"--filter-literal",
                             u"--exclude", u"Testfiles/select2/2/2SUB1/2sub1sUb1/2sUb1sUb1_file.txt",
                             u"--filter-regexp",
                             u"--include", u"testfiles/select2/1/1sub[13]/1sub[13]sub[123]",
                             u"--include", u"testfiles/select2/2/2sub1/2SUB1SUB[12]",
                             u"--filter-literal",
                             u"--include", u"TESTFILES/select2/trailing_space /trailing_space sub2/trailing_space "
                                           u"sub2_file.txt",
                             u"--include", u"TestFiles/select2/3/3sub3/3sub3sub2/3sub3sub2_file.txt",
                             u"--filter-globbing",
                             u"--filter-strictcase",
                             u"--exclude", u"testfiles/select2/*"])
        self.restore()
        restore_path = u"testfiles/restore_out"
        restored = self.directory_tree_to_list_of_lists(restore_path)
        self.assertEqual(restored, [[u"1", u"2", u"3", u"trailing_space ", u"1.doc"],
                                    [u"1sub1", u"1sub3"],
                                    [u"1sub1sub1", u"1sub1sub2", u"1sub1sub3"],
                                    [u"1sub3sub1", u"1sub3sub2", u"1sub3sub3"],
                                    [u"2sub1"], [u"2sub1sub1", u"2sub1sub2"],
                                    [u"3sub3"], [u"3sub3sub2"], [u"3sub3sub2_file.txt"],
                                    [u"trailing_space sub2"],
                                    [u"trailing_space sub2_file.txt"]])

    def test_literal_special_files(self):
        u""" No reason this shouldn't work as the differences in file selection
        code for literal-vs-regex-vs-globs is dealing only with strings. this is
        included for completeness and against the remote future possibility that
        those different filter implementations one day touch filesystem meta data
        and pick up interactions with special file types or attributes...
        """
        self.backup(u"full", u"testfiles/dir1/",
                    options=[u"--filter-literal",
                             u"--include", u"testfiles/dir1/fifo",
                             u"--include", u"testfiles/dir1/symbolic_link",
                             u"--include", u"testfiles/dir1/largefile",
                             u"--exclude", u"testfiles/dir1"])
        self.restore()
        restore_path = u"testfiles/restore_out"
        restored = self.directory_tree_to_list_of_lists(restore_path)
        self.assertEqual(restored, [[u"fifo", u"largefile", u"symbolic_link"]])


class TestIncludeSpecialGlobChars(IncludeExcludeFunctionalTest):
    u"""
    Use of literal selection functions to match shell globbing characters
    """

    def test_literal_special_shell_chars(self):
        u""" Selecting files using literal selection functions which would have
        different interactions if interpreted as shell globs, e.g. '[01]' which
        will not match the same as a glob, or 0?1 which would also match 0*1 in
        the same folder (where ? and * appear literally in the filenames).
        """
        self.backup(u"full", u"testfiles/shell_glob_chars",
                    options=[u"--filter-literal",
                             u"--include", u"testfiles/shell_glob_chars/0?1/1?1/0?1sub1?1_file.txt",
                             u"--exclude", u"testfiles/shell_glob_chars/0?1",
                             u"--exclude", u"testfiles/shell_glob_chars/0*1/2*2/0*1sub2*2_file.txt",
                             u"--exclude", u"testfiles/shell_glob_chars/[01]/3?3/[01]sub3?3_file.txt"])
        self.restore()
        restore_path = u"testfiles/restore_out"
        restored = self.directory_tree_to_list_of_lists(restore_path)
        self.assertEqual(restored, [[u"0*1", u"0?1", u"[01]"],
                                    [u"2*2", u"2?2", u"[02]"], [u"0*1sub2?2_file.txt"], [u"0*1sub[02]_file.txt"],
                                    [u"1?1"], [u"0?1sub1?1_file.txt"],
                                    [u"3*3", u"3?3", u"[03]"], [u"[01]sub3*3_file.txt"], [u"[01]sub[03]_file.txt"]])

    def test_globbing_special_shell_chars(self):
        u""" Selecting files using both literal and globbing selection functions
        on a fileset which contains literal shell characters
        """
        self.backup(u"full", u"testfiles/shell_glob_chars",
                    options=[u"--filter-literal",
                             u"--include", u"testfiles/shell_glob_chars/0*1/2*2/0*1sub2*2_file.txt",
                             u"--filter-globbing",
                             u"--exclude", u"testfiles/shell_glob_chars/0*1"])
        self.restore()
        restore_path = u"testfiles/restore_out"
        restored = self.directory_tree_to_list_of_lists(restore_path)
        self.assertEqual(restored, [[u"0*1", u"[01]"],
                                    [u"2*2"], [u"0*1sub2*2_file.txt"],
                                    [u"3*3", u"3?3", u"[03]"], [u"[01]sub3*3_file.txt"], [u"[01]sub3?3_file.txt"],
                                    [u"[01]sub[03]_file.txt"]])

    def test_filelist_special_shell_chars(self):
        u""" This test is the same as test_literal_special_shell_chars() except that
        an include file-list is used instead.
        """
        with io.open(u"testfiles/include.txt", u"w") as f:
            f.write(u"testfiles/shell_glob_chars/0?1/1?1/0?1sub1?1_file.txt\n"
                    u"- testfiles/shell_glob_chars/0?1\n"
                    u"- testfiles/shell_glob_chars/0*1/2*2/0*1sub2*2_file.txt\n"
                    u"- testfiles/shell_glob_chars/[01]/3?3/[01]sub3?3_file.txt\n")

        self.backup(u"full", u"testfiles/shell_glob_chars",
                    options=[u"--filter-literal", u"--include-filelist=testfiles/include.txt"])
        self.restore()
        restore_path = u"testfiles/restore_out"
        restored = self.directory_tree_to_list_of_lists(restore_path)
        self.assertEqual(restored, [[u"0*1", u"0?1", u"[01]"],
                                    [u"2*2", u"2?2", u"[02]"], [u"0*1sub2?2_file.txt"], [u"0*1sub[02]_file.txt"],
                                    [u"1?1"], [u"0?1sub1?1_file.txt"],
                                    [u"3*3", u"3?3", u"[03]"], [u"[01]sub3*3_file.txt"], [u"[01]sub[03]_file.txt"]])


class TestExcludeFilelistTest(IncludeExcludeFunctionalTest):
    u"""
    Test --exclude-filelist using duplicity binary.
    """

    def test_exclude_filelist(self):
        u"""Test that exclude filelist works in the basic case """
        # As this is an exclude filelist any lines with no +/- modifier should be treated as if they have a -.
        # Create a filelist
        with io.open(u"testfiles/exclude.txt", u"w") as f:
            f.write(u"+ testfiles/select2/3/3sub3/3sub3sub2/3sub3sub2_file.txt\n"
                    u"testfiles/select2/3/3sub3/3sub3sub2\n"
                    u"+ testfiles/select2/3/3sub2/3sub2sub2\n"
                    u"+ testfiles/select2/3/3sub3\n"
                    u"- testfiles/select2/3/3sub1\n"  # - added to ensure it makes no difference
                    u"testfiles/select2/2/2sub1/2sub1sub3\n"
                    u"testfiles/select2/2/2sub1/2sub1sub2\n"
                    u"+ testfiles/select2/2/2sub1\n"
                    u"testfiles/select2/1/1sub3/1sub3sub2\n"
                    u"testfiles/select2/1/1sub3/1sub3sub1\n"
                    u"testfiles/select2/1/1sub2/1sub2sub3\n"
                    u"+ testfiles/select2/1/1sub2/1sub2sub1\n"
                    u"testfiles/select2/1/1sub1/1sub1sub3/1sub1sub3_file.txt\n"
                    u"testfiles/select2/1/1sub1/1sub1sub2\n"
                    u"- testfiles/select2/1/1sub2\n"  # - added to ensure it makes no difference
                    u"+ testfiles/select2/1.py\n"
                    u"+ testfiles/select2/3\n"
                    u"+ testfiles/select2/1\n"
                    u"testfiles/select2/**")
        self.backup(u"full", u"testfiles/select2", options=[u"--exclude-filelist=testfiles/exclude.txt"])
        self.restore()
        restore_path = u"testfiles/restore_out"
        restored = self.directory_tree_to_list_of_lists(restore_path)
        self.assertEqual(restored, self.expected_restored_tree)

    def test_exclude_filelist_combined_imperfections(self):
        u"""Test that exclude filelist works with imperfections in the input file"""
        # This is a combined test for speed reasons. The individual imperfections are tested as unittests in
        # unit/test_selection.
        # Imperfections tested are;
        # * Leading space/spaces before the modifier
        # * Trailing space/spaces after the filename (but before the newline)
        # * Blank lines (newline character only)
        # * Line only containing spaces
        # * Full-line comments with # as the first character and with leading/trailing spaces
        # * Unnecessarily quoted filenames with/without modifier (both " and ')
        # Create a filelist
        with io.open(u"testfiles/exclude.txt", u"w") as f:
            f.write(u"+ testfiles/select2/3/3sub3/3sub3sub2/3sub3sub2_file.txt\n"
                    u"testfiles/select2/3/3sub3/3sub3sub2\n"
                    u"+ testfiles/select2/3/3sub2/3sub2sub2\n"
                    u" + testfiles/select2/3/3sub3\n"  # Note leading space added here
                    u"- testfiles/select2/3/3sub1\n"
                    u"  testfiles/select2/2/2sub1/2sub1sub3\n"  # Note leading spaces added here
                    u"\n"
                    u"testfiles/select2/2/2sub1/2sub1sub2\n"
                    u" + testfiles/select2/2/2sub1 \n"  # Note added trailing/leading space here
                    u'- "testfiles/select2/1/1sub3/1sub3sub2"\n'  # Unnecessary quotes
                    u"# Testing a full-line comment\n"
                    u"'testfiles/select2/1/1sub3/1sub3sub1'  \n"  # Note added spaces and quotes here
                    u"testfiles/select2/1/1sub2/1sub2sub3\n"
                    u"    \n"
                    u"+ testfiles/select2/1/1sub2/1sub2sub1\n"
                    u"- testfiles/select2/1/1sub1/1sub1sub3/1sub1sub3_file.txt\n"
                    u"testfiles/select2/1/1sub1/1sub1sub2\n"
                    u"     # Testing a full-line comment with leading and trailing spaces     \n"
                    u"testfiles/select2/1/1sub2  \n"  # Note added spaces here
                    u"+ testfiles/select2/1.py\n"
                    u"+ testfiles/select2/3 \n"  # Note added space here
                    u"+ testfiles/select2/1\n"
                    u"- testfiles/select2/**")
        self.backup(u"full", u"testfiles/select2", options=[u"--exclude-filelist=testfiles/exclude.txt"])
        self.restore()
        restore_path = u"testfiles/restore_out"
        restored = self.directory_tree_to_list_of_lists(restore_path)
        self.assertEqual(restored, self.expected_restored_tree)

    def test_exclude_filelist_trailing_whitespace_folders_work_with_quotes(self):
        u"""Test that folders with trailing whitespace in the names work correctly if they are enclosed in quotes"""
        # Create a filelist
        with io.open(u"testfiles/exclude.txt", u"w") as f:
            f.write(u'+ "testfiles/select2/trailing_space /trailing_space sub2/trailing_space sub2_file.txt"\n'  # New
                    u"- 'testfiles/select2/trailing_space /trailing_space sub2'\n"  # New
                    u'+ "testfiles/select2/trailing_space "\n'  # New
                    u"+ testfiles/select2/3/3sub3/3sub3sub2/3sub3sub2_file.txt\n"
                    u"testfiles/select2/3/3sub3/3sub3sub2\n"
                    u"+ testfiles/select2/3/3sub2/3sub2sub2\n"
                    u"+ testfiles/select2/3/3sub3\n"
                    u"- testfiles/select2/3/3sub1\n"
                    u"testfiles/select2/2/2sub1/2sub1sub3\n"
                    u"testfiles/select2/2/2sub1/2sub1sub2\n"
                    u"+ testfiles/select2/2/2sub1\n"
                    u"testfiles/select2/1/1sub3/1sub3sub2\n"
                    u"testfiles/select2/1/1sub3/1sub3sub1\n"
                    u"testfiles/select2/1/1sub2/1sub2sub3\n"
                    u"+ testfiles/select2/1/1sub2/1sub2sub1\n"
                    u"testfiles/select2/1/1sub1/1sub1sub3/1sub1sub3_file.txt\n"
                    u"testfiles/select2/1/1sub1/1sub1sub2\n"
                    u"- testfiles/select2/1/1sub2\n"
                    u"+ testfiles/select2/1.py\n"
                    u"+ testfiles/select2/3\n"
                    u"+ testfiles/select2/1\n"
                    u"testfiles/select2/**")
        self.backup(u"full", u"testfiles/select2", options=[u"--exclude-filelist=testfiles/exclude.txt"])
        self.restore()
        restore_path = u"testfiles/restore_out"
        restored = self.directory_tree_to_list_of_lists(restore_path)
        self.assertEqual(restored, self.expected_restored_tree_with_trailing_space)

    def test_exclude_filelist_progress_option(self):
        u"""Test that exclude filelist is unaffected by the --progress option"""
        # Regression test for Bug #1264744 (https://bugs.launchpad.net/duplicity/+bug/1264744)
        # Create a filelist identical to that used in test_exclude_filelist
        with io.open(u"testfiles/exclude.txt", u"w") as f:
            f.write(u"+ testfiles/select2/3/3sub3/3sub3sub2/3sub3sub2_file.txt\n"
                    u"testfiles/select2/3/3sub3/3sub3sub2\n"
                    u"+ testfiles/select2/3/3sub2/3sub2sub2\n"
                    u"+ testfiles/select2/3/3sub3\n"
                    u"- testfiles/select2/3/3sub1\n"  # - added to ensure it makes no difference
                    u"testfiles/select2/2/2sub1/2sub1sub3\n"
                    u"testfiles/select2/2/2sub1/2sub1sub2\n"
                    u"+ testfiles/select2/2/2sub1\n"
                    u"testfiles/select2/1/1sub3/1sub3sub2\n"
                    u"testfiles/select2/1/1sub3/1sub3sub1\n"
                    u"testfiles/select2/1/1sub2/1sub2sub3\n"
                    u"+ testfiles/select2/1/1sub2/1sub2sub1\n"
                    u"testfiles/select2/1/1sub1/1sub1sub3/1sub1sub3_file.txt\n"
                    u"testfiles/select2/1/1sub1/1sub1sub2\n"
                    u"- testfiles/select2/1/1sub2\n"  # - added to ensure it makes no difference
                    u"+ testfiles/select2/1.py\n"
                    u"+ testfiles/select2/3\n"
                    u"+ testfiles/select2/1\n"
                    u"testfiles/select2/**")

        # Backup the files exactly as in test_exclude_filelist, but with the --progress option
        self.backup(u"full", u"testfiles/select2", options=[u"--exclude-filelist=testfiles/exclude.txt",
                                                            u"--progress"])
        self.restore()
        restore_path = u"testfiles/restore_out"
        restored = self.directory_tree_to_list_of_lists(restore_path)
        # The restored files should match those restored in test_exclude_filelist
        self.assertEqual(restored, self.expected_restored_tree)


class TestIncludeFilelistTest(IncludeExcludeFunctionalTest):
    u"""
    Test --include-filelist using duplicity binary.
    """

    def test_include_filelist(self):
        u"""Test that include filelist works in the basic case"""
        # See test_exclude_filelist above for explanation of what is expected. As this is an include filelist
        # any lines with no +/- modifier should be treated as if they have a +.
        # Create a filelist
        with io.open(u"testfiles/include.txt", u"w") as f:
            f.write(u"testfiles/select2/3/3sub3/3sub3sub2/3sub3sub2_file.txt\n"
                    u"- testfiles/select2/3/3sub3/3sub3sub2\n"
                    u"testfiles/select2/3/3sub2/3sub2sub2\n"
                    u"+ testfiles/select2/3/3sub3\n"  # + added to ensure it makes no difference
                    u"- testfiles/select2/3/3sub1\n"
                    u"- testfiles/select2/2/2sub1/2sub1sub3\n"
                    u"- testfiles/select2/2/2sub1/2sub1sub2\n"
                    u"testfiles/select2/2/2sub1\n"
                    u"- testfiles/select2/1/1sub3/1sub3sub2\n"
                    u"- testfiles/select2/1/1sub3/1sub3sub1\n"
                    u"- testfiles/select2/1/1sub2/1sub2sub3\n"
                    u"+ testfiles/select2/1/1sub2/1sub2sub1\n"  # + added to ensure it makes no difference
                    u"- testfiles/select2/1/1sub1/1sub1sub3/1sub1sub3_file.txt\n"
                    u"- testfiles/select2/1/1sub1/1sub1sub2\n"
                    u"- testfiles/select2/1/1sub2\n"
                    u"testfiles/select2/1.py\n"
                    u"testfiles/select2/3\n"
                    u"testfiles/select2/1\n"
                    u"- testfiles/select2/**")
        self.backup(u"full", u"testfiles/select2", options=[u"--include-filelist=testfiles/include.txt"])
        self.restore()
        restore_path = u"testfiles/restore_out"
        restored = self.directory_tree_to_list_of_lists(restore_path)
        self.assertEqual(restored, self.expected_restored_tree)

    def test_include_filelist_combined_imperfections(self):
        u"""Test that include filelist works with imperfections in the input file"""
        # This is a combined test for speed reasons. The individual imperfections are tested as unittests in
        # unit/test_selection.
        # Imperfections tested are;
        # * Leading space/spaces before the modifier
        # * Trailing space/spaces after the filename (but before the newline)
        # * Blank lines (newline character only)
        # * Line only containing spaces
        # * Full-line comments with # as the first character and with leading/trailing spaces
        # * Unnecessarily quoted filenames with/without modifier  (both " and ')
        # Create a filelist
        with io.open(u"testfiles/include.txt", u"w") as f:
            f.write(u"testfiles/select2/3/3sub3/3sub3sub2/3sub3sub2_file.txt\n"
                    u"- testfiles/select2/3/3sub3/3sub3sub2\n"
                    u'"testfiles/select2/3/3sub2/3sub2sub2"\n'
                    u"  + testfiles/select2/3/3sub3\n"  # + added to ensure it makes no difference
                    u"- testfiles/select2/3/3sub1\n"
                    u"- testfiles/select2/2/2sub1/2sub1sub3\n"
                    u' - "testfiles/select2/2/2sub1/2sub1sub2"\n'
                    u"testfiles/select2/2/2sub1  \n"
                    u"\n"
                    u"- testfiles/select2/1/1sub3/1sub3sub2\n"
                    u"- testfiles/select2/1/1sub3/1sub3sub1 \n"
                    u"- 'testfiles/select2/1/1sub2/1sub2sub3'\n"
                    u"             \n"
                    u" + testfiles/select2/1/1sub2/1sub2sub1 \n"  # + added to ensure it makes no difference
                    u"- testfiles/select2/1/1sub1/1sub1sub3/1sub1sub3_file.txt\n"
                    u"  - testfiles/select2/1/1sub1/1sub1sub2  \n"
                    u"# Testing full-line comment\n"
                    u"- testfiles/select2/1/1sub2\n"
                    u"'testfiles/select2/1.py'\n"
                    u"testfiles/select2/3\n"
                    u"        #  Testing another full-line comment      \n"
                    u"testfiles/select2/1\n"
                    u"- testfiles/select2/**")
        self.backup(u"full", u"testfiles/select2", options=[u"--include-filelist=testfiles/include.txt"])
        self.restore()
        restore_path = u"testfiles/restore_out"
        restored = self.directory_tree_to_list_of_lists(restore_path)
        self.assertEqual(restored, self.expected_restored_tree)

    def test_include_filelist_workaround_combined_imperfections_no_wildcards(self):
        u"""Test that include filelist works with imperfections in the input file"""
        # This is a modified version of test_include_filelist that passes, despite Bug #1408411
        # It is still a valid test, it just does not test as many selection features as the above.
        # This is a combined test for speed reasons. The individual imperfections are tested as unittests in
        # unit/test_selection.
        # Imperfections tested are;
        # * Leading space/spaces before the modifier
        # * Trailing space/spaces after the filename (but before the newline)
        # * Blank lines (newline character only)
        # * Line only containing spaces
        # * Full-line comments with # as the first character and with leading/trailing spaces
        # * Unnecessarily quoted filenames with/without modifier  (both " and ')
        # Create a filelist
        with io.open(u"testfiles/include.txt", u"w") as f:
            f.write(u"testfiles/select2/3/3sub3/3sub3sub2/3sub3sub2_file.txt\n"
                    u"testfiles/select2/3/3sub2/3sub2sub2 \n"
                    u"  + testfiles/select2/3/3sub3\n"  # + added to ensure it makes no difference
                    u" - testfiles/select2/3/3sub1  \n"
                    u"- testfiles/select2/2/2sub1/2sub1sub3\n"
                    u"- testfiles/select2/2/2sub1/2sub1sub2\n"
                    u'"testfiles/select2/2/2sub1"\n'
                    u"   - testfiles/select2/2/2sub3 \n"  # Added because of Bug #1408411
                    u"- testfiles/select2/2/2sub2\n"  # Added because of Bug #1408411
                    u"- 'testfiles/select2/1/1sub3/1sub3sub2'\n"
                    u"\n"
                    u"- testfiles/select2/1/1sub3/1sub3sub1\n"
                    u"- testfiles/select2/1/1sub2/1sub2sub3\n"
                    u'- "testfiles/select2/1/1sub2/1sub2sub2"\n'  # Added because of Bug #1408411
                    u"# This is a full-line comment\n"
                    u"+ testfiles/select2/1/1sub2/1sub2sub1  \n"  # + added to ensure it makes no difference
                    u"- testfiles/select2/1/1sub1/1sub1sub3/1sub1sub3_file.txt\n"
                    u"          \n"
                    u"- testfiles/select2/1/1sub1/1sub1sub2\n"
                    #  "- testfiles/select2/1/1sub2\n"  # Commented out because of Bug #1408411
                    u"'testfiles/select2/1.py'\n"
                    u"       # This is another full-line comment, with spaces     \n"
                    u"testfiles/select2/3\n"
                    #  "- testfiles/select2/2\n" # Commented out because of Bug #1408411
                    u"testfiles/select2/1\n"
                    u'- "testfiles/select2/trailing_space "\n'  # es instead of ea as no wildcard - **
                    u"- testfiles/select2/1.doc")  # es instead of ea as no wildcard - **
        self.backup(u"full", u"testfiles/select2", options=[u"--include-filelist=testfiles/include.txt"])
        self.restore()
        restore_path = u"testfiles/restore_out"
        restored = self.directory_tree_to_list_of_lists(restore_path)
        self.assertEqual(restored, self.expected_restored_tree)


class TestIncludeExcludedForContents(IncludeExcludeFunctionalTest):
    u""" Test to check that folders that are excluded are included if they contain includes of higher priority.
     Exhibits the issue reported in Bug #1408411 (https://bugs.launchpad.net/duplicity/+bug/1408411). """

    def write_filelist(self, filelist_name):
        u"""Used by the below tests to write the filelist"""
        assert filelist_name is not None
        with io.open(filelist_name, u"w") as f:
            f.write(u"+ testfiles/select/1/2/1\n"
                    u"- testfiles/select/1/2\n"
                    u"- testfiles/select/1/1\n"
                    u"- testfiles/select/1/3")

    def restore_and_check(self):
        u"""Restores the backup and compares to what was expected (based on the filelist in write_filelist)"""
        self.restore()
        restore_path = u"testfiles/restore_out"
        restored = self.directory_tree_to_list_of_lists(restore_path)
        self.assertEqual(restored, [[u"2"], [u"1"]])

    def test_commandline_include_exclude(self):
        u"""test an excluded folder is included for included contents when using commandline includes and excludes"""
        self.backup(u"full", u"testfiles/select/1",
                    options=[u"--include", u"testfiles/select/1/2/1",
                             u"--exclude", u"testfiles/select/1/2",
                             u"--exclude", u"testfiles/select/1/1",
                             u"--exclude", u"testfiles/select/1/3"])
        self.restore_and_check()

    def test_include_filelist(self):
        u"""test an excluded folder is included for included contents with an include-filelist (non-globbing) """
        # Regression test for Bug #1408411 (https://bugs.launchpad.net/duplicity/+bug/1408411)
        self.write_filelist(u"testfiles/include.txt")
        self.backup(u"full", u"testfiles/select/1", options=[u"--include-filelist=testfiles/include.txt"])
        self.restore_and_check()

    def test_exclude_filelist(self):
        u"""test an excluded folder is included for included contents with an exclude-filelist  (non-globbing) """
        # Regression test for Bug #1408411 (https://bugs.launchpad.net/duplicity/+bug/1408411)
        self.write_filelist(u"testfiles/exclude.txt")
        self.backup(u"full", u"testfiles/select/1", options=[u"--exclude-filelist=testfiles/exclude.txt"])
        self.restore_and_check()


class TestAsterisks(IncludeExcludeFunctionalTest):
    u""" Test to check that asterisks work as expected
     Exhibits the issue reported in Bug #884371 (https://bugs.launchpad.net/duplicity/+bug/884371).
     See the unit tests for more granularity on the issue."""

    def restore_and_check(self):
        u"""Restores the backup and compares to what is expected."""
        self.restore()
        restore_path = u"testfiles/restore_out"
        restored = self.directory_tree_to_list_of_lists(restore_path)
        self.assertEqual(restored, [[u"2"], [u"1"]])

    def test_exclude_filelist_asterisks_none(self):
        u"""Basic exclude filelist."""
        with io.open(u"testfiles/filelist.txt", u"w") as f:
            f.write(u"+ testfiles/select/1/2/1\n"
                    u"- testfiles/select/1/2\n"
                    u"- testfiles/select/1/1\n"
                    u"- testfiles/select/1/3")
        self.backup(u"full", u"testfiles/select/1", options=[u"--exclude-filelist=testfiles/filelist.txt"])
        self.restore_and_check()

    def test_exclude_filelist_asterisks_single(self):
        u"""Exclude filelist with asterisks replacing folders."""
        # Regression test for Bug #884371 (https://bugs.launchpad.net/duplicity/+bug/884371)
        with io.open(u"testfiles/filelist.txt", u"w") as f:
            f.write(u"+ */select/1/2/1\n"
                    u"- */select/1/2\n"
                    u"- testfiles/*/1/1\n"
                    u"- */*/1/3")
        self.backup(u"full", u"testfiles/select/1", options=[u"--exclude-filelist=testfiles/filelist.txt"])
        self.restore_and_check()

    def test_exclude_filelist_asterisks_double_asterisks(self):
        u"""Exclude filelist with double asterisks replacing folders."""
        # Regression test for Bug #884371 (https://bugs.launchpad.net/duplicity/+bug/884371)
        with io.open(u"testfiles/filelist.txt", u"w") as f:
            f.write(u"+ **/1/2/1\n"
                    u"- **/1/2\n"
                    u"- **/select/1/1\n"
                    u"- testfiles/select/1/3")
        self.backup(u"full", u"testfiles/select/1", options=[u"--exclude-filelist=testfiles/filelist.txt"])
        self.restore_and_check()

    def test_commandline_asterisks_single_excludes_only(self):
        u"""test_commandline_include_exclude with single asterisks on exclude lines."""
        self.backup(u"full", u"testfiles/select/1",
                    options=[u"--include", u"testfiles/select/1/2/1",
                             u"--exclude", u"testfiles/*/1/2",
                             u"--exclude", u"*/select/1/1",
                             u"--exclude", u"*/select/1/3"])
        self.restore_and_check()

    def test_commandline_asterisks_single_both(self):
        u"""test_commandline_include_exclude with single asterisks on both exclude and include lines."""
        # Regression test for Bug #884371 (https://bugs.launchpad.net/duplicity/+bug/884371)
        self.backup(u"full", u"testfiles/select/1",
                    options=[u"--include", u"*/select/1/2/1",
                             u"--exclude", u"testfiles/*/1/2",
                             u"--exclude", u"*/select/1/1",
                             u"--exclude", u"*/select/1/3"])
        self.restore_and_check()

    def test_commandline_asterisks_double_exclude_only(self):
        u"""test_commandline_include_exclude with double asterisks on exclude lines."""
        self.backup(u"full", u"testfiles/select/1",
                    options=[u"--include", u"testfiles/select/1/2/1",
                             u"--exclude", u"**/1/2",
                             u"--exclude", u"**/1/1",
                             u"--exclude", u"**/1/3"])
        self.restore_and_check()

    def test_commandline_asterisks_double_both(self):
        u"""test_commandline_include_exclude with double asterisks on both exclude and include lines."""
        # Regression test for Bug #884371 (https://bugs.launchpad.net/duplicity/+bug/884371)
        self.backup(u"full", u"testfiles/select/1",
                    options=[u"--include", u"**/1/2/1",
                             u"--exclude", u"**/1/2",
                             u"--exclude", u"**/1/1",
                             u"--exclude", u"**/1/3"])
        self.restore_and_check()

    def test_single_and_double_asterisks_includes_excludes(self):
        u"""This compares a backup using --includes/--excludes with a single and double *."""
        self.backup(u"full", u"testfiles/",
                    options=[u"--include", u"testfiles/select2/*",
                             u"--exclude", u"testfiles/select"])
        self.restore()
        restore_path = u"testfiles/restore_out"
        restored = self.directory_tree_to_list_of_lists(restore_path + u"/select2")
        self.backup(u"full", u"testfiles/",
                    options=[u"--include", u"testfiles/select2/**",
                             u"--exclude", u"testfiles/select"])
        self.restore()
        restore_path = u"testfiles/restore_out"
        restored2 = self.directory_tree_to_list_of_lists(restore_path + u"/select2")
        self.assertEqual(restored, restored2)


class TestTrailingSlash(IncludeExcludeFunctionalTest):
    u""" Test to check that a trailing slash works as expected
     Exhibits the issue reported in Bug #932482 (https://bugs.launchpad.net/duplicity/+bug/932482)."""

    def restore_and_check(self):
        u"""Restores the backup and compares to what is expected."""
        self.restore()
        restore_path = u"testfiles/restore_out"
        restored = self.directory_tree_to_list_of_lists(restore_path)
        self.assertEqual(restored, [[u"2"], [u"1"]])

    def test_exclude_filelist_trailing_slashes(self):
        u"""test_exclude_filelist_asterisks_none with trailing slashes."""
        with io.open(u"testfiles/filelist.txt", u"w") as f:
            f.write(u"+ testfiles/select/1/2/1/\n"
                    u"- testfiles/select/1/2/\n"
                    u"- testfiles/select/1/1/\n"
                    u"- testfiles/select/1/3/")
        self.backup(u"full", u"testfiles/select/1", options=[u"--exclude-filelist=testfiles/filelist.txt"])
        self.restore_and_check()

    def test_exclude_filelist_trailing_slashes_single_wildcards_excludes(self):
        u"""test_exclude_filelist_trailing_slashes with single wildcards in excludes."""
        # Regression test for Bug #932482 (https://bugs.launchpad.net/duplicity/+bug/932482)
        with io.open(u"testfiles/filelist.txt", u"w") as f:
            f.write(u"+ testfiles/select/1/2/1/\n"
                    u"- */select/1/2/\n"
                    u"- testfiles/*/1/1/\n"
                    u"- */*/1/3/")
        self.backup(u"full", u"testfiles/select/1", options=[u"--exclude-filelist=testfiles/filelist.txt"])
        self.restore_and_check()

    def test_exclude_filelist_trailing_slashes_double_wildcards_excludes(self):
        u"""test_exclude_filelist_trailing_slashes with double wildcards in excludes."""
        # Regression test for Bug #932482 (https://bugs.launchpad.net/duplicity/+bug/932482)
        with io.open(u"testfiles/filelist.txt", u"w") as f:
            f.write(u"+ testfiles/select/1/2/1/\n"
                    u"- **/1/2/\n"
                    u"- **/1/1/\n"
                    u"- **/1/3/")
        self.backup(u"full", u"testfiles/select/1", options=[u"--exclude-filelist=testfiles/filelist.txt"])
        self.restore_and_check()

    def test_exclude_filelist_trailing_slashes_double_wildcards_excludes_2(self):
        u"""second test_exclude_filelist_trailing_slashes with double wildcards in excludes."""
        # Regression test for Bug #932482 (https://bugs.launchpad.net/duplicity/+bug/932482) and
        # Regression test for Bug #884371 (https://bugs.launchpad.net/duplicity/+bug/884371)
        with io.open(u"testfiles/filelist.txt", u"w") as f:
            f.write(u"+ **/1/2/1/\n"
                    u"- **/1/2/\n"
                    u"- **/1/1/\n"
                    u"- **/1/3/")
        self.backup(u"full", u"testfiles/select/1", options=[u"--exclude-filelist=testfiles/filelist.txt"])
        self.restore_and_check()

    def test_exclude_filelist_trailing_slashes_wildcards(self):
        u"""test_commandline_asterisks_single_excludes_only with trailing slashes."""
        # Regression test for Bug #932482 (https://bugs.launchpad.net/duplicity/+bug/932482)
        self.backup(u"full", u"testfiles/select/1",
                    options=[u"--include", u"testfiles/select/1/2/1/",
                             u"--exclude", u"testfiles/*/1/2/",
                             u"--exclude", u"*/select/1/1/",
                             u"--exclude", u"*/select/1/3/"])
        self.restore_and_check()


class TestTrailingSlash2(IncludeExcludeFunctionalTest):
    u""" This tests the behaviour of globbing strings with a trailing slash"""
    # See Bug #1479545 (https://bugs.launchpad.net/duplicity/+bug/1479545)

    def test_no_trailing_slash(self):
        u""" Test that including 1.py works as expected"""
        self.backup(u"full", u"testfiles/select2",
                    options=[u"--include", u"testfiles/select2/1.py",
                             u"--exclude", u"**"])
        self.restore()
        restore_path = u"testfiles/restore_out"
        restored = self.directory_tree_to_list_of_lists(restore_path)
        self.assertEqual(restored, [[u"1.py"]])

    def test_trailing_slash(self):
        u""" Test that globs with a trailing slash only match directories"""
        # Regression test for Bug #1479545
        # (https://bugs.launchpad.net/duplicity/+bug/1479545)
        self.backup(u"full", u"testfiles/select2",
                    options=[u"--include", u"testfiles/select2/1.py/",
                             u"--exclude", u"**"])
        self.restore()
        restore_path = u"testfiles/restore_out"
        restored = self.directory_tree_to_list_of_lists(restore_path)
        self.assertEqual(restored, [])

    def test_include_files_not_subdirectories(self):
        u""" Test that a trailing slash glob followed by a * glob only matches
        files and not subdirectories"""
        self.backup(u"full", u"testfiles/select2",
                    options=[u"--exclude", u"testfiles/select2/*/",
                             u"--include", u"testfiles/select2/*",
                             u"--exclude", u"**"])
        self.restore()
        restore_path = u"testfiles/restore_out"
        restored = self.directory_tree_to_list_of_lists(restore_path)
        self.assertEqual(restored, [[u"1.doc", u"1.py"]])

    def test_include_subdirectories_not_files(self):
        u""" Test that a trailing slash glob only matches directories"""
        self.backup(u"full", u"testfiles/select2",
                    options=[u"--include", u"testfiles/select2/1/1sub1/**/",
                             u"--exclude", u"testfiles/select2/1/1sub1/**",
                             u"--exclude", u"**"])
        self.restore()
        restore_path = u"testfiles/restore_out"
        restored = self.directory_tree_to_list_of_lists(restore_path)
        self.assertEqual(restored, [[u"1"], [u"1sub1"],
                                    [u"1sub1sub1", u"1sub1sub2", u"1sub1sub3"]])


class TestGlobbingReplacement(IncludeExcludeFunctionalTest):
    u""" This tests the behaviour of the extended shell globbing pattern replacement functions."""
    # See the manual for a description of behaviours, but in summary:
    # * can be expanded to any string of characters not containing "/"
    # ? expands to any character except "/" and
    # [...] expands to a single character of those characters specified (ranges are acceptable).
    # The new special pattern, **, expands to any string of characters whether or not it contains "/".
    # Furthermore, if the pattern starts with "ignorecase:" (case insensitive), then this prefix will be
    # removed and any character in the string can be replaced with an upper- or lowercase version of itself.

    def test_globbing_replacement_in_includes(self):
        u""" Test behaviour of the extended shell globbing pattern replacement functions in both include and exclude"""
        # Identical to test_include_exclude_basic with globbing characters added to both include and exclude lines
        # Exhibits the issue reported in Bug #884371 (https://bugs.launchpad.net/duplicity/+bug/884371).
        # See above and the unit tests for more granularity on the issue.
        self.backup(u"full", u"testfiles/select2",
                    options=[u"--include", u"testfiles/select2/**/3sub3sub2/3sub3su?2_file.txt",  # Note ** and ? added
                             u"--exclude", u"testfiles/select2/*/3s*1",  # Note * added in both directory and filename
                             u"--exclude", u"testfiles/select2/**/2sub1sub3",  # Note ** added
                             u"--exclude", u"ignorecase:testfiles/select2/2/2sub1/2Sub1Sub2",  # Note ignorecase added
                             u"--include", u"ignorecase:testfiles/sel[w,u,e,q]ct2/2/2S?b1",    # Note ignorecase, [] and
                             # ? added
                             u"--exclude", u"testfiles/select2/1/1sub3/1s[w,u,p,q]b3sub2",  # Note [] added
                             u"--exclude", u"testfiles/select2/1/1sub[1-4]/1sub3sub1",  # Note [range] added
                             u"--include", u"testfiles/select2/*/1sub2/1s[w,u,p,q]b2sub1",  # Note * and [] added
                             u"--exclude", u"testfiles/select2/1/1sub1/1sub1sub3/1su?1sub3_file.txt",  # Note ? added
                             u"--exclude", u"testfiles/select2/1/1*1/1sub1sub2",  # Note * added
                             u"--exclude", u"testfiles/select2/1/1sub2",
                             u"--include", u"testfiles/select[2-4]/*.py",  # Note * and [range] added
                             u"--include", u"testfiles/*2/3",  # Note * added
                             u"--include", u"**/select2/1",  # Note ** added
                             u"--exclude", u"testfiles/select2/**"])
        self.restore()
        restore_path = u"testfiles/restore_out"
        restored = self.directory_tree_to_list_of_lists(restore_path)
        self.assertEqual(restored, self.expected_restored_tree)

    def test_globbing_replacement_in_includes_using_filter_ignorecase(self):
        u""" Test behaviour of the extended shell globbing pattern replacement functions in both include and exclude.
        same test as above, but implemented using --filter-*case instead of the ignorecase prefix.
        """
        # Identical to test_include_exclude_basic with globbing characters added to both include and exclude lines
        # Exhibits the issue reported in Bug #884371 (https://bugs.launchpad.net/duplicity/+bug/884371).
        # See above and the unit tests for more granularity on the issue.
        self.backup(u"full", u"testfiles/select2",
                    options=[u"--include", u"testfiles/select2/**/3sub3sub2/3sub3su?2_file.txt",  # Note ** and ? added
                             u"--exclude", u"testfiles/select2/*/3s*1",  # Note * added in both directory and filename
                             u"--exclude", u"testfiles/select2/**/2sub1sub3",  # Note ** added
                             u"--filter-ignorecase",
                             u"--exclude", u"testfiles/select2/2/2sub1/2Sub1Sub2",  # Note ignorecase added
                             u"--include", u"testfiles/sel[w,u,e,q]ct2/2/2S?b1",    # Note ignorecase, [] and
                             u"--filter-strictcase",
                             # ? added
                             u"--exclude", u"testfiles/select2/1/1sub3/1s[w,u,p,q]b3sub2",  # Note [] added
                             u"--exclude", u"testfiles/select2/1/1sub[1-4]/1sub3sub1",  # Note [range] added
                             u"--include", u"testfiles/select2/*/1sub2/1s[w,u,p,q]b2sub1",  # Note * and [] added
                             u"--exclude", u"testfiles/select2/1/1sub1/1sub1sub3/1su?1sub3_file.txt",  # Note ? added
                             u"--exclude", u"testfiles/select2/1/1*1/1sub1sub2",  # Note * added
                             u"--exclude", u"testfiles/select2/1/1sub2",
                             u"--include", u"testfiles/select[2-4]/*.py",  # Note * and [range] added
                             u"--include", u"testfiles/*2/3",  # Note * added
                             u"--include", u"**/select2/1",  # Note ** added
                             u"--exclude", u"testfiles/select2/**"])
        self.restore()
        restore_path = u"testfiles/restore_out"
        restored = self.directory_tree_to_list_of_lists(restore_path)
        self.assertEqual(restored, self.expected_restored_tree)


class TestExcludeIfPresent(IncludeExcludeFunctionalTest):
    u""" This tests the behaviour of duplicity's --exclude-if-present option"""

    def test_exclude_if_present_baseline(self):
        u""" Test that duplicity normally backs up files"""
        with io.open(u"testfiles/select2/1/1sub1/1sub1sub1/.nobackup", u"w") as tag:
            tag.write(u"Files in this folder should not be backed up.")
        self.backup(u"full", u"testfiles/select2/1/1sub1",
                    options=[u"--include", u"testfiles/select2/1/1sub1/1sub1sub1/*",
                             u"--exclude", u"**"])
        self.restore()
        restore_path = u"testfiles/restore_out"
        restored = self.directory_tree_to_list_of_lists(restore_path)
        self.assertEqual(restored, [[u"1sub1sub1"],
                                    [u".nobackup", u"1sub1sub1_file.txt"]])

    def test_exclude_if_present_excludes(self):
        u""" Test that duplicity excludes files with relevant tag"""
        with io.open(u"testfiles/select2/1/1sub1/1sub1sub1/.nobackup", u"w") as tag:
            tag.write(u"Files in this folder should not be backed up.")
        self.backup(u"full", u"testfiles/select2/1/1sub1",
                    options=[u"--exclude-if-present", u".nobackup",
                             u"--include", u"testfiles/select2/1/1sub1/1sub1sub1/*",
                             u"--exclude", u"**"])
        self.restore()
        restore_path = u"testfiles/restore_out"
        restored = self.directory_tree_to_list_of_lists(restore_path)
        self.assertEqual(restored, [])

    def test_exclude_if_present_excludes_2(self):
        u""" Test that duplicity excludes files with relevant tag"""
        with io.open(u"testfiles/select2/1/1sub1/1sub1sub1/EXCLUDE.tag", u"w") as tag:
            tag.write(u"Files in this folder should also not be backed up.")
        self.backup(u"full", u"testfiles/select2/1/1sub1",
                    options=[u"--exclude-if-present", u"EXCLUDE.tag",
                             u"--include", u"testfiles/select2/1/1sub1/1sub1sub1/*",
                             u"--exclude", u"**"])
        self.restore()
        restore_path = u"testfiles/restore_out"
        restored = self.directory_tree_to_list_of_lists(restore_path)
        self.assertEqual(restored, [])


class TestLockedFoldersNoError(IncludeExcludeFunctionalTest):
    u""" This tests that inaccessible folders do not cause an error"""

    @unittest.skipUnless(platform.platform().startswith(u"Linux"),
                         u"Skip on non-Linux systems")
    def test_locked_baseline(self):
        u""" Test no error if locked in path but excluded"""
        folder_to_lock = u"testfiles/select2/1/1sub1/1sub1sub3"
        initial_mode = os.stat(folder_to_lock).st_mode
        os.chmod(folder_to_lock, 0o0000)
        self.backup(u"full", u"testfiles/select2/1/1sub1",
                    options=[u"--include", u"testfiles/select2/1/1sub1/1sub1sub1/*",
                             u"--exclude", u"**"])
        os.chmod(folder_to_lock, initial_mode)
        self.restore()
        restore_path = u"testfiles/restore_out"
        restored = self.directory_tree_to_list_of_lists(restore_path)
        self.assertEqual(restored, [[u"1sub1sub1"],
                                    [u"1sub1sub1_file.txt"]])

    @unittest.skipUnless(platform.platform().startswith(u"Linux"),
                         u"Skip on non-Linux systems")
    def test_locked_excl_if_present(self):
        u""" Test no error if excluded locked with --exclude-if-present"""
        # Regression test for Bug #1620085
        # https://bugs.launchpad.net/duplicity/+bug/1620085
        folder_to_lock = u"testfiles/select2/1/1sub1/1sub1sub3"
        initial_mode = os.stat(folder_to_lock).st_mode
        os.chmod(folder_to_lock, 0o0000)
        self.backup(u"full", u"testfiles/select2/1/1sub1",
                    options=[u"--exclude-if-present", u"EXCLUDE.tag",
                             u"--include", u"testfiles/select2/1/1sub1/1sub1sub1/*",
                             u"--exclude", u"**"])
        os.chmod(folder_to_lock, initial_mode)
        self.restore()
        restore_path = u"testfiles/restore_out"
        restored = self.directory_tree_to_list_of_lists(restore_path)
        self.assertEqual(restored, [[u"1sub1sub1"],
                                    [u"1sub1sub1_file.txt"]])


class TestFolderIncludesFiles(IncludeExcludeFunctionalTest):
    u""" This tests that including a folder includes the files within it"""
    # https://bugs.launchpad.net/duplicity/+bug/1624725

    def test_includes_files(self):
        u"""This tests that including a folder includes the files within it"""
        self.backup(u"full", u"testfiles/select2/1/1sub1",
                    options=[u"--include", u"testfiles/select2/1/1sub1/1sub1sub1",
                             u"--exclude", u"**"])
        self.restore()
        restore_path = u"testfiles/restore_out"
        restored = self.directory_tree_to_list_of_lists(restore_path)
        self.assertEqual(restored, [[u"1sub1sub1"],
                                    [u"1sub1sub1_file.txt"]])

    def test_includes_files_trailing_slash(self):
        u"""This tests that including a folder includes the files within it"""
        self.backup(u"full", u"testfiles/select2/1/1sub1",
                    options=[u"--include", u"testfiles/select2/1/1sub1/1sub1sub1/",
                             u"--exclude", u"**"])
        self.restore()
        restore_path = u"testfiles/restore_out"
        restored = self.directory_tree_to_list_of_lists(restore_path)
        self.assertEqual(restored, [[u"1sub1sub1"],
                                    [u"1sub1sub1_file.txt"]])

    def test_includes_files_trailing_slash_globbing_chars(self):
        u"""Tests folder includes with globbing char and /"""
        self.backup(u"full", u"testfiles/select2/1/1sub1",
                    options=[u"--include", u"testfiles/s?lect2/1/1sub1/1sub1sub1/",
                             u"--exclude", u"**"])
        self.restore()
        restore_path = u"testfiles/restore_out"
        restored = self.directory_tree_to_list_of_lists(restore_path)
        self.assertEqual(restored, [[u"1sub1sub1"],
                                    [u"1sub1sub1_file.txt"]])

    def test_excludes_files_no_trailing_slash(self):
        u"""This tests that excluding a folder excludes the files within it"""
        self.backup(u"full", u"testfiles/select2/1/1sub1",
                    options=[u"--exclude", u"testfiles/select2/1/1sub1/1sub1sub1",
                             u"--exclude", u"testfiles/select2/1/1sub1/1sub1sub2",
                             u"--exclude", u"testfiles/select2/1/1sub1/1sub1sub3",
                             u"--include", u"testfiles/select2/1/1sub1/1sub1**",
                             u"--exclude", u"testfiles/select2/1/1sub1/irrelevant.txt"])
        self.restore()
        restore_path = u"testfiles/restore_out"
        restored = self.directory_tree_to_list_of_lists(restore_path)
        self.assertEqual(restored, [])

    def test_excludes_files_trailing_slash(self):
        u"""Excluding a folder excludes the files within it, if ends with /"""
        self.backup(u"full", u"testfiles/select2/1/1sub1",
                    options=[u"--exclude", u"testfiles/select2/1/1sub1/1sub1sub1/",
                             u"--exclude", u"testfiles/select2/1/1sub1/1sub1sub2/",
                             u"--exclude", u"testfiles/select2/1/1sub1/1sub1sub3/",
                             u"--include", u"testfiles/select2/1/1sub1/1sub1**",
                             u"--exclude", u"testfiles/select2/1/1sub1/irrelevant.txt"])
        self.restore()
        restore_path = u"testfiles/restore_out"
        restored = self.directory_tree_to_list_of_lists(restore_path)
        self.assertEqual(restored, [])

    def test_excludes_files_trailing_slash_globbing_chars(self):
        u"""Tests folder excludes with globbing char and /"""
        self.backup(u"full", u"testfiles/select2/1/1sub1",
                    options=[u"--exclude", u"testfiles/sel?ct2/1/1sub1/1sub1sub1/",
                             u"--exclude", u"testfiles/sel[e,f]ct2/1/1sub1/1sub1sub2/",
                             u"--exclude", u"testfiles/sel*t2/1/1sub1/1sub1sub3/",
                             u"--include", u"testfiles/select2/1/1sub1/1sub1**",
                             u"--exclude", u"testfiles/select2/1/1sub1/irrelevant.txt"])
        self.restore()
        restore_path = u"testfiles/restore_out"
        restored = self.directory_tree_to_list_of_lists(restore_path)
        self.assertEqual(restored, [])


class TestAbsolutePaths(IncludeExcludeFunctionalTest):
    u""" Tests include/exclude options with absolute paths"""

    def test_absolute_paths_non_globbing(self):
        u""" Test --include and --exclude work with absolute paths"""
        self.backup(u"full", os.path.abspath(u"testfiles/select2"),
                    options=[u"--include", os.path.abspath(u"testfiles/select2/3/3sub3/3sub3sub2/3sub3sub2_file.txt"),
                             u"--exclude", os.path.abspath(u"testfiles/select2/3/3sub3/3sub3sub2"),
                             u"--include", os.path.abspath(u"testfiles/select2/3/3sub2/3sub2sub2"),
                             u"--include", os.path.abspath(u"testfiles/select2/3/3sub3"),
                             u"--exclude", os.path.abspath(u"testfiles/select2/3/3sub1"),
                             u"--exclude", os.path.abspath(u"testfiles/select2/2/2sub1/2sub1sub3"),
                             u"--exclude", os.path.abspath(u"testfiles/select2/2/2sub1/2sub1sub2"),
                             u"--include", os.path.abspath(u"testfiles/select2/2/2sub1"),
                             u"--exclude", os.path.abspath(u"testfiles/select2/1/1sub3/1sub3sub2"),
                             u"--exclude", os.path.abspath(u"testfiles/select2/1/1sub3/1sub3sub1"),
                             u"--exclude", os.path.abspath(u"testfiles/select2/1/1sub2/1sub2sub3"),
                             u"--include", os.path.abspath(u"testfiles/select2/1/1sub2/1sub2sub1"),
                             u"--exclude", os.path.abspath(u"testfiles/select2/1/1sub1/1sub1sub3/1sub1sub3_file.txt"),
                             u"--exclude", os.path.abspath(u"testfiles/select2/1/1sub1/1sub1sub2"),
                             u"--exclude", os.path.abspath(u"testfiles/select2/1/1sub2"),
                             u"--include", os.path.abspath(u"testfiles/select2/1.py"),
                             u"--include", os.path.abspath(u"testfiles/select2/3"),
                             u"--include", os.path.abspath(u"testfiles/select2/1"),
                             u"--exclude", os.path.abspath(u"testfiles/select2/**")])
        self.restore()
        restore_path = u"testfiles/restore_out"
        restored = self.directory_tree_to_list_of_lists(restore_path)
        self.assertEqual(restored, self.expected_restored_tree)


@unittest.skipUnless(platform.platform().startswith(u"Linux"), u"Skip on non-Linux systems")
@unittest.skipUnless(sys.getfilesystemencoding().upper() == u"UTF-8", u"Skip on non-UTF-8 systems")
@unittest.skipIf(sys.version_info[:2] < (3, 7), u"Skip on bad unicode handling")
class TestUnicode(IncludeExcludeFunctionalTest):
    u""" Tests include/exclude options with unicode paths"""

    def test_unicode_paths_non_globbing(self):
        u""" Test --include and --exclude work with unicode paths"""
        self.backup(u"full", u"testfiles/select-unicode",
                    options=[u"--exclude", u"testfiles/select-unicode/прыклад/пример/例/Παράδειγμα/उदाहरण.txt",
                             u"--exclude", u"testfiles/select-unicode/прыклад/пример/例/Παράδειγμα/דוגמא.txt",
                             u"--exclude", u"testfiles/select-unicode/прыклад/пример/例/მაგალითი/",
                             u"--include", u"testfiles/select-unicode/прыклад/пример/例/",
                             u"--exclude", u"testfiles/select-unicode/прыклад/пример/",
                             u"--include", u"testfiles/select-unicode/прыклад/",
                             u"--include", u"testfiles/select-unicode/օրինակ.txt",
                             u"--exclude", u"testfiles/select-unicode/**"])
        self.restore()
        restore_path = u"testfiles/restore_out"
        restored = self.directory_tree_to_list_of_lists(restore_path)
        self.assertEqual(restored, [[u"прыклад", u"օրինակ.txt"],
                                    [u"пример", u"উদাহরণ"], [u"例"], [u"Παράδειγμα"], [u"ઉદાહરણ.log"]])

    def test_unicode_paths_asterisks(self):
        u""" Test --include and --exclude work with unicode paths and globs containing * and **"""
        p = u"testfiles/select-unicode/"
        self.backup(u"full", u"testfiles/select-unicode",
                    options=[u"--exclude", p + u"прыклад/пример/例/Παρά*ειγμα/उदाहरण.txt",  # Note *
                             u"--exclude", p + u"прыклад/пример/例/Παράδειγμα/דוגמא.txt",
                             u"--exclude", p + u"прыклад/пример/例/მაგალითი/",
                             u"--include", p + u"пр**/例/",  # Note **
                             u"--exclude", p + u"прыклад/пример/",
                             u"--include", p + u"прыкла*/",  # Note *
                             u"--include", p + u"օր*ակ.txt",  # Note *
                             u"--exclude", p + u"**"])
        self.restore()
        restore_path = u"testfiles/restore_out"
        restored = self.directory_tree_to_list_of_lists(restore_path)
        self.assertEqual(restored, [[u"прыклад", u"օրինակ.txt"],
                                    [u"пример", u"উদাহরণ"], [u"例"], [u"Παράδειγμα"], [u"ઉદાહરણ.log"]])

    def test_unicode_paths_square_brackets(self):
        u""" Test --include and --exclude work with unicode paths with character options in []s and [!]s"""
        p = u"testfiles/select-unicode/"
        self.backup(u"full", u"testfiles/select-unicode",
                    options=[u"--exclude", p + u"прыклад/пример/例/Παράδειγμα/उदाहरण.txt",
                             u"--exclude", p + u"пры[к,и,р]лад/пример/例/Παράδειγμα/דוגמא.txt",
                             u"--exclude", p + u"прыклад/пр[!a,b,c]мер/例/მაგალითი/",
                             u"--include", p + u"прыклад/при[g,м,д]ер/例/",
                             u"--exclude", p + u"прыклад/пример/",
                             u"--include", p + u"прыклад/",
                             u"--include", p + u"օրինակ.txt",
                             u"--exclude", p + u"**"])
        self.restore()
        restore_path = u"testfiles/restore_out"
        restored = self.directory_tree_to_list_of_lists(restore_path)
        self.assertEqual(restored, [[u"прыклад", u"օրինակ.txt"],
                                    [u"пример", u"উদাহরণ"], [u"例"], [u"Παράδειγμα"], [u"ઉદાહરણ.log"]])

    def test_unicode_filelist(self):
        u"""Test that exclude filelist works with unicode filenames"""
        # As this is an exclude filelist any lines with no +/- modifier should be treated as if they have a -.
        path = u"testfiles/select-unicode/"
        # Create a filelist
        with io.open(u"testfiles/exclude.txt", u"w", encoding=u"UTF-8") as f:
            f.write(u"- " + path + u"прыклад/пример/例/Παράδειγμα/उदाहरण.txt\n"
                    u"- " + path + u"прыклад/пример/例/Παράδειγμα/דוגמא.txt\n"
                    u"- " + path + u"прыклад/пример/例/მაგალითი/\n"
                    u"+ " + path + u"прыклад/пример/例/\n"
                    u"- " + path + u"прыклад/пример/\n"
                    u"+ " + path + u"прыклад/\n"
                    u"+ " + path + u"օրինակ.txt\n"
                    u"- " + path + u"**")
        self.backup(u"full", path, options=[u"--exclude-filelist=testfiles/exclude.txt"])
        self.restore()
        restore_path = u"testfiles/restore_out"
        restored = self.directory_tree_to_list_of_lists(restore_path)
        self.assertEqual(restored, [[u"прыклад", u"օրինակ.txt"],
                                    [u"пример", u"উদাহরণ"], [u"例"], [u"Παράδειγμα"], [u"ઉદાહરણ.log"]])


if __name__ == u"__main__":
    unittest.main()
