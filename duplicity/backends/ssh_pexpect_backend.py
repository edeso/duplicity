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

# The following can be redefined to use different shell commands from
# ssh or scp or to add more arguments.  However, the replacements must
# have the same syntax.  Also these strings will be executed by the
# shell, so shouldn't have strange characters in them.

from __future__ import division

import os
import re

from duplicity import config
from duplicity import log
from duplicity import util
from duplicity.errors import BackendException
import duplicity.backend


class SSHPExpectBackend(duplicity.backend.Backend):
    """This backend copies files using scp.  List not supported.  Filenames
       should not need any quoting or this will break."""
    def __init__(self, parsed_url):
        """scpBackend initializer"""
        duplicity.backend.Backend.__init__(self, parsed_url)

        try:
            global pexpect
            import pexpect
        except ImportError:
            raise

        if pexpect.__version__ < "4.5.0":
            log.FatalError("""
                The version of pexpect, '%s`, is too old.  We need version 4.5.0 or above to run.
                See https://gitlab.com/duplicity/duplicity/-/issues/125 for the gory details.

                Use "python3 -m pip install pexpect" to install the latest version.
                """ % pexexpect.__version__)

        self.retry_delay = 10

        self.scp_command = "scp"
        if config.scp_command:
            self.scp_command = config.scp_command

        self.sftp_command = "sftp"
        if config.sftp_command:
            self.sftp_command = config.sftp_command

        self.scheme = duplicity.backend.strip_prefix(parsed_url.scheme, 'pexpect')
        self.use_scp = (self.scheme == 'scp')

        # host string of form [user@]hostname
        if parsed_url.username:
            self.host_string = parsed_url.username + "@" + parsed_url.hostname
        else:
            self.host_string = parsed_url.hostname
        # make sure remote_dir is always valid
        if parsed_url.path:
            # remove leading '/'
            self.remote_dir = re.sub(r'^/', r'', parsed_url.path, 1)
        else:
            self.remote_dir = '.'
        self.remote_prefix = self.remote_dir + '/'
        # maybe use different ssh port
        if parsed_url.port:
            config.ssh_options = config.ssh_options + " -oPort=%s" % parsed_url.port
        # set some defaults if user has not specified already.
        if "ServerAliveInterval" not in config.ssh_options:
            config.ssh_options += " -oServerAliveInterval=%d" % ((int)(config.timeout / 2))
        if "ServerAliveCountMax" not in config.ssh_options:
            config.ssh_options += " -oServerAliveCountMax=2"

        # set up password
        self.use_getpass = config.ssh_askpass
        self.password = self.get_password()

    def run_scp_command(self, commandline):
        """ Run an scp command, responding to password prompts """
        log.Info("Running '%s'" % commandline)
        child = pexpect.spawn(commandline, timeout=None, use_poll=True)
        if config.ssh_askpass:
            state = "authorizing"
        else:
            state = "copying"
        while 1:
            if state == "authorizing":
                match = child.expect([pexpect.EOF,
                                      "(?i)timeout, server not responding",
                                      "(?i)pass(word|phrase .*):",
                                      "(?i)permission denied",
                                      "authenticity"])
                log.Debug("State = %s, Before = '%s'" % (state, child.before.strip()))
                if match == 0:
                    log.Warn("Failed to authenticate")
                    break
                elif match == 1:
                    log.Warn("Timeout waiting to authenticate")
                    break
                elif match == 2:
                    child.sendline(self.password)
                    state = "copying"
                elif match == 3:
                    log.Warn("Invalid SSH password")
                    break
                elif match == 4:
                    log.Warn("Remote host authentication failed (missing known_hosts entry?)")
                    break
            elif state == "copying":
                match = child.expect([pexpect.EOF,
                                      "(?i)timeout, server not responding",
                                      "stalled",
                                      "authenticity",
                                      "ETA"])
                log.Debug("State = %s, Before = '%s'" % (state, child.before.strip()))
                if match == 0:
                    break
                elif match == 1:
                    log.Warn("Timeout waiting for response")
                    break
                elif match == 2:
                    state = "stalled"
                elif match == 3:
                    log.Warn("Remote host authentication failed (missing known_hosts entry?)")
                    break
            elif state == "stalled":
                match = child.expect([pexpect.EOF,
                                      "(?i)timeout, server not responding",
                                      "ETA"])
                log.Debug("State = %s, Before = '%s'" % (state, child.before.strip()))
                if match == 0:
                    break
                elif match == 1:
                    log.Warn("Stalled for too long, aborted copy")
                    break
                elif match == 2:
                    state = "copying"
        child.close(force=True)
        if child.exitstatus != 0:
            raise BackendException("Error running '%s'" % commandline)

    def run_sftp_command(self, commandline, commands):
        """ Run an sftp command, responding to password prompts, passing commands from list """
        maxread = 2000  # expected read buffer size
        responses = [pexpect.EOF,
                     "(?i)timeout, server not responding",
                     "sftp>",
                     "(?i)pass(word|phrase .*):",
                     "(?i)permission denied",
                     "authenticity",
                     "(?i)no such file or directory",
                     "Couldn't delete file: No such file or directory",
                     "Couldn't delete file",
                     "open(.*): Failure"]
        max_response_len = max([len(p) for p in responses[1:]])
        log.Info("Running '%s'" % (commandline))
        child = pexpect.spawn(commandline, timeout=None, maxread=maxread, encoding=config.fsencoding, use_poll=True)
        cmdloc = 0
        passprompt = 0
        while 1:
            msg = ""
            match = child.expect(responses,
                                 searchwindowsize=maxread + max_response_len)
            log.Debug("State = sftp, Before = '%s'" % (child.before.strip()))
            if match == 0:
                break
            elif match == 1:
                msg = "Timeout waiting for response"
                break
            if match == 2:
                if cmdloc < len(commands):
                    command = commands[cmdloc]
                    log.Info("sftp command: '%s'" % (command,))
                    child.sendline(command)
                    cmdloc += 1
                else:
                    command = 'quit'
                    child.sendline(command)
                    res = child.before
            elif match == 3:
                passprompt += 1
                child.sendline(self.password)
                if (passprompt > 1):
                    raise BackendException("Invalid SSH password.")
            elif match == 4:
                if not child.before.strip().startswith("mkdir"):
                    msg = "Permission denied"
                    break
            elif match == 5:
                msg = "Host key authenticity could not be verified (missing known_hosts entry?)"
                break
            elif match == 6:
                if not child.before.strip().startswith("rm"):
                    msg = "Remote file or directory does not exist in command='%s'" % (commandline,)
                    break
            elif match == 7:
                if not child.before.strip().startswith("Removing"):
                    msg = "Could not delete file in command='%s'" % (commandline,)
                    break
            elif match == 8:
                msg = "Could not delete file in command='%s'" % (commandline,)
                break
            elif match == 9:
                msg = "Could not open file in command='%s'" % (commandline,)
                break
        child.close(force=True)
        if child.exitstatus == 0:
            return res
        else:
            raise BackendException("Error running '%s': %s" % (commandline, msg))

    def _put(self, source_path, remote_filename):
        remote_filename = os.fsdecode(remote_filename)
        if self.use_scp:
            self.put_scp(source_path, remote_filename)
        else:
            self.put_sftp(source_path, remote_filename)

    def put_sftp(self, source_path, remote_filename):
        commands = ["put \"%s\" \"%s.%s.part\"" %
                    (source_path.uc_name, self.remote_prefix, remote_filename),
                    "rename \"%s.%s.part\" \"%s%s\"" %
                    (self.remote_prefix, remote_filename, self.remote_prefix, remote_filename)]
        commandline = ("%s %s %s" % (self.sftp_command,
                                     config.ssh_options,
                                     self.host_string))
        self.run_sftp_command(commandline, commands)

    def put_scp(self, source_path, remote_filename):
        commandline = "%s %s %s %s:%s%s" % \
            (self.scp_command, config.ssh_options, source_path.uc_name, self.host_string,
             self.remote_prefix, remote_filename)
        self.run_scp_command(commandline)

    def _get(self, remote_filename, local_path):
        remote_filename = os.fsdecode(remote_filename)
        if self.use_scp:
            self.get_scp(remote_filename, local_path)
        else:
            self.get_sftp(remote_filename, local_path)

    def get_sftp(self, remote_filename, local_path):
        commands = ["get \"%s%s\" \"%s\"" %
                    (self.remote_prefix, remote_filename, local_path.uc_name)]
        commandline = ("%s %s %s" % (self.sftp_command,
                                     config.ssh_options,
                                     self.host_string))
        self.run_sftp_command(commandline, commands)

    def get_scp(self, remote_filename, local_path):
        commandline = "%s %s %s:%s%s %s" % \
            (self.scp_command, config.ssh_options, self.host_string, self.remote_prefix,
             remote_filename, local_path.uc_name)
        self.run_scp_command(commandline)

    def _list(self):
        # Note that this command can get confused when dealing with
        # files with newlines in them, as the embedded newlines cannot
        # be distinguished from the file boundaries.
        dirs = self.remote_dir.split(os.sep)
        if len(dirs) > 0:
            if dirs[0] == '':
                dirs[0] = '/'
        mkdir_commands = []
        for d in dirs:
            mkdir_commands += ["mkdir \"%s\"" % (d)] + ["cd \"%s\"" % (d)]

        commands = mkdir_commands + ["ls -1"]
        commandline = ("%s %s %s" % (self.sftp_command,
                                     config.ssh_options,
                                     self.host_string))

        l = self.run_sftp_command(commandline, commands).split('\n')[1:]

        return [x for x in map("".__class__.strip, l) if x]

    def _delete(self, filename):
        commands = ["cd \"%s\"" % (self.remote_dir,)]
        commands.append("rm \"%s\"" % os.fsdecode(filename))
        commandline = ("%s %s %s" % (self.sftp_command, config.ssh_options, self.host_string))
        self.run_sftp_command(commandline, commands)

    def _delete_list(self, filename_list):
        commands = ["cd \"%s\"" % (self.remote_dir,)]
        for filename in filename_list:
            commands.append("rm \"%s\"" % os.fsdecode(filename))
        commandline = ("%s %s %s" % (self.sftp_command, config.ssh_options, self.host_string))
        self.run_sftp_command(commandline, commands)


duplicity.backend.register_backend("pexpect+sftp", SSHPExpectBackend)
duplicity.backend.register_backend("pexpect+scp", SSHPExpectBackend)
duplicity.backend.uses_netloc.extend(['pexpect+sftp', 'pexpect+scp'])
