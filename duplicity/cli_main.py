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

u"""Parse command line, check for consistency, and set config"""

import sys

import duplicity
from duplicity import gpg
from duplicity.cli_data import *
from duplicity.cli_util import *


class DuplicityHelpFormatter(argparse.ArgumentDefaultsHelpFormatter,
                             argparse.RawDescriptionHelpFormatter):
    u"""
    A working class to combine ArgumentDefaults, RawDescription.
    Use with make_wide() to insure we catch argparse API changes.
    """


def make_wide(formatter, w=120, h=46):
    """
    Return a wider HelpFormatter, if possible.
    See: https://stackoverflow.com/a/5464440
    Beware: "Only the name of this class is considered a public API."
    """
    try:
        kwargs = {'width': w, 'max_help_position': h}
        formatter(None, **kwargs)
        return lambda prog: formatter(prog, **kwargs)
    except TypeError:
        warnings.warn("argparse help formatter failed, falling back.")
        return formatter


def parse_cmdline_options(arglist):
    u"""
    Parse argument list
    """
    # set up parent parser
    parser = argparse.ArgumentParser(
        prog=u'duplicity',
        argument_default=None,
        formatter_class=make_wide(DuplicityHelpFormatter),
        epilog=help_url_formats,
    )
    for var in parent_options:
        names = OptionAliases.__dict__.get(var, []) + [var]
        names = [var2opt(n) for n in names]
        parser.add_argument(*names, **OptionKwargs.__dict__[var])

    # set up command subparsers
    subparsers = parser.add_subparsers(
        title=u"valid ommands",
        required=False,
    )

    # add sub_parser for each command
    subparser_dict = dict()
    for var, meta in sorted(DuplicityCommands.__dict__.items()):
        if var.startswith(u"__"):
            continue
        cmd = var2cmd(var)
        subparser_dict[cmd] = subparsers.add_parser(
            cmd,
            aliases=CommandAliases.__dict__[var],
            help=f"# duplicity {var} {u' '.join(meta)}",
            formatter_class=make_wide(DuplicityHelpFormatter),
            epilog=help_url_formats,
        )
        subparser_dict[cmd].add_argument(
            u"action",
            action=u"store_const",
            const=cmd)
        for arg in meta:
            func = getattr(duplicity.cli_util, f"check_{arg}")
            subparser_dict[cmd].add_argument(arg, type=func)

        # add valid options for each command
        for opt in sorted(CommandOptions.__dict__[var]):
            names = OptionAliases.__dict__.get(opt, []) + [opt]
            names = [var2opt(n) for n in names]
            subparser_dict[cmd].add_argument(*names, **OptionKwargs.__dict__[opt])

    # parse the options
    args = parser.parse_args(arglist)

    # Copy all arguments and their values to the config module.  Don't copy
    # attributes that are 'hidden' (start with an underscore) or whose name is
    # the empty string (used for arguments that don't directly store a value
    # by using dest="")
    for f in [x for x in dir(args) if x and not x.startswith(u"_")]:
        v = getattr(args, f)
        setattr(config, f, v)

    return args


def process_command_line(cmdline_list):
    u"""
    Process command line, set config
    """
    # parse command line
    args = parse_cmdline_options(cmdline_list)

    # Set to GPGProfile that will be used to compress/uncompress encrypted
    # files.  Replaces encryption_keys, sign_key, and passphrase settings.
    config.gpg_profile = gpg.GPGProfile()

    return args


if __name__ == u"__main__":
    log.setup()
    args = process_command_line(sys.argv[1:])
    for a, v in sorted(args.__dict__.items()):
        print(f"{a} = {v}")
