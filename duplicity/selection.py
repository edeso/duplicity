# -*- Mode:Python; indent-tabs-mode:nil; tab-width:4; encoding:utf-8 -*-
#
# Copyright 2002 Ben Escoto <ben@emerose.org>
# Copyright 2007 Kenneth Loafman <kenneth@loafman.com>
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

from builtins import next
from builtins import str
from builtins import object

import os
import stat
import sys
import re

from duplicity import config
from duplicity import diffdir
from duplicity import log
from duplicity import util
from duplicity.globmatch import GlobbingError, FilePrefixError, select_fn_from_glob
from duplicity.path import *  # pylint: disable=unused-wildcard-import,redefined-builtin

u"""Iterate exactly the requested files in a directory

Parses includes and excludes to yield correct files.  More
documentation on what this code does can be found on the man page.

"""


class Select(object):
    u"""Iterate appropriate Paths in given directory

    This class acts as an iterator on account of its next() method.
    Basically, it just goes through all the files in a directory in
    order (depth-first) and subjects each file to a bunch of tests
    (selection functions) in order.  The first test that includes or
    excludes the file means that the file gets included (iterated) or
    excluded.  The default is include, so with no tests we would just
    iterate all the files in the directory in order.

    The one complication to this is that sometimes we don't know
    whether or not to include a directory until we examine its
    contents.  For instance, if we want to include all the **.py
    files.  If /home/ben/foo.py exists, we should also include /home
    and /home/ben, but if these directories contain no **.py files,
    they shouldn't be included.  For this reason, a test may not
    include or exclude a directory, but merely "scan" it.  If later a
    file in the directory gets included, so does the directory.

    As mentioned above, each test takes the form of a selection
    function.  The selection function takes a path, and returns:

    None - means the test has nothing to say about the related file
    0 - the file is excluded by the test
    1 - the file is included
    2 - the test says the file (must be directory) should be scanned

    Also, a selection function f has a variable f.exclude which should
    be true if f could potentially exclude some file. This is used
    to signal an error if the last function only includes, which would
    be redundant and presumably isn't what the user intends.

    """

    def __init__(self, path):
        u"""Initializer, called with Path of root directory"""
        assert isinstance(path, Path), str(path)
        self.selection_functions = []
        self.rootpath = path
        self.prefix = self.rootpath.uc_name

    def __iter__(self):  # pylint: disable=non-iterator-returned
        return self

    def __next__(self):
        return next(self.iter)

    def set_iter(self):
        u"""Initialize generator, prepare to iterate."""
        # Externally-accessed method
        self.rootpath.setdata()  # this may have changed since Select init
        self.iter = self.Iterate(self.rootpath)
        return self

    def Iterate(self, path):
        u"""Return iterator yielding paths in path

        This function looks a bit more complicated than it needs to be
        because it avoids extra recursion (and no extra function calls
        for non-directory files) while still doing the "directory
        scanning" bit.

        """
        # Only called by set_iter. Internal.
        def error_handler(exc, path, filename):  # pylint: disable=unused-argument
            fullpath = os.path.join(path.name, filename)
            try:
                mode = os.stat(fullpath)[stat.ST_MODE]
                if stat.S_ISSOCK(mode):
                    log.Info(_(u"Skipping socket %s") % util.fsdecode(fullpath),
                             log.InfoCode.skipping_socket,
                             util.escape(fullpath))
                else:
                    log.Warn(_(u"Error initializing file %s") % util.fsdecode(fullpath),
                             log.WarningCode.cannot_iterate,
                             util.escape(fullpath))
            except OSError:
                log.Warn(_(u"Error accessing possibly locked file %s") % util.fsdecode(fullpath),
                         log.WarningCode.cannot_stat, util.escape(fullpath))
            return None

        def diryield(path):
            u"""Generate relevant files in directory path

            Returns (path, num) where num == 0 means path should be
            generated normally, num == 1 means the path is a directory
            and should be included iff something inside is included.

            """
            # Only called by Iterate. Internal.
            # todo: get around circular dependency issue by importing here
            from duplicity import robust
            for filename in robust.listpath(path):
                new_path = robust.check_common_error(
                    error_handler, Path.append, (path, filename))
                if new_path:
                    s = self.Select(new_path)
                    if (new_path.type in [u"reg", u"dir"]
                        and not os.access(new_path.name, os.R_OK)) \
                            and (s == 1 or s == 2):
                        # Path is a file or folder that cannot be read, but
                        # should be included or scanned.
                        log.Warn(_(u"Error accessing possibly locked file %s") %
                                 new_path.uc_name,
                                 log.WarningCode.cannot_read,
                                 util.escape(new_path.name))
                        if diffdir.stats:
                            diffdir.stats.Errors += 1
                    elif s == 1:
                        # Should be included
                        yield (new_path, 0)
                    elif s == 2 and new_path.isdir():
                        # Is a directory that should be scanned
                        yield (new_path, 1)

        if not path.type:
            # base doesn't exist
            log.Warn(_(u"Warning: base %s doesn't exist, continuing") %
                     path.uc_name)
            return
        log.Debug(_(u"Selecting %s") % path.uc_name)
        yield path
        if not path.isdir():
            return
        diryield_stack = [diryield(path)]
        delayed_path_stack = []

        while diryield_stack:
            try:
                subpath, val = next(diryield_stack[-1])
            except StopIteration:
                diryield_stack.pop()
                if delayed_path_stack:
                    delayed_path_stack.pop()
                continue
            if val == 0:
                if delayed_path_stack:
                    for delayed_path in delayed_path_stack:
                        log.Log(_(u"Selecting %s") % delayed_path.uc_name, 6)
                        yield delayed_path
                    del delayed_path_stack[:]
                log.Debug(_(u"Selecting %s") % subpath.uc_name)
                yield subpath
                if subpath.isdir():
                    diryield_stack.append(diryield(subpath))
            elif val == 1:
                delayed_path_stack.append(subpath)
                diryield_stack.append(diryield(subpath))

    def Select(self, path):
        u"""Run through the selection functions and return dominant val 0/1/2"""
        # Only used by diryield and tests. Internal.
        log.Debug(u"Selection: examining path %s" % path.uc_name)
        if not self.selection_functions:
            log.Debug(u"Selection:     + no selection functions found. Including")
            return 1
        scan_pending = False
        for sf in self.selection_functions:
            result = sf(path)
            log.Debug(u"Selection:     result: %4s from function: %s" %
                      (str(result), sf.name))
            if result == 2:
                # Selection function says that the path should be scanned for matching files, but keep going
                # through the selection functions looking for a real match (0 or 1).
                scan_pending = True
            elif result == 0 or result == 1:
                # A real match found, no need to try other functions.
                break

        if scan_pending and result != 1:
            # A selection function returned 2 and either no real match was
            # found or the highest-priority match was 0
            result = 2
        if result is None:
            result = 1

        if result == 0:
            log.Debug(u"Selection:     - excluding file")
        elif result == 1:
            log.Debug(u"Selection:     + including file")
        else:
            assert result == 2
            log.Debug(u"Selection:     ? scanning directory for matches")

        return result

    def ParseArgs(self, argtuples, filelists):
        u"""Create selection functions based on list of tuples

        The tuples are created when the initial commandline arguments
        are read.  They have the form (option string, additional
        argument) except for the filelist tuples, which should be
        (option-string, (additional argument, filelist_fp)).

        """
        # Sanity checks on --filter-* options for the benefit of users
        if argtuples and argtuples[-1][0].startswith(u"--filter-"):
            log.FatalError(_(u"""\
The last file selection option is the filter option %s, which will have no
effect as there are no subsequent file selection options. Exiting because
this probably isn't what you meant.""") %
                           (argtuples[-1][0],),
                           log.ErrorCode.trailing_filter)
        f_opt = set(opt[0] for opt in argtuples if opt[0].startswith(u"--filter-"))
        f_def = (u"--filter-globbing", u"--filter-strictcase")
        if f_opt and all(opt in f_def for opt in f_opt):
            log.FatalError(_(u"""\
Only these filter mode options were specified:
    %s
Case sensitive globbing is the default behaviour and so this has no effect.
Exiting because this probably isn't what you meant.""") %
                           (u", ".join(f_opt),),
                           log.ErrorCode.redundant_filter)

        # Called by commandline.py set_selection. External.
        filelists_index = 0
        mode = u"globbing"
        no_case = False
        try:
            for opt, arg in argtuples:
                if opt == u"--exclude":
                    self.add_selection_func(self.general_get_sf(arg, 0, mode, ignore_case=no_case))
                elif opt == u"--exclude-if-present":
                    self.add_selection_func(self.present_get_sf(arg, 0), add_to_start=True)
                elif opt == u"--exclude-device-files":
                    self.add_selection_func(self.devfiles_get_sf(), add_to_start=True)
                elif opt == u"--exclude-filelist":
                    for sf in self.filelist_general_get_sfs(filelists[filelists_index], 0, arg, mode, no_case):
                        self.add_selection_func(sf)
                    filelists_index += 1
                elif opt == u"--exclude-globbing-filelist":
                    # --exclude-globbing-filelist is now deprecated, but if it
                    # turns up then it needs to always work in globbing mode...
                    for sf in self.filelist_general_get_sfs(filelists[filelists_index], 0, arg, u"globbing", no_case):
                        self.add_selection_func(sf)
                    filelists_index += 1
                elif opt == u"--exclude-other-filesystems":
                    self.add_selection_func(self.other_filesystems_get_sf(0))
                elif opt == u"--exclude-regexp":
                    self.add_selection_func(self.regexp_get_sf(arg, 0, no_case))
                elif opt == u"--exclude-older-than":
                    self.add_selection_func(self.exclude_older_get_sf(arg))
                elif opt == u"--filter-strictcase":
                    no_case = False
                elif opt == u"--filter-globbing":
                    mode = u"globbing"
                elif opt == u"--filter-ignorecase":
                    no_case = True
                elif opt == u"--filter-literal":
                    mode = u"literal"
                elif opt == u"--filter-regexp":
                    mode = u"regex"
                elif opt == u"--include":
                    self.add_selection_func(self.general_get_sf(arg, 1, mode, no_case))
                elif opt == u"--include-filelist":
                    for sf in self.filelist_general_get_sfs(filelists[filelists_index], 1, arg, mode, no_case):
                        self.add_selection_func(sf)
                    filelists_index += 1
                elif opt == u"--include-globbing-filelist":
                    # --include-globbing-filelist is now deprecated, but if it
                    # turns up then it needs to always work in globbing mode...
                    for sf in self.filelist_general_get_sfs(filelists[filelists_index], 1, arg, u"globbing", no_case):
                        self.add_selection_func(sf)
                    filelists_index += 1
                elif opt == u"--include-regexp":
                    self.add_selection_func(self.regexp_get_sf(arg, 1, no_case))
                else:
                    assert 0, u"Bad selection option %s" % opt
        except GlobbingError as e:
            self.parse_catch_error(e)
        assert filelists_index == len(filelists)
        self.parse_last_excludes()

    def parse_catch_error(self, exc):
        u"""Deal with selection error exc"""
        # Internal, used by ParseArgs.
        if isinstance(exc, FilePrefixError):
            log.FatalError(_(u"""\
Fatal Error: The file specification
    %s
cannot match any files in the base directory
    %s
Useful file specifications begin with the base directory or some
pattern (such as '**') which matches the base directory.""") %
                           (exc, self.prefix), log.ErrorCode.file_prefix_error)
        elif isinstance(exc, GlobbingError):
            log.FatalError(_(u"Fatal Error while processing expression\n"
                             u"%s") % exc, log.ErrorCode.globbing_error)
        else:
            raise  # pylint: disable=misplaced-bare-raise

    def parse_last_excludes(self):
        u"""Exit with error if last selection function isn't an exclude"""
        # Internal. Used by ParseArgs.
        if self.selection_functions and not self.selection_functions[-1].exclude:
            log.FatalError(_(u"""\
Last selection expression:
    %s
only specifies that files be included.  Because the default is to
include all files, the expression is redundant.  Exiting because this
probably isn't what you meant.""") %
                           (self.selection_functions[-1].name,),
                           log.ErrorCode.redundant_inclusion)

    def add_selection_func(self, sel_func, add_to_start=None):
        u"""Add another selection function at the end or beginning"""
        # Internal. Used by ParseArgs.
        if add_to_start:
            self.selection_functions.insert(0, sel_func)
        else:
            self.selection_functions.append(sel_func)

    def filelist_sanitise_line(self, line, include_default):
        u"""
        Sanitises lines of both normal and globbing filelists, returning
        (line, include) and line=None if blank/comment

        The aim is to parse filelists in a consistent way, prior to the
        interpretation of globbing statements. The function removes
        whitespace, comment lines and processes modifiers (leading +/-)
        and quotes.
        """
        # Internal. Used by filelist_general_get_sfs

        line = line.strip()
        if not line:  # skip blanks
            return None, include_default
        if line.startswith(u"#"):  # skip full-line comments
            return None, include_default

        include = include_default
        if line.startswith(u"+ "):
            # Check for "+ " or "- " syntax
            include = 1
            line = line[2:]
        elif line.startswith(u"- "):
            include = 0
            line = line[2:]

        if (line.startswith(u"'") and line.endswith(u"'")) or (line.startswith(u'"') and line.endswith(u'"')):
            line = line[1:-1]

        return line, include

    def filelist_general_get_sfs(self, filelist_fp, inc_default, list_name, mode=u"globbing", ignore_case=False):
        u"""Return list of selection functions by reading fileobj

        filelist_fp should be an open file object
        inc_default is true if this is an include list
        list_name is just the name of the list, used for logging
        mode indicates whether to glob, regex, or not

        """
        # Internal. Used by ParseArgs.
        log.Notice(_(u"Reading %s filelist %s") % (mode, list_name))
        separator = config.null_separator and u"\0" or u"\n"
        try:
            filelist_fp.seek(0)
        except:
            pass
        for line in filelist_fp.read().split(separator):
            line, include = self.filelist_sanitise_line(line, inc_default)
            if not line:
                # Skip blanks and comment lines
                continue
            yield self.general_get_sf(line, include, mode, ignore_case)

    def other_filesystems_get_sf(self, include):
        u"""Return selection function matching files on other filesystems"""
        # Internal. Used by ParseArgs and unit tests.
        assert include == 0 or include == 1
        root_devloc = self.rootpath.getdevloc()

        def sel_func(path):
            if path.exists() and path.getdevloc() != root_devloc:
                return include
            else:
                return None

        sel_func.exclude = not include
        sel_func.name = u"Match other filesystems"
        return sel_func

    def regexp_get_sf(self, regexp_string, include, ignore_case=False):
        u"""Return selection function given by regexp_string"""
        # Internal. Used by ParseArgs and unit tests.
        assert include == 0 or include == 1

        flags = 0
        if ignore_case:
            flags = re.IGNORECASE

        try:
            regexp = re.compile(regexp_string, flags)
        except Exception:
            log.Warn(_(u"Error compiling regular expression %s") % regexp_string)
            raise

        def sel_func(path):
            if regexp.search(path.uc_name):
                return include
            else:
                return None

        sel_func.exclude = not include
        sel_func.name = u"regular expression %s %scase: %s" % \
            (include and u"include" or u"exclude", ignore_case and u"no-" or u"", regexp_string)
        return sel_func

    def devfiles_get_sf(self):
        u"""Return a selection function to exclude all dev files"""
        # Internal. Used by ParseArgs.
        def sel_func(path):
            if path.isdev():
                return 0
            else:
                return None

        sel_func.exclude = 1
        sel_func.name = u"Exclude device files"
        return sel_func

    def general_get_sf(self, pattern_str, include, mode=u"globbing", ignore_case=False):
        u"""Return selection function given by a pattern string

        The selection patterns are interpretted in accordance with the mode
        argument, "globbing", "literal", or "regex".

        The 'ignorecase:' prefix is a legacy feature which historically lived on
        the globbing code path and was only ever documented as working for globs.
        """

        # Internal. Used by ParseArgs, filelist_general_get_sfs and unit tests.
        assert include == 0 or include == 1
        assert isinstance(pattern_str, str)

        # legacy prefix applies *only* in globbing mode
        if mode == u"globbing" and pattern_str.lower().startswith(u"ignorecase:"):
            pattern_str = pattern_str[len(u"ignorecase:"):]
            pattern_str = util.casefold_compat(util.fsdecode(pattern_str))
            ignore_case = True

        if mode == u"globbing":
            return self.glob_get_sf(pattern_str, include, ignore_case)
        elif mode == u"literal":
            return self.literal_get_sf(pattern_str, include, ignore_case)
        elif mode == u"regex":
            return self.regexp_get_sf(pattern_str, include, ignore_case)
        else:
            assert 0, u"Bad selection mode %s" % mode

    def present_get_sf(self, filename, include):
        u"""Return selection function given by existence of a file in a directory"""
        # Internal. Used by ParseArgs.
        assert include == 0 or include == 1

        # todo: get around circular dependency issue by importing here
        from duplicity.robust import check_common_error

        def exclude_sel_func(path):
            # do not follow symbolic links when checking for file existence!
            if path.isdir():
                def error_handler(_exc, _filename):
                    # Path is not read accessible
                    # ToDo: Ideally this error would only show if the folder
                    # was ultimately included by the full set of selection
                    # functions. Currently this will give an error for any
                    # locked directory within the folder being backed up.
                    log.Warn(_(
                        u"Error accessing possibly locked file %s") % path.uc_name,
                        log.WarningCode.cannot_read, util.escape(path.uc_name))
                    if diffdir.stats:
                        diffdir.stats.Errors += 1
                    return False
                if check_common_error(error_handler, path.contains, [filename]):
                    return 0
                else:
                    return None

        if include == 0:
            sel_func = exclude_sel_func
        else:
            log.FatalError(u"--include-if-present not implemented (would it make sense?).",
                           log.ErrorCode.not_implemented)

        sel_func.exclude = not include
        sel_func.name = u"Command-line %s filename: %s" % \
                        (include and u"include-if-present" or u"exclude-if-present", filename)
        return sel_func

    def glob_get_sf(self, glob_str, include, ignore_case=False):
        u"""Return selection function based on glob_str"""
        assert isinstance(glob_str, str), \
            u"The glob string " + glob_str.decode(sys.getfilesystemencoding(), u"ignore") + u" is not unicode"

        # Check to make sure prefix is ok, i.e. the glob string is within
        # the root folder being backed up
        if not select_fn_from_glob(glob_str, 1, ignore_case)(self.rootpath):
            # file_prefix_selection == 1 (include) or 2 (scan)
            raise FilePrefixError(glob_str)

        if glob_str == u"**":
            sel_func = lambda path: include
        else:
            sel_func = select_fn_from_glob(glob_str, include, ignore_case)

        sel_func.exclude = not include
        sel_func.name = u"shell glob %s %scase: %s" % \
                        (include and u"include" or u"exclude", ignore_case and u"no-" or u"", glob_str)

        return sel_func

    def literal_get_sf(self, lit_str, include, ignore_case=False):
        u"""Return a selection function that matches a literal string while
        still including the contents of any folders which are matched
        """

        # Check to make sure prefix is ok, see also glob_get_sf()
        if not self.select_fn_from_literal(lit_str, 1, ignore_case)(self.rootpath):
            raise FilePrefixError(lit_str)

        sel_func = self.select_fn_from_literal(lit_str, include, ignore_case)
        sel_func.exclude = not include
        sel_func.name = u"literal string %s %scase: %s" % \
                        (include and u"include" or u"exclude", ignore_case and u"no-" or u"", lit_str)
        return sel_func

    def exclude_older_get_sf(self, date):
        u"""Return selection function based on files older than modification date """
        # Internal. Used by ParseArgs.

        def sel_func(path):
            if not path.isreg():
                return None
            try:
                if os.path.getmtime(path.name) < date:
                    return 0
            except OSError as e:
                pass  # this is probably only on a race condition of file being deleted
            return None

        sel_func.exclude = True
        sel_func.name = u"Select older than %s" % (date,)
        return sel_func

    def select_fn_from_literal(self, lit_str, include, ignore_case=False):
        u"""Return a function test_fn(path) which test where a path matches a
        literal string. See also select_fn_from_blog() in globmatch.py

        This function is separated from literal_get_sf() so that it can be used
        to test the prefix without creating a loop.

        TODO: this doesn't need to be part of the Select class type, but not
        sure where else to put it?
        """
        if lit_str != u"/" and lit_str[-1] == u"/":
            lit_str = lit_str[:-1]

        if ignore_case:
            lit_str = util.casefold_compat(util.fsdecode(lit_str))

        def test_fn(path):
            # FIXME: caller to do this once, rather than for every path?
            if ignore_case:
                uc_name = util.casefold_compat(util.fsdecode(path.uc_name))
            else:
                uc_name = path.uc_name

            if uc_name == lit_str:
                return include
            elif uc_name.startswith(lit_str) and uc_name[len(lit_str)] == u"/":
                return include
            elif lit_str.startswith(uc_name) and lit_str[len(uc_name)] == u"/" and include == 1:
                return 2
            else:
                return None

        return test_fn
