# -*- Mode:Python; indent-tabs-mode:nil; tab-width:4 -*-
#
# Copyright 2021 Menno Smits <menno@smi-ling.nl>
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

import os
import urllib
import tempfile
import re
import xml.etree.ElementTree as ET
import shutil
import errno


import duplicity.backend
from duplicity import config
from duplicity import log
from duplicity import tempdir
from duplicity import progress
from duplicity.errors import BackendException

#
#   This backend works with the IDrive  "dedup implementation". V0.1
#               (for all new and recent accounts)
#
#   Credits: This code is loosely inspired by the work of <aappddeevv>
#
#
#   This backend uses an intermediate driver for IDrive: "idevsutil_dedup" that will be
#   installed automagically  when you perform the account setup on your system.
#   It can, however, also be downloaded directly from the following URL's
#
#   https://www.idrivedownloads.com/downloads/linux/download-options/IDrive_linux_64bit.zip
#   and
#   https://www.idrivedownloads.com/downloads/linux/download-options/IDrive_linux_32bit.zip
#
#   for 32 and 64 bit linux, respectively. Copy the file anywhere with exe permissions.
#   (no further setup of your IDrive account is needed for idrived to work)
#
#
#   For this backend to work, you need to create a number of environment variables:
#
#   - Put the absolute path to the driver-file (idevsutil_dedup) in IDEVSPATH
#   - Put the account-name (login name) in IDRIVEID
#
#   - Put the name of the desired bucket for this backup-session in IDBUCKET
#     If this bucket does not exist it will be created at runtime
#
#   - Create a file with the account password - put absolute path in IDPWDFILE
#
#   When using a custom encryption key:
#   - Create a file with the encryption key - put absolute path in IDKEYFILE
#
#   Note: setup proper security for these files!
#
#
#   The IDrive "root" issue ...
#
#   IDrive stores files according to 1) the selected bucket, 2) the supplied path
#   and 3)the absolute path of the directory used for uploads. So ... if we use
#       - bucket <MYBUCKET>
#       - duplicity commandline idrived://DUPLICITY
#   and
#       - system tempfile OR path set from --tempfile "\tmp"
#
#   the files end-up in the following path:
#       <MYBUCKET>/DUPLICITY/tmp/duplicity-??????-tempdir
#
#   Not only is this SO UGLY .... but - as tempdirs have unique names - this effectively
#   disables the idea of incremental backups.
#
#   To remedy this, idrived uses the concept of a "fakeroot" directory, defined via the
#   --idr-fakeroot=... switch. This can be an existing directory, or the directory is
#   created at runtime on the root of the (host) files system. (cave: you have to have
#   write access to the root!). Directories created at runtime are auto-removed on exit!
#
#   So, in the above scheme, we could do:
#       duplicity --idr-fakeroot=nicepath idrived://DUPLICITY
#
#   our files end-up at
#       <MYBUCKET>/DUPLICITY/nicepath
#
#
#   Have fun!
#


