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
import pytest
import sys

from duplicity import errors
from duplicity import log
from duplicity import cli_main
from duplicity import config
from duplicity.cli_data import *
from duplicity.cli_util import *
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
        for var in DuplicityCommands.__dict__.keys():
            if var.startswith(u"__"):
                continue
            cmd = var2cmd(var)
            runtest = False
            args = DuplicityCommands.__dict__[var]
            cline = [cmd]
            for arg in args:
                cline.append(test_args[arg])
                if arg in new_args:
                    runtest = True
            if runtest:
                with self.assertRaisesRegex(cli_main.CommandLineError, err_msg) as cm:
                    cli_main.process_command_line(cline)

    @pytest.mark.usefixtures(u"redirect_stdin")
    def test_full_command(self):
        u"""
        test backup, restore, verify with explicit commands
        """
        for cmd in [u"cleanup"] + cli_main.CommandAliases.cleanup:
            cli_main.process_command_line(f"{cmd} file://duptest".split())
            self.assertEqual(config.action, u"cleanup")
            self.assertEqual(config.target_url, u"file://duptest")

        for cmd in [u"collection-status"] + cli_main.CommandAliases.collection_status:
            cli_main.process_command_line(f"{cmd} file://duptest".split())
            self.assertEqual(config.action, u"collection-status")
            self.assertEqual(config.target_url, u"file://duptest")

        for cmd in [u"full"] + cli_main.CommandAliases.full:
            cli_main.process_command_line(f"{cmd} foo/bar file://duptest".split())
            self.assertEqual(config.action, u"full")
            self.assertTrue(config.source_dir.endswith(u"foo/bar"))
            self.assertEqual(config.target_url, u"file://duptest")

        for cmd in [u"incremental"] + cli_main.CommandAliases.incremental:
            cli_main.process_command_line(f"{cmd} foo/bar file://duptest".split())
            self.assertEqual(config.action, u"incremental")
            self.assertTrue(config.source_dir.endswith(u"foo/bar"))
            self.assertEqual(config.target_url, u"file://duptest")

        for cmd in [u"list-current-files"] + cli_main.CommandAliases.list_current_files:
            cli_main.process_command_line(f"{cmd} file://duptest".split())
            self.assertEqual(config.action, u"list-current-files")
            self.assertEqual(config.target_url, u"file://duptest")

        for cmd in [u"remove-all-but-n-full"] + cli_main.CommandAliases.remove_all_but_n_full:
            cli_main.process_command_line(f"{cmd} 5 file://duptest".split())
            self.assertEqual(config.action, u"remove-all-but-n-full")
            self.assertEqual(config.target_url, u"file://duptest")

        for cmd in [u"remove-all-inc-of-but-n-full"] + cli_main.CommandAliases.remove_all_inc_of_but_n_full:
            cli_main.process_command_line(f"{cmd} 5 file://duptest".split())
            self.assertEqual(config.action, u"remove-all-inc-of-but-n-full")
            self.assertEqual(config.target_url, u"file://duptest")

        for cmd in [u"remove-older-than"] + cli_main.CommandAliases.remove_older_than:
            cli_main.process_command_line(f"{cmd} 100 file://duptest".split())
            self.assertEqual(config.action, u"remove-older-than")
            self.assertEqual(config.target_url, u"file://duptest")

        for cmd in [u"restore"] + cli_main.CommandAliases.restore:
            cli_main.process_command_line(f"{cmd} file://duptest foo/bar".split())
            self.assertEqual(config.action, u"restore")
            self.assertTrue(config.source_dir.endswith(u"foo/bar"))
            self.assertEqual(config.target_url, u"file://duptest")

        for cmd in [u"verify"] + cli_main.CommandAliases.verify:
            cli_main.process_command_line(f"{cmd} file://duptest foo/bar".split())
            self.assertEqual(config.action, u"verify")
            self.assertTrue(config.source_dir.endswith(u"foo/bar"))
            self.assertEqual(config.target_url, u"file://duptest")

    @pytest.mark.usefixtures(u"redirect_stdin")
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

    @pytest.mark.usefixtures(u"redirect_stdin")
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

    @pytest.mark.usefixtures(u"redirect_stdin")
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

    @pytest.mark.usefixtures(u"redirect_stdin")
    def test_full_command_errors_bad_integer(self):
        u"""
        test backup, restore, verify with explicit commands - bad integer
        """
        new_args = {
            u"count": u"foo",
        }
        err_msg = u"not an int"
        self.run_all_commands_with_errors(new_args, err_msg)

    @pytest.mark.usefixtures(u"redirect_stdin")
    def test_full_command_errors_bad_time_string(self):
        u"""
        test backup, restore, verify with explicit commands - bad time string
        """
        new_args = {
            u"remove_time": u"foo",
        }
        err_msg = u"Bad time string"
        self.run_all_commands_with_errors(new_args, err_msg)

    @pytest.mark.usefixtures(u"redirect_stdin")
    def test_help_commands(self):
        u"""
        test multi-level help system
        """
        for var in DuplicityCommands.__dict__.keys():
            if var.startswith(u"__"):
                continue
            cmd = var2cmd(var)
            cline = [cmd, u'--help']
            with self.assertRaises(SystemExit) as cm:
                cli_main.process_command_line(cline)
                for opt in sorted(CommandOptions.__dict__[var]):
                    names = OptionAliases.__dict__.get(opt, []) + [opt]
                    names = [var2opt(n) for n in names]
                    for name in names:
                        self.assertIn(name, cm.output)
