# -*- Mode:Python; indent-tabs-mode:nil; tab-width:4; encoding:utf-8 -*-
#
# Copyright 2022 Kenneth Loafman <kenneth@loafman.com>
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

u"""
Utils for parse command line, check for consistency, and set config
"""

import argparse
import io
import os
import re
from hashlib import md5

from duplicity import config
from duplicity import dup_time
from duplicity import errors
from duplicity import log
from duplicity import path
from duplicity import selection

gpg_key_patt = re.compile(u"^(0x)?([0-9A-Fa-f]{8}|[0-9A-Fa-f]{16}|[0-9A-Fa-f]{40})$")


class CommandLineError(errors.UserError):
    pass


def command_line_error(message):
    u"""
    Indicate a command line error and exit
    """
    raise CommandLineError(_(f"{message}\n") +
                           _(u"Enter 'duplicity --help' for help screen."))


class DuplicityAction(argparse.Action):
    def __init__(self, option_strings, dest, **kwargs):
        super().__init__(option_strings, dest, **kwargs)

    def __call__(self, parser, namespace, values, option_string=None):
        raise NotImplementedError


class AddSelectionAction(DuplicityAction):
    def __init__(self, option_strings, dest, **kwargs):
        super().__init__(option_strings, dest, **kwargs)

    def __call__(self, parser, namespace, values, option_string=None):
        addarg = os.fsdecode(value) if isinstance(values, bytes) else values
        config.select_opts.append((os.fsdecode(option_string), addarg))


class AddFilelistAction(DuplicityAction):
    def __init__(self, option_strings, dest, **kwargs):
        super().__init__(option_strings, dest, **kwargs)

    def __call__(self, parser, namespace, values, option_string=None):
        config.select_opts.append((os.fsdecode(option_string), os.fsdecode(values)))
        try:
            config.select_files.append(io.open(values, u"rt", encoding=u"UTF-8"))
        except Exception as e:
            command_line_error(str(e))


class AddRenameAction(DuplicityAction):
    def __init__(self, option_strings, dest, **kwargs):
        super().__init__(option_strings, dest, **kwargs)

    def __call__(self, parser, namespace, values, option_string=None):
        key = os.fsencode(os.path.normcase(os.path.normpath(values[0])))
        config.rename[key] = os.fsencode(values[1])


class DeprecationAction(DuplicityAction):
    def __init__(self, option_strings, dest, **kwargs):
        super().__init__(option_strings, dest, **kwargs)

    def __call__(self, parser, namespace, values, option_string=None):
        command_line_error(_(
            f"Option '{option_string} was removed or changed in 2.0.0.\n"
            f"See https://gitlab.com/duplicity/duplicity/-/issues/152\n"
            f"for discussion and possible replacement options."))


class IgnoreErrorsAction(DuplicityAction):
    def __init__(self, option_strings, dest, **kwargs):
        super().__init__(option_strings, dest, **kwargs)

    def __call__(self, parser, namespace, values, option_string=None):
        log.Warn(_(u"Running in 'ignore errors' mode due to --ignore-errors.\n"
                   u"Please reconsider if this was not intended"))
        config.ignore_errors = True


def check_count(val):
    try:
        return int(val)
    except Exception as e:
        command_line_error(_(f"'{val}' is not an int: {str(e)}"))


def check_remove_time(val):
    try:
        return dup_time.genstrtotime(val)
    except Exception as e:
        command_line_error(str(e))


def check_source_path(val):
    if u"://" in val:
        command_line_error(_(f"Source should be pathname, not url.  Got '{val}' instead."))
    if not os.path.exists(val):
        command_line_error(_(f"Argument source_path '{val}' does not exist."))
    return val


def check_source_url(val):
    if u"://" not in val:
        command_line_error(_(f"Source should be url, not directory.  Got '{val}' instead."))
    return val


def check_target_dir(val):
    if u"://" in val:
        command_line_error(_(f"Target should be directory, not url.  Got '{val}' instead."))
    if not os.path.exists(val):
        try:
            os.makedirs(val, exist_ok=True)
        except Exception as e:
            command_line_error(_(f"Unable to create target dir '{val}': {str(e)}"))
    return val


def check_target_url(val):
    if u"://" not in val:
        command_line_error(_(f"Source should be url, not directory.  Got '{val}' instead."))
    return val


def dflt(val):
    u"""
    Return printable value for default.
    """
    if isinstance(val, (str, bytes, bool, int)):
        return val
    else:
        return None


def expand_fn(filename):
    return os.path.expanduser(os.path.expandvars(filename))


def expand_archive_dir(archdir, backname):
    u"""
    Return expanded version of archdir joined with backname.
    """
    assert config.backup_name is not False, \
        u"expand_archive_dir() called prior to config.backup_name being set"

    return expand_fn(os.path.join(archdir, os.fsencode(backname)))


