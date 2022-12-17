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

u"""
Usage messages with translation.
"""

trans = {
    # TRANSL: Used in usage help to represent a Unix-style path name. Example:
    # rsync://user[:password]@other_host[:port]//absolute_path
    u'absolute_path': _(u"absolute_path"),

    # TRANSL: Used in usage help. Example:
    # tahoe://alias/some_dir
    u'alias': _(u"alias"),

    # TRANSL: Used in help to represent a "bucket name" for Amazon Web
    # Services' Simple Storage Service (S3). Example:
    # s3://other.host/bucket_name[/prefix]
    u'bucket_name': _(u"bucket_name"),

    # TRANSL: abbreviation for "character" (noun)
    u'char': _(u"char"),

    # TRANSL: noun
    u'command': _(u"command"),

    # TRANSL: Used in usage help to represent the name of a container in
    # Amazon Web Services' Cloudfront. Example:
    # cf+http://container_name
    u'container_name': _(u"container_name"),

    # TRANSL: noun
    u'count': _(u"count"),

    # TRANSL: Used in usage help to represent the name of a file directory
    u'directory': _(u"directory"),

    # TRANSL: Used in usage help to represent the name of a file. Example:
    # --log-file <filename>
    u'filename': _(u"filename"),

    # TRANSL: Used in usage help to represent an ID for a GnuPG key. Example:
    # --encrypt-key <gpg_key_id>
    u'gpg_key_id': _(u"gpg-key-id"),

    # TRANSL: Used in usage help, e.g. to represent the name of a code
    # module. Example:
    # rsync://user[:password]@other.host[:port]::/module/some_dir
    u'module': _(u"module"),

    # TRANSL: Used in usage help to represent a desired number of
    # something. Example:
    # --num-retries <number>
    u'number': _(u"number"),

    # TRANSL: Used in usage help. (Should be consistent with the "Options:"
    # header.) Example:
    # duplicity [full|incremental] [options] source_dir target_url
    u'options': _(u"options"),

    # TRANSL: Used in usage help to represent an internet hostname. Example:
    # ftp://user[:password]@other.host[:port]/some_dir
    u'other_host': _(u"other.host"),

    # TRANSL: Used in usage help. Example:
    # ftp://user[:password]@other.host[:port]/some_dir
    u'password': _(u"password"),

    # TRANSL: Used in usage help to represent a Unix-style path name. Example:
    # --archive-dir <path>
    u'path': _(u"path"),

    # TRANSL: Used in usage help to represent a TCP port number. Example:
    # ftp://user[:password]@other.host[:port]/some_dir
    u'port': _(u"port"),

    # TRANSL: Used in usage help. This represents a string to be used as a
    # prefix to names for backup files created by Duplicity. Example:
    # s3://other.host/bucket_name[/prefix]
    u'prefix': _(u"prefix"),

    # TRANSL: Used in usage help to represent a Unix-style path name. Example:
    # rsync://user[:password]@other.host[:port]/relative_path
    u'relative_path': _(u"relative_path"),

    # TRANSL: Used in usage help. Example:
    # --timeout <seconds>
    u'seconds': _(u"seconds"),

    # TRANSL: Used in usage help to represent a "glob" style pattern for
    # matching one or more files, as described in the documentation.
    # Example:
    # --exclude <shell_pattern>
    u'shell_pattern': _(u"shell_pattern"),

    # TRANSL: Used in usage help to represent the name of a single file
    # directory or a Unix-style path to a directory. Example:
    # file:///some_dir
    u'some_dir': _(u"some_dir"),

    # TRANSL: Used in usage help to represent the name of a single file
    # directory or a Unix-style path to a directory where files will be
    # coming FROM. Example:
    # duplicity [full|incremental] [options] source_dir target_url
    u'source_dir': _(u"source_dir"),

    # TRANSL: Used in usage help to represent a URL files will be coming
    # FROM. Example:
    # duplicity [restore] [options] source_url target_dir
    u'source_url': _(u"source_url"),

    # TRANSL: Used in usage help to represent the name of a single file
    # directory or a Unix-style path to a directory. where files will be
    # going TO. Example:
    # duplicity [restore] [options] source_url target_dir
    u'target_dir': _(u"target_dir"),

    # TRANSL: Used in usage help to represent a URL files will be going TO.
    # Example:
    # duplicity [full|incremental] [options] source_dir target_url
    u'target_url': _(u"target_url"),

    # TRANSL: Used in usage help to represent a time spec for a previous
    # point in time, as described in the documentation. Example:
    # duplicity remove-older-than time [options] target_url
    u'time': _(u"time"),

    # TRANSL: Used in usage help to represent a user name (i.e. login).
    # Example:
    # ftp://user[:password]@other.host[:port]/some_dir
    u'user': _(u"user"),

    # TRANSL: account id for b2. Example: b2://account_id@bucket/
    u'account_id': _(u"account_id"),

    # TRANSL: application_key for b2.
    # Example: b2://account_id:application_key@bucket/
    u'application_key': _(u"application_key"),

    # TRANSL: remote name for rclone.
    # Example: rclone://remote:/some_dir
    u'remote': _(u"remote"),
}

