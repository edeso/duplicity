# -*- Mode:Python; indent-tabs-mode:nil; tab-width:4; encoding:utf-8 -*-
#
# Copyright 2002 Ben Escoto <ben@emerose.org>
# Copyright 2007 Kenneth Loafman <kenneth@loafman.com>
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

"""Generate and process backup statistics"""

import json
import os
import re
import time

from duplicity import config
from duplicity import dup_time
from duplicity import util
from duplicity import log


class StatsException(Exception):
    pass


class StatsObj(object):
    """Contains various statistics, provide string conversion functions"""

    # used when quoting files in get_stats_line
    space_regex = re.compile(" ")

    stat_file_attrs = (
        "SourceFiles",
        "SourceFileSize",
        "NewFiles",
        "NewFileSize",
        "DeletedFiles",
        "ChangedFiles",
        "ChangedFileSize",
        "ChangedDeltaSize",
        "DeltaEntries",
        "RawDeltaSize",
    )
    stat_misc_attrs = ("Errors", "TotalDestinationSizeChange")
    stat_time_attrs = ("StartTime", "EndTime", "ElapsedTime")
    stat_attrs = ("Filename",) + stat_time_attrs + stat_misc_attrs + stat_file_attrs

    # Below, the second value in each pair is true iff the value
    # indicates a number of bytes
    stat_file_pairs = (
        ("SourceFiles", False),
        ("SourceFileSize", True),
        ("NewFiles", False),
        ("NewFileSize", True),
        ("DeletedFiles", False),
        ("ChangedFiles", False),
        ("ChangedFileSize", True),
        ("ChangedDeltaSize", True),
        ("DeltaEntries", False),
        ("RawDeltaSize", True),
    )

    # This is used in get_byte_summary_string below
    byte_abbrev_list = (
        (1024 * 1024 * 1024 * 1024, "TB"),
        (1024 * 1024 * 1024, "GB"),
        (1024 * 1024, "MB"),
        (1024, "KB"),
    )

    def __init__(self):
        """Set attributes to None"""
        for attr in self.stat_attrs:
            self.__dict__[attr] = None

    def get_stat(self, attribute):
        """Get a statistic"""
        return self.__dict__[attribute]

    def set_stat(self, attr, value):
        """Set attribute to given value"""
        self.__dict__[attr] = value

    def increment_stat(self, attr):
        """Add 1 to value of attribute"""
        self.__dict__[attr] += 1

    def get_stats_line(self, index, use_repr=1):
        """Return one line abbreviated version of full stats string"""
        file_attrs = [str(self.get_stat(a)) for a in self.stat_file_attrs]
        if not index:
            filename = "."
        else:
            filename = os.path.join(*index)
            if use_repr:
                # use repr to quote newlines in relative filename, then
                # take of leading and trailing quote and quote spaces.
                filename = self.space_regex.sub("\\\\x20", repr(filename))
                n = 1
                if filename[0] == "u":
                    n = 2
                filename = filename[n:-1]
        return " ".join(
            [
                filename,
            ]
            + file_attrs
        )

    def set_stats_from_line(self, line):
        """Set statistics from given line"""

        def error():
            raise StatsException(f"Bad line '{line}'")

        if line[-1] == "\n":
            line = line[:-1]
        lineparts = line.split(" ")
        if len(lineparts) < len(self.stat_file_attrs):
            error()
        for attr, val_string in zip(self.stat_file_attrs, lineparts[-len(self.stat_file_attrs) :]):
            try:
                val = int(val_string)
            except ValueError:
                try:
                    val = float(val_string)
                except ValueError:
                    error()
            self.set_stat(attr, val)
        return self

    def get_stats_string(self):
        """Return extended string printing out statistics"""
        return f"{self.get_timestats_string()}{self.get_filestats_string()}{self.get_miscstats_string()}"

    def get_timestats_string(self):
        """Return portion of statistics string dealing with time"""
        timelist = []
        if self.StartTime is not None:
            timelist.append(
                "StartTime %.2f (%s)\n"
                % (  # pylint: disable=bad-string-format-type
                    self.StartTime,
                    dup_time.timetopretty(self.StartTime),
                )
            )
        if self.EndTime is not None:
            timelist.append(
                "EndTime %.2f (%s)\n"
                % (  # pylint: disable=bad-string-format-type
                    self.EndTime,
                    dup_time.timetopretty(self.EndTime),
                )
            )
        if self.ElapsedTime or (  # pylint:disable=access-member-before-definition
            self.StartTime is not None and self.EndTime is not None
        ):
            if self.ElapsedTime is None:  # pylint:disable=access-member-before-definition
                self.ElapsedTime = self.EndTime - self.StartTime
            timelist.append(f"ElapsedTime {self.ElapsedTime:.2f} ({dup_time.inttopretty(self.ElapsedTime)})\n")
        return "".join(timelist)

    def get_filestats_string(self):
        """Return portion of statistics string about files and bytes"""

        def fileline(stat_file_pair):
            """Return zero or one line of the string"""
            attr, in_bytes = stat_file_pair
            val = self.get_stat(attr)
            if val is None:
                return ""
            if in_bytes:
                return f"{attr} {val} ({self.get_byte_summary_string(val)})\n"
            else:
                return f"{attr} {val}\n"

        return "".join(map(fileline, self.stat_file_pairs))

    def get_miscstats_string(self):
        """Return portion of extended stat string about misc attributes"""
        misc_string = ""
        tdsc = self.TotalDestinationSizeChange
        if tdsc is not None:
            misc_string += f"TotalDestinationSizeChange {tdsc} ({self.get_byte_summary_string(tdsc)})\n"
        if self.Errors is not None:
            misc_string += f"Errors {int(self.Errors)}\n"
        return misc_string

    def get_byte_summary_string(self, byte_count):
        """Turn byte count into human readable string like "7.23GB" """
        if byte_count < 0:
            sign = "-"
            byte_count = -byte_count
        else:
            sign = ""

        for abbrev_bytes, abbrev_string in self.byte_abbrev_list:
            if byte_count >= abbrev_bytes:
                # Now get 3 significant figures
                abbrev_count = float(byte_count) / abbrev_bytes
                if abbrev_count >= 100:
                    precision = 0
                elif abbrev_count >= 10:
                    precision = 1
                else:
                    precision = 2
                return f"{sign}{abbrev_count:.{precision}f} {abbrev_string}"
        byte_count = round(byte_count)
        if byte_count == 1:
            return f"{sign}1 byte"
        else:
            return f"{sign}{int(byte_count)} bytes"

    def get_stats_json(self, col_stat):
        """
        Return enriched statistics in JSON format
        @type col_stat: dup_collections.CollectionsStatus
        @param col_stat: allow to gather information about the whole
            backup chain

        @rtype: String
        @return: JSON formated string
        """

        def fail_save_read(parent, *attributes, is_function=False, default="N/A"):
            """
            returns "N/A" if value can't de determined.
            @type parent: object
            @param parent: object where vale should received from. Object must exists
            @type *attributes: list of str
            @param *attributes: path down to the attribute that should be read
            @type is_function: boolean
            @param is_function: run last attribute as function instead of reading the value direct
            @param default: overwrite return value if value can't be determined
            """
            try:
                attr_path = parent
                for attribute in attributes:
                    try:
                        attr_path = getattr(attr_path, attribute)
                    except AttributeError:
                        return default
                if is_function:
                    return attr_path()
                else:
                    return attr_path
            except Exception as e:
                log.Error(f"Can't read expected attribute: {e}")
                return default

        py_obj = {key: self.__dict__[key] for key in self.stat_attrs}
        for t in ("StartTime", "EndTime"):
            t_str = f"{t}_str"
            py_obj[t_str] = dup_time.timetostring(py_obj[t])
        if not py_obj.get("ElapsedTime"):
            py_obj["ElapsedTime"] = py_obj["EndTime"] - py_obj["StartTime"]
        if col_stat:
            backup_meta = {}
            backup_chain = col_stat.matched_chain_pair[1]
            backup_meta["action"] = col_stat.action
            backup_meta["skipped_inc"] = config.skipped_inc
            backup_meta["time_full_bkp"] = backup_chain.fullset.time
            backup_meta["time_full_bkp_str"] = dup_time.timetostring(backup_meta["time_full_bkp"])
            backup_meta["no_of_inc"] = len(backup_chain.incset_list)
            backup_meta["concurrency"] = fail_save_read(config, "concurrency")
            backup_meta["target"] = fail_save_read(config, "target_url")
            backup_meta["source"] = fail_save_read(config, "source_path")
            backup_meta["local_json_stat"] = [
                fail_save_read(
                    backup_chain,
                    "fullset",
                    "local_jsonstat_path",
                    "get_filename",
                    is_function=True,
                )
            ]
            for inc in backup_chain.incset_list:
                backup_meta["local_json_stat"].append(
                    fail_save_read(inc, "local_jsonstat_path", "get_filename", is_function=True)
                )
            py_obj["backup_meta"] = backup_meta

        return json.dumps(py_obj, cls=util.BytesEncoder, indent=4)

    def get_stats_logstring(self, title):
        """Like get_stats_string, but add header and footer"""
        header = f"--------------[ {title} ]--------------"
        footer = "-" * len(header)
        return f"{header}\n{self.get_stats_string()}{footer}\n"

    def set_stats_from_string(self, s):
        """Initialize attributes from string, return self for convenience"""

        def error(line):
            raise StatsException(f"Bad line '{line}'")

        for line in s.split("\n"):
            if not line:
                continue
            line_parts = line.split()
            if len(line_parts) < 2:
                error(line)
            attr, value_string = line_parts[:2]
            if attr not in self.stat_attrs:
                error(line)
            try:
                try:
                    val1 = int(value_string)
                except ValueError:
                    val1 = None
                val2 = float(value_string)
                if val1 == val2:
                    self.set_stat(attr, val1)  # use integer val
                else:
                    self.set_stat(attr, val2)  # use float
            except ValueError:
                error(line)
        return self

    def write_stats_to_path(self, path):
        """Write statistics string to given path"""
        fin = path.open("w")
        fin.write(self.get_stats_string())
        assert not fin.close()

    def read_stats_from_path(self, path):
        """Set statistics from path, return self for convenience"""
        fp = path.open("r")
        self.set_stats_from_string(fp.read())
        assert not fp.close()
        return self

    def stats_equal(self, s):
        """Return true if s has same statistics as self"""
        assert isinstance(s, StatsObj)
        for attr in self.stat_file_attrs:
            if self.get_stat(attr) != s.get_stat(attr):
                return None
        return 1

    def set_to_average(self, statobj_list):
        """Set self's attributes to average of those in statobj_list"""
        for attr in self.stat_attrs:
            self.set_stat(attr, 0)
        for statobj in statobj_list:
            for attr in self.stat_attrs:
                if statobj.get_stat(attr) is None:
                    self.set_stat(attr, None)
                elif self.get_stat(attr) is not None:
                    self.set_stat(attr, statobj.get_stat(attr) + self.get_stat(attr))

        # Don't compute average starting/stopping time
        self.StartTime = None
        self.EndTime = None

        for attr in self.stat_attrs:
            if self.get_stat(attr) is not None:
                self.set_stat(attr, self.get_stat(attr) / float(len(statobj_list)))
        return self

    def get_statsobj_copy(self):
        """Return new StatsObj object with same stats as self"""
        s = StatsObj()
        for attr in self.stat_attrs:
            s.set_stat(attr, self.get_stat(attr))
        return s


