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

import copy
import os
import sys

from duplicity import errors
from duplicity import log
from duplicity import cli_main
from duplicity import config
from testing.unit import UnitTestCase


class CommandlineTest(UnitTestCase):
    u"""
    Test parse_commandline_options
    """
    good_args = {
        u"count": u"5",
        u"remove_time": u"100",
        u"source_dir": u"foo/bar",
        u"source_url": u"file://duptest",
        u"target_dir": u"foo/bar",
        u"target_url": u"file://duptest",
    }

    def setUp(self):
        log.setup()
        os.makedirs(u"foo/bar", exist_ok=True)

    def tearDown(self):
        log.shutdown()
        os.removedirs(u"foo/bar")

    def run_all_commands_with_errors(self, new_args, err_msg):
        u"""
        Test all commands with the supplied argument list.
        Only test command if new_args contains needed arg.
        """
        test_args = copy.copy(self.good_args)
        test_args.update(new_args)
        for cmd in cli_main.commands:
            runtest = False
            args = cli_main.commands[cmd]
            cline = [cmd]
            for arg in args:
                cline.append(test_args[arg])
                if arg in new_args:
                    runtest = True
            if runtest:
                with self.assertRaisesRegex(cli_main.CommandLineError, err_msg) as cm:
                    cli_main.parse_cmdline_options(cline)

    def test_full_commands(self):
        u"""
        test backup, restore, verify with explicit commands
        """

        cli_main.parse_cmdline_options(u"cleanup file://duptest".split())
        assert config.cleanup
        assert config.target_url == u"file://duptest"

        cli_main.parse_cmdline_options(u"collection-status file://duptest".split())
        assert config.collection_status
        assert config.target_url == u"file://duptest"

        cli_main.parse_cmdline_options(u"full foo/bar file://duptest".split())
        assert config.full
        assert config.source_dir.endswith(u"foo/bar")
        assert config.target_url == u"file://duptest"

        cli_main.parse_cmdline_options(u"inc foo/bar file://duptest".split())
        assert config.incremental
        assert config.source_dir.endswith(u"foo/bar")
        assert config.target_url == u"file://duptest"

        cli_main.parse_cmdline_options(u"list-current-files file://duptest".split())
        assert config.list_current_files
        assert config.target_url == u"file://duptest"

        cli_main.parse_cmdline_options(u"remove-all-but-n-full 5 file://duptest".split())
        assert config.remove_all_but_n_full
        assert config.target_url == u"file://duptest"

        cli_main.parse_cmdline_options(u"remove-all-inc-of-but-n-full 5 file://duptest".split())
        assert config.remove_all_inc_of_but_n_full
        assert config.target_url == u"file://duptest"

        cli_main.parse_cmdline_options(u"remove-older-than 100 file://duptest".split())
        assert config.remove_older_than
        assert config.target_url == u"file://duptest"

        cli_main.parse_cmdline_options(u"restore file://duptest foo/bar".split())
        assert config.restore
        assert config.source_dir.endswith(u"foo/bar")
        assert config.target_url == u"file://duptest"

        cli_main.parse_cmdline_options(u"verify file://duptest foo/bar".split())
        assert config.verify
        assert config.source_dir.endswith(u"foo/bar")
        assert config.target_url == u"file://duptest"

    def test_implied_commands(self):
        u"""
        test backup, restore, verify without explicit commands
        """
        cli_main.parse_cmdline_options(u"foo/bar file://duptest".split())
        assert config.full
        assert config.source_dir.endswith(u"foo/bar")
        assert config.target_url == u"file://duptest"

        cli_main.parse_cmdline_options(u"file://duptest foo/bar".split())
        assert config.restore
        assert config.source_dir.endswith(u"foo/bar")
        assert config.target_url == u"file://duptest"

    def test_full_command_errors_reversed_args(self):
        u"""
        test backup, restore, verify with explicit commands - reversed arg
        """
        new_args = {
            u"source_dir": u"file://duptest",
            u"source_url": u"foo/bar",
            u"target_dir": u"file://duptest",
            u"target_url": u"foo/bar",
        }
        err_msg = u"should be url|should be directory"
        self.run_all_commands_with_errors(new_args, err_msg)

    def test_full_command_errors_bad_url(self):
        u"""
        test backup, restore, verify with explicit commands - bad url
        """
        new_args = {
            u"source_url": u"file:/duptest",
            u"target_url": u"file:/duptest",
        }
        err_msg = u"should be url"
        self.run_all_commands_with_errors(new_args, err_msg)

    def test_full_command_errors_bad_filename(self):
        u"""
        test backup, restore, verify with explicit commands - bad filename
        """
        new_args = {
            u"source_dir": u"fi:l*e/p\"a?t>h|.t<xt",
            u"target_dir": u"fi:l*e/p\"a?t>h|.t<xt",
        }
        err_msg = u"not a valid file path"
        self.run_all_commands_with_errors(new_args, err_msg)

    def test_full_command_errors_bad_integer(self):
        u"""
        test backup, restore, verify with explicit commands - bad integer
        """
        new_args = {
            u"count": u"foo",
        }
        err_msg = u"not an int"
        self.run_all_commands_with_errors(new_args, err_msg)

    def test_full_command_errors_bad_time_string(self):
        u"""
        test backup, restore, verify with explicit commands - bad time string
        """
        new_args = {
            u"remove_time": u"foo",
        }
        err_msg = u"Bad time string"
        self.run_all_commands_with_errors(new_args, err_msg)