help_url_formats = _(u"Backends and their URL formats:") + u"""
  azure://%(container_name)s
  b2://%(account_id)s[:%(application_key)s]@%(bucket_name)s/[%(some_dir)s/]
  boto3+s3://%(bucket_name)s[/%(prefix)s]
  cf+http://%(container_name)s
  dpbx:///%(some_dir)s
  file:///%(some_dir)s
  ftp://%(user)s[:%(password)s]@%(other_host)s[:%(port)s]/%(some_dir)s
  ftps://%(user)s[:%(password)s]@%(other_host)s[:%(port)s]/%(some_dir)s
  gdocs://%(user)s[:%(password)s]@%(other_host)s/%(some_dir)s
  gdrive://<service-account-url>/target-folder/?driveID=<SHARED DRIVE ID> (for GOOGLE Shared Drive)
  gdrive://<service-account-url>/target-folder/?myDriveFolderID=<google-myDrive-folder-id> (for GOOGLE MyDrive)
  hsi://%(user)s[:%(password)s]@%(other_host)s[:%(port)s]/%(some_dir)s
  imap://%(user)s[:%(password)s]@%(other_host)s[:%(port)s]/%(some_dir)s
  mega://%(user)s[:%(password)s]@%(other_host)s/%(some_dir)s
  megav2://%(user)s[:%(password)s]@%(other_host)s/%(some_dir)s
  mf://%(user)s[:%(password)s]@%(other_host)s/%(some_dir)s
  onedrive://%(some_dir)s
  pca://%(container_name)s
  pydrive://%(user)s@%(other_host)s/%(some_dir)s
  rclone://%(remote)s:/%(some_dir)s
  rsync://%(user)s[:%(password)s]@%(other_host)s[:%(port)s]/%(relative_path)s
  rsync://%(user)s[:%(password)s]@%(other_host)s[:%(port)s]//%(absolute_path)s
  rsync://%(user)s[:%(password)s]@%(other_host)s[:%(port)s]::/%(module)s/%(some_dir)s
  s3+http://%(bucket_name)s[/%(prefix)s]
  s3://%(other_host)s[:%(port)s]/%(bucket_name)s[/%(prefix)s]
  scp://%(user)s[:%(password)s]@%(other_host)s[:%(port)s]/%(some_dir)s
  ssh://%(user)s[:%(password)s]@%(other_host)s[:%(port)s]/%(some_dir)s
  swift://%(container_name)s
  tahoe://%(alias)s/%(directory)s
  webdav://%(user)s[:%(password)s]@%(other_host)s/%(some_dir)s
  webdavs://%(user)s[:%(password)s]@%(other_host)s/%(some_dir)s
""" % trans