class IDriveBackend(duplicity.backend.Backend):

    def __init__(self, parsed_url):
        duplicity.backend.Backend.__init__(self, parsed_url)

        # parsed_url will have leading slashes in it, 4 slashes typically.
        self.parsed_url = parsed_url
        self.url_string = duplicity.backend.strip_auth_from_url(self.parsed_url)
        log.Debug("parsed_url: {0}".format(parsed_url))

        self.connected = False

    def user_connected(self):
        return self.connected

    def request(self, commandline):
        # request for commands returning data in XML format
        log.Debug("Request command: {0}".format(commandline))
        try:
            _, reply, error = self.subprocess_popen(commandline)
        except KeyError:
            raise BackendException("Unknown protocol failure on request {0}".format(commandline))

        response = reply + error
        try:
            xml = "<root>" + ''.join(re.findall("<[^>]+>", response)) + "</root>"
            el = ET.fromstring(xml)

        except:
            el = None
        log.Debug("Request response: {0}".format(response))

        return el

    def connect(self):
        # get the path to the command executable
        path = os.environ.get("IDEVSPATH")
        if path is None:
            log.Warn("-" * 72)
            log.Warn("WARNING: No path to 'idevsutil_dedup' has been set. Download module from")
            log.Warn("   https://www.idrivedownloads.com/downloads/linux/download-options/IDrive_linux_64bit.zip")
            log.Warn("or")
            log.Warn("   https://www.idrivedownloads.com/downloads/linux/download-options/IDrive_linux_32bit.zip")
            log.Warn("and place anywhere with exe rights. Then creat env var 'IDEVSPATH' with path to file")
            log.Warn("-" * 72)
            raise BackendException("No IDEVSPATH env var set. Should contain folder to idevsutil_dedup")
        self.cmd = os.path.join(path, "idevsutil_dedup")
        log.Debug("IDrive command base: %s" % (self.cmd))

        # get the account-id
        self.idriveid = os.environ.get("IDRIVEID")
        if self.idriveid is None:
            log.Warn("-" * 72)
            log.Warn("WARNING: IDrive logon ID missing")
            log.Warn("Create an environment variable IDriveID with your IDrive logon ID")
            log.Warn("-" * 72)
            raise BackendException("No IDRIVEID env var set. Should contain IDrive id")
        log.Debug("IDrive id: %s" % (self.idriveid))

        # Get the full-path to the account password file
        filepath = os.environ.get("IDPWDFILE")
        if filepath is None:
            log.Warn("-" * 72)
            log.Warn("WARNING: IDrive password file missging")
            log.Warn("Please create a file with your IDrive logon password,")
            log.Warn("Then create an environment variable IDPWDFILE with path/filename of said file")
            log.Warn("-" * 72)
            raise BackendException("No IDPWDFILE env var set. Should contain file with password")
        log.Debug("IDrive pwdpath: %s" % (filepath))
        self.auth_switch = " --password-file={0}".format(filepath)

        # fakeroot set? Create directory and mark for cleanup
        if config.fakeroot is None:
            self.cleanup = False
            self.fakeroot = ''
        else:
            # Make sure fake root is created at root level!
            self.fakeroot = os.path.join('/', config.fakeroot)
            try:
                os.mkdir(self.fakeroot)
            except OSError as e:
                self.cleanup = False
                if e.errno == errno.EEXIST:
                    log.Debug("Using existing directory {0} as fake-root".format(self.fakeroot))
                else:
                    log.Warn("-" * 72)
                    log.Warn("WARNING: Creation of FAKEROOT {0} failed; backup will use system temp directory"
                             .format(self.fakeroot))
                    log.Warn("This might interfere with incremental backups")
                    log.Warn("-" * 72)
                    raise BackendException("Creation of the directory {0} failed".format(self.fakeroot))
            else:
                log.Debug("Directory {0} created as fake-root (Will clean-up afterwards!)".format(self.fakeroot))
                self.cleanup = True

        # get the bucket
        self.bucket = os.environ.get("IDBUCKET")
        if self.bucket is None:
            log.Warn("-" * 72)
            log.Warn("WARNING: IDrive backup bucket missing")
            log.Warn("Create an environment variable IDBUCKET specifying the target bucket")
            log.Warn("-" * 72)
            raise BackendException("No IDBUCKET env var set. Should contain IDrive backup bucket")
        log.Debug("IDrive bucket: %s" % (self.bucket))

        # check account / get config status and config type
        el = self.request(self.cmd + self.auth_switch + " --validate --user={0}".format(self.idriveid)).find('tree')

        if el.attrib["message"] != "SUCCESS":
            raise BackendException("Protocol failure - " + el.attrib["desc"])
        if el.attrib["desc"] != "VALID ACCOUNT":
            raise BackendException("IDrive account invalid")
        if el.attrib["configstatus"] != "SET":
            raise BackendException("IDrive account not set")

        # When private encryption enabled: get the full-path to a encription key file
        if el.attrib["configtype"] == "PRIVATE":
            filepath = os.environ.get("IDKEYFILE")
            if filepath is None:
                log.Warn("-" * 72)
                log.Warn("WARNING: IDrive encryption key file missging")
                log.Warn("Please create a file with your IDrive encryption key,")
                log.Warn("Then create an environment variable IDKEYFILE with path/filename of said file")
                log.Warn("-" * 72)
                raise BackendException("No IDKEYFILE env var set. Should contain file with encription key")
            log.Debug("IDrive keypath: %s" % (filepath))
            self.auth_switch += " --pvt-key={0}".format(filepath)

        # get the server address
        el = self.request(self.cmd + self.auth_switch + " --getServerAddress {0}".format(self.idriveid)).find('tree')
        self.idriveserver = el.attrib["cmdUtilityServer"]

        # get the device list - primarely used to get device-id string
        el = self.request(self.cmd + self.auth_switch + " --list-device {0}@{1}::home".
                          format(self.idriveid, self.idriveserver))
        # scan all returned devices for requested device (== bucket)
        self.idrivedevid = None
        for item in el.findall('item'):
            if item.attrib['nick_name'] == self.bucket:
                # prefix and suffix reverse-engineered from Common.pl!
                self.idrivedevid = "5c0b" + item.attrib["device_id"] + "4b5z"
        if self.idrivedevid is None:
            el = self.request(
                self.cmd + self.auth_switch +
                " --create-bucket --bucket-type=D --nick-name={0} --os=Linux --uid=987654321 {1}@{2}::home/"
                .format(self.bucket, self.idriveid, self.idriveserver)).find('item')
            # prefix and suffix reverse-engineered from Common.pl!
            self.idrivedevid = "5c0b" + el.attrib["device_id"] + "4b5z"

        # We're fully connected!
        self.connected = True
        log.Debug("User fully connected")

    def list_raw(self):
        # get raw list; used by _list, _query and _query_list
        remote_path = os.path.join(urllib.parse.unquote(self.parsed_url.path.lstrip('/')),
                                   self.fakeroot.lstrip('/')).rstrip()
        commandline = ((self.cmd + self.auth_switch + " --auth-list --device-id={0} {1}@{2}::home/{3}"
                       .format(self.idrivedevid, self.idriveid, self.idriveserver, remote_path)))
        try:
            _, l, _ = self.subprocess_popen(commandline)
        except:
            # error: treat as empty response
            log.Debug("list EMPTY response ")
            return []

        log.Debug("list response: {0}".format(l))

        # get a list of lists from data lines returned by idevsutil_dedup --auth-list
        filtered = map((lambda line: re.split(r"\[|\]", line)), [x for x in l.splitlines() if x.startswith("[")])
        # remove whitespace from elements
        filtered = map((lambda line: map((lambda c: c.strip()), line)), filtered)
        # remove empty elements
        filtered = list(map((lambda cols: list(filter((lambda c: c != ''), cols))), filtered))

        return filtered

    def _put(self, source_path, remote_filename):
        # Put a file.
        log.Debug("_PUT")
        if not self.user_connected():
            self.connect()

        # decode from byte-stream to utf-8 string
        filename = remote_filename.decode('utf-8')

        intrim_file = os.path.join(self.fakeroot, filename)
        remote_dirpath = urllib.parse.unquote(self.parsed_url.path.lstrip('/'))

        os.rename(source_path.name, intrim_file)

        log.Debug("put_file: source_path={0}, remote_file={1}".format(source_path.name, filename))

        flist = tempfile.NamedTemporaryFile('w')
        flist.write(intrim_file)
        flist.seek(0)

        putrequest = ((self.cmd + self.auth_switch + "  --device-id={0} --files-from={1} / {2}@{3}::home/{4}")
                      .format(self.idrivedevid, flist.name, self.idriveid, self.idriveserver, remote_dirpath))
        log.Debug("put_file put command: {0}".format(putrequest))
        _, putresponse, _ = self.subprocess_popen(putrequest)
        log.Debug("put_file put response: {0}".format(putresponse))

        flist.close()
        os.remove(intrim_file)

    def _get(self, remote_filename, local_path):
        # Get a file.
        log.Debug("_GET")
        if not self.user_connected():
            self.connect()

        # decode from byte-stream to utf-8 string
        filename = remote_filename.decode('utf-8')

        remote_path = os.path.join(urllib.parse.unquote(self.parsed_url.path.lstrip('/')),
                                   self.fakeroot.lstrip('/'), filename).rstrip()

        log.Debug("_get: remote_filename={0}, local_path={1}, remote_path={2}, parsed_url.path={3}"
                  .format(filename, local_path, remote_path, self.parsed_url.path))

        # Create tempdir to downlaod file into
        tmpdir = tempfile.mkdtemp()
        log.Debug("_get created temporary download folder: {}".format(tmpdir))

        # The filelist file
        flist = tempfile.NamedTemporaryFile('w')
        flist.write(remote_path)
        flist.seek(0)

        commandline = ((self.cmd + self.auth_switch + " --device-id={0} --files-from={1} {2}@{3}::home/ {4}")
                       .format(self.idrivedevid, flist.name, self.idriveid, self.idriveserver, tmpdir))
        log.Debug("get command: {0}".format(commandline))
        _, getresponse, _ = self.subprocess_popen(commandline)
        log.Debug("_get response: {0}".format(getresponse))

        flist.close()

        # move to the final location
        downloadedSrcPath = os.path.join(tmpdir, remote_path.lstrip('/').rstrip('/'))
        log.Debug("_get moving file {0} to final location: {1}".format(downloadedSrcPath, local_path.name))

        os.rename(downloadedSrcPath, local_path.name)

        shutil.rmtree(tmpdir)

    def _list(self):
        # List files on remote folder
        log.Debug("_LIST")
        if not self.user_connected():
            self.connect()

        filtered = self.list_raw()
        filtered = [x[-1] for x in filtered]

        return filtered

    def _delete(self, remote_filename):
        # Delete single file
        log.Debug("_DELETE")
        if not self.user_connected():
            self.connect()

        # decode from byte-stream to utf-8 string
        filename = remote_filename.decode('utf-8')

        # create a file-list file
        flist = tempfile.NamedTemporaryFile('w')
        flist.write(filename.lstrip('/'))
        flist.seek(0)

        # target path (remote) on IDrive
        remote_path = os.path.join(urllib.parse.unquote(self.parsed_url.path.lstrip('/')),
                                   self.fakeroot.lstrip('/')).rstrip()
        log.Debug("delete: {0} from remote file path {1}".format(filename, remote_path))

        # delete files from file-list
        delrequest = ((self.cmd + self.auth_switch +
                       " --delete-items --device-id={0} --files-from={1} {2}@{3}::home/{4}")
                      .format(self.idrivedevid, flist.name, self.idriveid, self.idriveserver, remote_path))
        log.Debug("delete: {0}".format(delrequest))
        _, delresponse, _ = self.subprocess_popen(delrequest)
        log.Debug("delete response: {0}".format(delresponse))

        # close tempfile
        flist.close()

    def _delete_list(self, filename_list):
        # Delete multiple files
        log.Debug("_DELETE LIST")
        if not self.user_connected():
            self.connect()

        # create a file-list file
        flist = tempfile.NamedTemporaryFile('w')

        # create file-list
        for filename in filename_list:
            flist.write(filename.decode('utf-8').lstrip('/') + '\n')
        flist.seek(0)

        # target path (remote) on IDrive
        remote_path = os.path.join(urllib.parse.unquote(self.parsed_url.path.lstrip('/')),
                                   self.fakeroot.lstrip('/')).rstrip()
        log.Debug("delete multiple files from remote file path {0}".format(remote_path))

        # delete files from file-list
        delrequest = ((self.cmd + self.auth_switch +
                       " --delete-items --device-id={0} --files-from={1} {2}@{3}::home/{4}")
                      .format(self.idrivedevid, flist.name, self.idriveid, self.idriveserver, remote_path))
        log.Debug("delete: {0}".format(delrequest))
        _, delresponse, _ = self.subprocess_popen(delrequest)
        log.Debug("delete response: {0}".format(delresponse))

        # close tempfile
        flist.close()

    def _close(self):
        # Remove EVS_temp directory + contents
        log.Debug("Removing IDrive temp folder evs_temp")
        try:
            shutil.rmtree("evs_temp")
        except:
            pass

    def _query(self, filename):
        log.Debug("_QUERY")
        if not self.user_connected():
            self.connect()

        # Get raw directory list; take-out size (index 1) for requested filename (index -1)
        filtered = self.list_raw()
        if filtered:
            filtered = [x[1] for x in filtered if x[-1] == filename.decode('utf-8')]
        if filtered:
            return {'size': int(filtered[0])}

        return {'size': -1}

    def _query_list(self, filename_list):
        log.Debug("_QUERY_LIST")
        if not self.user_connected():
            self.connect()

        # Get raw directory list
        filtered = self.list_raw()

        # For each filename in list: take-out size (index 1) for requested filename (index -1)
        info = {}
        for filename in filename_list:
            if filtered:
                result = [x[1] for x in filtered if x[-1] == filename.decode('utf-8')]
            if result:
                info[filename] = {'size': int(result[0])}
            else:
                info[filename] = {'size': -1}

        return info

    def __del__(self):
        # remove the self-created temp dir.
        # We do it here, AFTER the clean-up of Duplicity, so it will be empty!
        if self.cleanup:
            os.rmdir(self.fakeroot)


duplicity.backend.register_backend("idrived", IDriveBackend)
