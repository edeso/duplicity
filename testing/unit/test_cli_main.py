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

from duplicity import cli_main
from duplicity import config
from duplicity import errors
from duplicity import gpg
from duplicity import log
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
        u"source_path": u"foo/bar",
        u"source_url": u"file://duptest",
        u"target_dir": u"foo/bar",
        u"target_url": u"file://duptest",
    }

    def setUp(self):
        super().setUp()
        config.gpg_profile = gpg.GPGProfile()
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
            self.assertTrue(config.source_path.endswith(u"foo/bar"))
            self.assertEqual(config.target_url, u"file://duptest")

        for cmd in [u"incremental"] + cli_main.CommandAliases.incremental:
            cli_main.process_command_line(f"{cmd} foo/bar file://duptest".split())
            self.assertEqual(config.action, u"inc")
            self.assertTrue(config.source_path.endswith(u"foo/bar"))
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
            self.assertTrue(config.source_path.endswith(u"foo/bar"))
            self.assertEqual(config.target_url, u"file://duptest")

        for cmd in [u"verify"] + cli_main.CommandAliases.verify:
            cli_main.process_command_line(f"{cmd} file://duptest foo/bar".split())
            self.assertEqual(config.action, u"verify")
            self.assertTrue(config.source_path.endswith(u"foo/bar"))
            self.assertEqual(config.target_url, u"file://duptest")

    @pytest.mark.usefixtures(u"redirect_stdin")
    def test_full_command_errors_reversed_args(self):
        u"""
        test backup, restore, verify with explicit commands - reversed arg
        """
        new_args = {
            u"source_path": u"file://duptest",
            u"source_url": u"foo/bar",
            u"target_dir": u"file://duptest",
            u"target_url": u"foo/bar",
        }
        err_msg = u"should be url|should be pathname"
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
    def test_option_aliases(self):
        u"""
        test short option aliases
        """
        cline = u"back foo/bar file:///target_url -v 9".split()
        cli_main.process_command_line(cline)
        self.assertEqual(config.verbosity, 9)

        cline = u"rest file:///source_url foo/bar -t 10000".split()
        cli_main.process_command_line(cline)
        self.assertEqual(config.restore_time, 10000)

        cline = u"rest file:///source_url foo/bar --time 10000".split()
        cli_main.process_command_line(cline)
        self.assertEqual(config.restore_time, 10000)

    @pytest.mark.usefixtures(u"redirect_stdin")
    def test_encryption_options(self):
        u"""
        test short option aliases
        """
        start = u"back foo/bar file:///target_url "
        keys = (
            u"DEADDEAD",
            u"DEADDEADDEADDEAD",
            u"DEADDEADDEADDEADDEADDEADDEADDEADDEADDEAD",
        )
        opts = (

        )

        for key in keys:
            cline = f"{start} --encrypt-key={key}".split()
            cli_main.process_command_line(cline)
            self.assertEqual(config.gpg_profile.recipients, [key])

            cline = f"{start} --hidden-encrypt-key={key}".split()
            cli_main.process_command_line(cline)
            self.assertEqual(config.gpg_profile.hidden_recipients, [key])

            cline = f"{start} --sign-key={key}".split()
            cli_main.process_command_line(cline)
            self.assertEqual(config.gpg_profile.sign_key, key)

    @pytest.mark.usefixtures(u"redirect_stdin")
    def test_bad_encryption_options(self):
        u"""
        test short option aliases
        """
        start = u"back foo/bar file:///target_url "
        keys = (
            u"DEADFOO",
            u"DEADDEADDEADFOO",
            u"DEADDEADDEADDEADDEADDEADDEADDEADDEADFOO",
        )

        for key in keys:
            with self.assertRaises(CommandLineError) as cm:
                cline = f"{start} --encrypt-key={key}".split()
                cli_main.process_command_line(cline)

            with self.assertRaises(CommandLineError) as cm:
                cline = f"{start} --hidden-encrypt-key={key}".split()
                cli_main.process_command_line(cline)

            with self.assertRaises(CommandLineError) as cm:
                cline = f"{start} --sign-key={key}".split()
                cli_main.process_command_line(cline)

    @pytest.mark.usefixtures(u"redirect_stdin")
    def test_deprecated_options(self):
        u"""
        test short option aliases
        """
        start = u"back foo/bar file:///target_url "
        opts = (
            u"--gio",
            u"--old-filenames",
            u"--short-filenames",
            u"--exclude-globbing-filelist",
            u"--include-globbing-filelist",
            u"--exclude-filelist-stdin",
            u"--include-filelist-stdin",
        )

        for opt in opts:
            with self.assertLogs(logger=log._logger, level=log.DupToLoggerLevel(log.ERROR)) as cm:
                cline = f"{start} {opt}".split()
                cli_main.process_command_line(cline)