def generate_default_backup_name(backend_url):
    u"""
    @param backend_url: URL to backend.
    @returns A default backup name (string).
    """
    # For default, we hash args to obtain a reasonably safe default.
    # We could be smarter and resolve things like relative paths, but
    # this should actually be a pretty good compromise. Normally only
    # the destination will matter since you typically only restart
    # backups of the same thing to a given destination. The inclusion
    # of the source however, does protect against most changes of
    # source directory (for whatever reason, such as
    # /path/to/different/snapshot). If the user happens to have a case
    # where relative paths are used yet the relative path is the same
    # (but duplicity is run from a different directory or similar),
    # then it is simply up to the user to set --archive-dir properly.
    burlhash = md5()
    burlhash.update(backend_url.encode())
    return burlhash.hexdigest()


def check_file(value):
    return os.fsencode(expand_fn(value))


def check_time(value):
    try:
        return dup_time.genstrtotime(value)
    except dup_time.TimeException as e:
        command_line_error(str(e))


def check_verbosity(value):
    # TODO: normalize logging to Python standards
    fail = False
    verb = log.NOTICE
    value = value.lower()
    if value in [u'e', u'error']:
        verb = log.ERROR
    elif value in [u'w', u'warning']:
        verb = log.WARNING
    elif value in [u'n', u'notice']:
        verb = log.NOTICE
    elif value in [u'i', u'info']:
        verb = log.INFO
    elif value in [u'd', u'debug']:
        verb = log.DEBUG
    else:
        try:
            verb = int(value)
            if verb < 0 or verb > 9:
                fail = True
        except ValueError:
            fail = True

    if fail:
        # TRANSL: In this portion of the usage instructions, "[ewnid]" indicates which
        # characters are permitted (e, w, n, i, or d); the brackets imply their own
        # meaning in regex; i.e., only one of the characters is allowed in an instance.
        command_line_error(_(
            u"Verbosity must be one of: digit [0-9], character [ewnid],\n"
            u"or word ['error', 'warning', 'notice', 'info', 'debug'].\n"
            u"The default is 4 (Notice).  It is strongly recommended\n"
            u"that verbosity level is set at 2 (Warning) or higher."))

    log.setverbosity(verb)
    return verb


def make_bytes(value):
    if isinstance(value, str):
        return bytes(value, u'utf-8')


def var2cmd(s):
    u"""
    Convert var name to command string
    """
    return s.replace(u"_", u"-")


def var2opt(s):
    u"""
    Convert var name to option string
    """
    if len(s) > 1:
        return u"--" + s.replace(u"_", u"-")
    else:
        return u"-" + s


def cmd2var(s):
    u"""
    Convert ccommand string to var name
    """
    return s.replace(u"-", u"_")


def opt2var(s):
    u"""
    Convert option string to var name
    """
    return s.lstrip(u"-").replace(u"-", u"_")


def set_log_fd(fd):
    try:
        fd = int(fd)
    except ValueError:
        command_line_error(u"log_fd must be an integer.")
    if fd < 1:
        command_line_error(u"log-fd must be greater than zero.")
    log.add_fd(fd)
    return fd


def set_log_file(fn):
    fn = check_file(fn)
    log.add_file(fn)
    return fn


def set_megs(num):
    return int(num) * 1024 * 1024


def set_archive_dir(dirstring):
    u"""Check archive dir and set global"""
    if not os.path.exists(dirstring):
        try:
            os.makedirs(dirstring)
        except Exception:
            pass
    archive_dir_path = path.Path(dirstring)
    if not archive_dir_path.isdir():
        command_line_error(_(f"Specified archive directory '{archive_dir_path.uc_name}' is not a directory"))
    config.archive_dir_path = archive_dir_path


def set_encrypt_key(encrypt_key):
    u"""Set config.gpg_profile.encrypt_key assuming proper key given"""
    if not gpg_key_patt.match(encrypt_key):
        command_line_error(_(f"Encrypt key should be an 8, 16, or 40 character hex string, like 'AA0E73D2'.\n"
                             f"Received '{encrypt_key}' length={len(encrypt_key)} instead."))
    if config.gpg_profile.recipients is None:
        config.gpg_profile.recipients = []
    config.gpg_profile.recipients.append(encrypt_key)


def set_hidden_encrypt_key(hidden_encrypt_key):
    u"""Set config.gpg_profile.hidden_encrypt_key assuming proper key given"""
    if not gpg_key_patt.match(hidden_encrypt_key):
        command_line_error(_(f"Hidden dncrypt key should be an 8, 16, or 40 character hex string, like 'AA0E73D2'.\n"
                             f"Received '{hidden_encrypt_key}' length={len(hidden_encrypt_key)} instead."))
    if config.gpg_profile.hidden_recipients is None:
        config.gpg_profile.hidden_recipients = []
    config.gpg_profile.hidden_recipients.append(hidden_encrypt_key)


def set_sign_key(sign_key):
    u"""Set config.gpg_profile.sign_key assuming proper key given"""
    if not gpg_key_patt.match(sign_key):
        command_line_error(_(f"Sign key should be an 8, 16, or 40 character hex string, like 'AA0E73D2'.\n"
                             f"Received '{sign_key}' length={len(sign_key)} instead."))
    config.gpg_profile.sign_key = sign_key


def set_selection():
    u"""Return selection iter starting at filename with arguments applied"""
    sel = selection.Select(config.local_path)
    sel.ParseArgs(config.select_opts, config.select_files)
    config.select = sel.set_iter()
