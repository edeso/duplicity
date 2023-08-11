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

import argparse
import copy
import os
import shlex
import unittest

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


@unittest.skipIf(os.environ.get("USER", "") == "buildd", "Skip test on Launchpad")
class CommandlineTest(UnitTestCase):
    """
    Test parse_commandline_options
    """
    good_args = {
        "count": "5",
        "remove_time": "100",
        "source_path": "foo/bar",
        "source_url": "file://duptest",
        "target_dir": "foo/bar",
        "target_url": "file://duptest",
    }

    def setUp(self):
        super().setUp()
        config.gpg_profile = gpg.GPGProfile()
        os.makedirs("foo/bar", exist_ok=True)

    def tearDown(self):
        log.shutdown()
        os.removedirs("foo/bar")

    def run_all_commands_with_errors(self, new_args, err_msg):
        """
        Test all commands with the supplied argument list.
        Only test command if new_args contains needed arg.
        """
        test_args = copy.copy(self.good_args)
        test_args.update(new_args)
        for var in DuplicityCommands.__dict__.keys():
            if var.startswith("__"):
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

    @pytest.mark.usefixtures("redirect_stdin")
    def test_full_command(self):
        """
        test backup, restore, verify with explicit commands
        """
        for cmd in ["cleanup"] + cli_main.CommandAliases.cleanup:
            cli_main.process_command_line(f"{cmd} file://duptest".split())
            self.assertEqual(config.action, "cleanup")
            self.assertEqual(config.target_url, "file://duptest")

        for cmd in ["collection-status"] + cli_main.CommandAliases.collection_status:
            cli_main.process_command_line(f"{cmd} file://duptest".split())
            self.assertEqual(config.action, "collection-status")
            self.assertEqual(config.target_url, "file://duptest")

        for cmd in ["full"] + cli_main.CommandAliases.full:
            cli_main.process_command_line(f"{cmd} foo/bar file://duptest".split())
            self.assertEqual(config.action, "full")
            self.assertTrue(config.source_path.endswith("foo/bar"))
            self.assertEqual(config.target_url, "file://duptest")

        for cmd in ["incremental"] + cli_main.CommandAliases.incremental:
            cli_main.process_command_line(f"{cmd} foo/bar file://duptest".split())
            self.assertEqual(config.action, "inc")
            self.assertTrue(config.source_path.endswith("foo/bar"))
            self.assertEqual(config.target_url, "file://duptest")

        for cmd in ["list-current-files"] + cli_main.CommandAliases.list_current_files:
            cli_main.process_command_line(f"{cmd} file://duptest".split())
            self.assertEqual(config.action, "list-current-files")
            self.assertEqual(config.target_url, "file://duptest")

        for cmd in ["remove-all-but-n-full"] + cli_main.CommandAliases.remove_all_but_n_full:
            cli_main.process_command_line(f"{cmd} 5 file://duptest".split())
            self.assertEqual(config.action, "remove-all-but-n-full")
            self.assertEqual(config.target_url, "file://duptest")

        for cmd in ["remove-all-inc-of-but-n-full"] + cli_main.CommandAliases.remove_all_inc_of_but_n_full:
            cli_main.process_command_line(f"{cmd} 5 file://duptest".split())
            self.assertEqual(config.action, "remove-all-inc-of-but-n-full")
            self.assertEqual(config.target_url, "file://duptest")

        for cmd in ["remove-older-than"] + cli_main.CommandAliases.remove_older_than:
            cli_main.process_command_line(f"{cmd} 100 file://duptest".split())
            self.assertEqual(config.action, "remove-older-than")
            self.assertEqual(config.target_url, "file://duptest")

        for cmd in ["restore"] + cli_main.CommandAliases.restore:
            cli_main.process_command_line(f"{cmd} file://duptest foo/bar".split())
            self.assertEqual(config.action, "restore")
            self.assertTrue(config.source_path.endswith("foo/bar"))
            self.assertEqual(config.target_url, "file://duptest")

        for cmd in ["verify"] + cli_main.CommandAliases.verify:
            cli_main.process_command_line(f"{cmd} file://duptest foo/bar".split())
            self.assertEqual(config.action, "verify")
            self.assertTrue(config.source_path.endswith("foo/bar"))
            self.assertEqual(config.target_url, "file://duptest")

    @pytest.mark.usefixtures("redirect_stdin")
    def test_full_command_errors_reversed_args(self):
        """
        test backup, restore, verify with explicit commands - reversed arg
        """
        new_args = {
            "source_path": "file://duptest",
            "source_url": "foo/bar",
            "target_dir": "file://duptest",
            "target_url": "foo/bar",
        }
        err_msg = "should be url|should be pathname"
        self.run_all_commands_with_errors(new_args, err_msg)

    @pytest.mark.usefixtures("redirect_stdin")
    def test_full_command_errors_bad_url(self):
        """
        test backup, restore, verify with explicit commands - bad url
        """
        new_args = {
            "source_url": "file:/duptest",
            "target_url": "file:/duptest",
        }
        err_msg = "should be url"
        self.run_all_commands_with_errors(new_args, err_msg)

    @pytest.mark.usefixtures("redirect_stdin")
    def test_full_command_errors_bad_integer(self):
        """
        test backup, restore, verify with explicit commands - bad integer
        """
        new_args = {
            "count": "foo",
        }
        err_msg = "not an int"
        self.run_all_commands_with_errors(new_args, err_msg)

    @pytest.mark.usefixtures("redirect_stdin")
    def test_full_command_errors_bad_time_string(self):
        """
        test backup, restore, verify with explicit commands - bad time string
        """
        new_args = {
            "remove_time": "foo",
        }
        err_msg = "Bad time string"
        self.run_all_commands_with_errors(new_args, err_msg)

    @pytest.mark.usefixtures("redirect_stdin")
    def test_option_aliases(self):
        """
        test short option aliases
        """
        cline = "ib foo/bar file:///target_url -v 9".split()
        cli_main.process_command_line(cline)
        self.assertEqual(config.verbosity, 9)

        cline = "rb file:///source_url foo/bar -t 10000".split()
        cli_main.process_command_line(cline)
        self.assertEqual(config.restore_time, 10000)

        cline = "rb file:///source_url foo/bar --time 10000".split()
        cli_main.process_command_line(cline)
        self.assertEqual(config.restore_time, 10000)

    @pytest.mark.usefixtures("redirect_stdin")
    def test_encryption_options(self):
        """
        test encrypt/sign key handling
        """
        start = "ib foo/bar file:///target_url "
        keys = (
            "DEADDEAD",
            "DEADDEADDEADDEAD",
            "DEADDEADDEADDEADDEADDEADDEADDEADDEADDEAD",
        )

        for key in keys:
            cline = f"{start} --encrypt-key={key}".split()
            cli_main.process_command_line(cline)
            self.assertEqual(config.gpg_profile.recipients, [key])

            cline = f"{start} --encrypt-sign-key={key}".split()
            cli_main.process_command_line(cline)
            self.assertEqual(config.gpg_profile.recipients, [key])
            self.assertEqual(config.gpg_profile.sign_key, key)

            cline = f"{start} --hidden-encrypt-key={key}".split()
            cli_main.process_command_line(cline)
            self.assertEqual(config.gpg_profile.hidden_recipients, [key])

            cline = f"{start} --sign-key={key}".split()
            cli_main.process_command_line(cline)
            self.assertEqual(config.gpg_profile.sign_key, key)

    @pytest.mark.usefixtures("redirect_stdin")
    def test_bad_encryption_options(self):
        """
        test short option aliases
        """
        start = "inc foo/bar file:///target_url "
        keys = (
            "DEADFOO",
            "DEADDEADDEADFOO",
            "DEADDEADDEADDEADDEADDEADDEADDEADDEADFOO",
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

    # @pytest.mark.usefixtures("redirect_stdin")
    # def test_implied_commands(self):
    #     """
    #     test implied commands
    #     """
    #     cline = "foo/bar file:///target_url".split()
    #     cli_main.process_command_line(cline)
    #     self.assertEqual(config.action, "inc")
    #
    #     cline = "file:///source_url foo/bar".split()
    #     cli_main.process_command_line(cline)
    #     self.assertEqual(config.action, "restore")

    @pytest.mark.usefixtures("redirect_stdin")
    def test_integer_args(self):
        """
        test implied commands
        """
        cline = "inc foo/bar file:///target_url --copy-blocksize=1024 --volsize=1024".split()
        cli_main.process_command_line(cline)
        self.assertEqual(config.copy_blocksize, 1024 * 1024)
        self.assertEqual(config.volsize, 1024 * 1024 * 1024)

        with self.assertRaises(CommandLineError) as cm:
            cline = "inc foo/bar file:///target_url --copy-blocksize=foo --volsize=1024".split()
            cli_main.process_command_line(cline)

        with self.assertRaises(CommandLineError) as cm:
            cline = "inc foo/bar file:///target_url --copy-blocksize=1024 --volsize=foo".split()
            cli_main.process_command_line(cline)

    @pytest.mark.usefixtures("redirect_stdin")
    def test_bad_command(self):
        """
        test bad commands
        """
        with self.assertRaises(SystemExit) as cm:
            cline = "fbx foo/bar file:///target_url".split()
            cli_main.process_command_line(cline)

        with self.assertRaises(SystemExit) as cm:
            cline = "rbx file:///target_url foo/bar".split()
            cli_main.process_command_line(cline)

    @pytest.mark.usefixtures("redirect_stdin")
    def test_too_many_positionals(self):
        """
        test bad commands
        """
        with self.assertRaises(SystemExit) as cm:
            cline = "fb foo/bar file:///target_url extra".split()
            cli_main.process_command_line(cline)

        with self.assertRaises(SystemExit) as cm:
            cline = "rb file:///target_url foo/bar extra".split()
            cli_main.process_command_line(cline)

    @pytest.mark.usefixtures("redirect_stdin")
    def test_list_commands(self):
        """
        test list commands like ssh_options, etc.
        """
        cline = shlex.split("inc foo/bar file:///target_url --ssh-options=\'--foo\'")
        cli_main.process_command_line(cline)
        self.assertEqual(config.ssh_options, "--foo")

        cline = shlex.split("inc foo/bar file:///target_url --ssh-options=\'--foo\' --ssh-options=\'--bar\'")
        cli_main.process_command_line(cline)
        self.assertEqual(config.ssh_options, "--foo --bar")

        cline = shlex.split("inc foo/bar file:///target_url --ssh-options=\'--foo --bar\'")
        cli_main.process_command_line(cline)
        self.assertEqual(config.ssh_options, "--foo --bar")
