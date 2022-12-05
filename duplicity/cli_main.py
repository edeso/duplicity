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

import gpg
import sys

from duplicity import errors
from duplicity.cli_data import *
from duplicity.cli_util import *

# TODO: move to config
select_opts = []  # Will hold all the selection options
select_files = []  # Will hold file objects when filelist given


class CommandLineError(errors.UserError):
    pass


def command_line_error(message):
    u"""Indicate a command line error and exit"""
    raise CommandLineError(_(f"Command line error: {message}\n") +
                           _(u"Enter 'duplicity --help' for help screen."))


class DuplicityHelpFormatter(argparse.ArgumentDefaultsHelpFormatter,
                             argparse.RawDescriptionHelpFormatter):
    u"""
    A working class to combine ArgumentDefaults, RawDescription.
    Use with make_wide() to insure we catch argparse API changes.
    """


def make_wide(formatter, w=120, h=46):
    """
    Return a wider HelpFormatter, if possible.
    """
    try:
        # see: https://stackoverflow.com/a/5464440
        # beware: "Only the name of this class is considered a public API."
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
        names = option_alternates.get(var, []) + [var]
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
            cmd,
            action=u"store_true",
            default=d(getattr(config, var)))
        for arg in meta:
            subparser_dict[cmd].add_argument(arg, type=str)

        # add valid options for each command
        for opt in sorted(CommandOptions.__dict__[var]):
            names = option_alternates.get(opt, []) + [opt]
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
    u"""Process command line, set config, return action

    action will be "list-current", "collection-status", "cleanup",
    "remove-old", "restore", "verify", "full", or "inc".

    """
    # build initial gpg_profile
    config.gpg_profile = gpg.GPGProfile()

    # parse command line
    args = parse_cmdline_options(cmdline_list)

    # # process first arg as possible command
    # if args:
    #     cmd = args.pop(0)
    #     # look for possible abbreviations
    #     possible = [c for c in duplicity_commands.keys() if c.startswith(cmd)]
    #     # no unique match, that's an error
    #     if len(possible) > 1:
    #         command_line_error(f"command '{cmd}' not unique: could be {' or '.join(possible)}")
    #     # only one match, that's a keeper, maybe
    #     elif len(possible) == 1:
    #         cmd = possible[0]
    #         if cmd not in duplicity_commands.keys():
    #             command_line_error(f"command '{cmd}' is not a duplicity command.")
    #     # no matches, assume implied cmd
    #     elif not possible:
    #         args.insert(0, cmd)
    #         cmd = u"implied"
    #         duplicity_commands[cmd] = [u"defer", u"defer"]
    #
    # # duplicity_commands just need standard checks
    # cmdvar = cmd.replace(u'-', u'_')
    # setattr(config, cmdvar, args)
    # num_expect = len(duplicity_commands[cmd])
    # if len(args) != num_expect:
    #     command_line_error(f"Expected {num_expect} args, got {len(args)}.")
    #
    # targets = duplicity_commands[cmd]
    # for n in range(len(targets)):
    #     if targets[n] != u"defer":
    #         name = f"check_{targets[n]}"
    #         func = getattr(cli_main, name)
    #         setattr(config, targets[n], func(args[n]))
    #
    # # other duplicity_commands need added processing
    # if cmd == u"remove-all-but-n-full":
    #     config.remove_all_but_n_full_mode = True
    #     arg = args[0]
    #     config.keep_chains = int(arg)
    #     if not config.keep_chains > 0:
    #         command_line_error(cmd + u" count must be > 0")
    #
    # elif cmd == u"remove-all-inc-of-but-n-full":
    #     config.remove_all_inc_of_but_n_full_mode = True
    #     arg = args[0]
    #     config.keep_chains = int(arg)
    #     if not config.keep_chains > 0:
    #         command_line_error(cmd + u" count must be > 0")
    #
    # backend_url = config.target_url or config.source_url
    # if config.backup_name is None:
    #     config.backup_name = generate_default_backup_name(backend_url)
    #
    # # convert file_prefix* string
    # if isinstance(config.file_prefix, str):
    #     config.file_prefix = bytes(config.file_prefix, u'utf-8')
    # if isinstance(config.file_prefix_manifest, str):
    #     config.file_prefix_manifest = bytes(config.file_prefix_manifest, u'utf-8')
    # if isinstance(config.file_prefix_archive, str):
    #     config.file_prefix_archive = bytes(config.file_prefix_archive, u'utf-8')
    # if isinstance(config.file_prefix_signature, str):
    #     config.file_prefix_signature = bytes(config.file_prefix_signature, u'utf-8')
    #
    # # set and expand archive dir
    # set_archive_dir(expand_archive_dir(config.archive_dir,
    #                                    config.backup_name))
    #
    # log.Info(_(u"Using archive dir: %s") % (config.archive_dir_path.uc_name,))
    # log.Info(_(u"Using backup name: %s") % (config.backup_name,))
    #
    # # if we get a different gpg-binary from the commandline then redo gpg_profile
    # if config.gpg_binary is not None:
    #     src = config.gpg_profile
    #     config.gpg_profile = gpg.GPGProfile(
    #         passphrase=src.passphrase,
    #         sign_key=src.sign_key,
    #         recipients=src.recipients,
    #         hidden_recipients=src.hidden_recipients)
    # log.Debug(_(u"GPG binary is %s, version %s") %
    #           ((config.gpg_binary or u'gpg'), config.gpg_profile.gpg_version))
    #
    # # we can now try to import all the backends
    # backend.import_backends()
    #
    # # parse_cmdline_options already verified that we got exactly 1 or 2
    # # positional arguments.  Convert to action
    # if len(args) == 1:
    #     if list_current:
    #         action = u"list-current"
    #     elif collection_status:
    #         action = u"collection-status"
    #     elif cleanup:
    #         action = u"cleanup"
    #     elif config.remove_time is not None:
    #         action = u"remove-old"
    #     elif config.remove_all_but_n_full_mode:
    #         action = u"remove-all-but-n-full"
    #     elif config.remove_all_inc_of_but_n_full_mode:
    #         action = u"remove-all-inc-of-but-n-full"
    #     else:
    #         command_line_error(u"Too few arguments")
    #
    #     config.backend = backend.get_backend(args[0])
    #     if not config.backend:
    #         command_line_error(_(f"Bad URL '{args[0]})'.\n"
    #                              "Examples of URL strings are 'scp://user@host.net:1234/path' and\n"
    #                              "'file:///usr/local'.  See the man page for more information."""))
    # elif len(args) == 2:
    #     # Figure out whether backup or restore
    #     backup, local_pathname = set_backend(args[0], args[1])
    #     if backup:
    #         if full_backup:
    #             action = u"full"
    #         else:
    #             action = u"inc"
    #     else:
    #         if verify:
    #             action = u"verify"
    #         else:
    #             action = u"restore"
    #
    #     process_local_dir(action, local_pathname)
    #     if action in [u'full', u'inc', u'verify']:
    #         set_selection()
    #
    # check_consistency(action)
    #

    log.Info(_(u"Main action: ") + action)
    return action


if __name__ == u"__main__":
    log.setup()
    args = process_command_line(sys.argv[1:])
    print(args, argparse.Namespace)
