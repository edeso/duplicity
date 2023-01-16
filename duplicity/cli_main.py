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
from duplicity import backend
from duplicity import config
from duplicity import gpg
from duplicity import path
from duplicity.cli_data import *
from duplicity.cli_util import *


class DuplicityHelpFormatter(argparse.ArgumentDefaultsHelpFormatter,
                             argparse.RawDescriptionHelpFormatter):
    u"""
    A working class to combine ArgumentDefaults, RawDescription.
    Use with make_wide() to insure we catch argparse API changes.
    """


def make_wide(formatter, w=120, h=46):
    u"""
    Return a wider HelpFormatter, if possible.
    See: https://stackoverflow.com/a/5464440
    Beware: "Only the name of this class is considered a public API."
    """
    try:
        kwargs = {u'width': w, u'max_help_position': h}
        formatter(None, **kwargs)
        return lambda prog: formatter(prog, **kwargs)
    except TypeError:
        warnings.warn(u"argparse help formatter failed, falling back.")
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
        # epilog=help_url_formats,
    )
    for var in parent_only_options:
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
            help=f"# duplicity {var} [options] {u' '.join(meta)}",
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
            if opt.startswith(u"__"):
                continue
            names = OptionAliases.__dict__.get(opt, list())
            names = [var2opt(n) for n in names + [opt]]
            subparser_dict[cmd].add_argument(*names, **OptionKwargs.__dict__[opt])

    # parse the options
    args = parser.parse_args(arglist)

    # if no command, print help
    if not hasattr(args, u"action"):
        parser.print_usage()

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
    # build initial gpg_profile
    config.gpg_profile = gpg.GPGProfile()

    # parse command line
    args = parse_cmdline_options(cmdline_list)
    if not hasattr(args, u"action"):
        sys.exit(1)

    # if we get a different gpg-binary from the commandline then redo gpg_profile
    # TODO: Allow lists of keys not just single key
    if config.gpg_binary is not None:
        src = config.gpg_profile
        config.gpg_profile = gpg.GPGProfile(
            passphrase=src.passphrase,
            sign_key=src.sign_key,
            recipients=src.recipients,
            hidden_recipients=src.hidden_recipients)
    log.Info(_(u"GPG binary is %s, version %s") %
             ((config.gpg_binary or u'gpg'), config.gpg_profile.gpg_version))

    config.action = u"inc" if config.action == u"incremental" else config.action

    backend.import_backends()

    remote_url = config.source_url or config.target_url
    if remote_url:
        config.backend = backend.get_backend(remote_url)
    else:
        config.backend = None

    local_path = config.source_dir or config.target_dir
    if local_path:
        config.local_path = path.Path(path.Path(local_path).get_canonical())
    else:
        config.local_path = None

    if config.backup_name is None:
        config.backup_name = generate_default_backup_name(remote_url)

    set_archive_dir(expand_archive_dir(config.archive_dir,
                                       config.backup_name))

    config.keep_chains = config.count

    config.mp_segment_size = int(config.mp_factor * config.volsize)

    if config.action in [u'full', u'inc', u'verify']:
        set_selection()

    if config.ignore_errors:
        log.Warn(_(u"Running in 'ignore errors' mode due to --ignore-errors.\n"
                   u"Please reconsider if this was not intended"))

    log.Info(_(u"Using archive dir: %s") % (config.archive_dir_path.uc_name,))
    log.Info(_(u"Using backup name: %s") % (config.backup_name,))

    return config.action


if __name__ == u"__main__":
    log.setup()
    args = process_command_line(sys.argv[1:])
    for a, v in sorted(args.__dict__.items()):
        print(f"{a} = {v}")