class StatsDeltaProcess(StatsObj):
    """Keep track of statistics during DirDelta process"""

    def __init__(self):
        """StatsDeltaProcess initializer - zero file attributes"""
        StatsObj.__init__(self)
        for attr in StatsObj.stat_file_attrs:
            self.__dict__[attr] = 0
        self.Errors = 0
        self.StartTime = time.time()
        self.files_changed = []

    def add_new_file(self, path):
        """Add stats of new file path to statistics"""
        filesize = path.getsize()
        self.SourceFiles += 1
        # SourceFileSize is added-to incrementally as read
        self.NewFiles += 1
        self.NewFileSize += filesize
        self.DeltaEntries += 1
        self.add_delta_entries_file(path, b"new")

    def add_changed_file(self, path):
        """Add stats of file that has changed since last backup"""
        filesize = path.getsize()
        self.SourceFiles += 1
        # SourceFileSize is added-to incrementally as read
        self.ChangedFiles += 1
        self.ChangedFileSize += filesize
        self.DeltaEntries += 1
        self.add_delta_entries_file(path, b"changed")

    def add_deleted_file(self, path):
        """Add stats of file no longer in source directory"""
        self.DeletedFiles += 1  # can't add size since not available
        self.DeltaEntries += 1
        self.add_delta_entries_file(path, b"deleted")

    def add_unchanged_file(self, path):
        """Add stats of file that hasn't changed since last backup"""
        filesize = path.getsize()
        self.SourceFiles += 1
        self.SourceFileSize += filesize

    def close(self):
        """End collection of data, set EndTime"""
        self.EndTime = time.time()

    def add_delta_entries_file(self, path, action_type):
        if config.files_changed and path.isreg():
            self.files_changed.append((path.get_relative_path(), action_type))

    def get_delta_entries_file(self):
        return self.files_changed
