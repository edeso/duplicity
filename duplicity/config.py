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

"""Store global configuration information"""

import os
import pickle
import socket
import sys

from duplicity import __version__, log
from duplicity import gpg

# The current version of duplicity
version = __version__

# The following args are set by commandline processing
# they correspond to the args in cli_main.duplicity_commands
count = None
remove_time = None
source_path = None
source_url = None
target_dir = None
target_url = None

# action to take
action = None

# True if inc implied, not explicit
implied_inc = False

# Prefix for all files (appended before type-specific prefixes)
file_prefix = b""

# Prefix for manifest files only
file_prefix_manifest = b""

# Prefix for archive files only
file_prefix_archive = b""

# Prefix for sig files only
file_prefix_signature = b""

# Prefix for jsonstat files only
file_prefix_jsonstat = b""

# The name of the current host
hostname = socket.gethostname()

# For historical reasons also save the FQDN for comparing manifests, but
# we tend to prefer the hostname going forward.
fqdn = socket.getfqdn()

# The main local path.  For backing up the is the path to be backed
# up.  For restoring, this is the destination of the restored files.
local_path = None

# The symbolic name of the backup being operated upon.
backup_name = None

# Set to the Path of the archive directory (the directory which
# contains the signatures and manifests of the relevent backup
# collection), and for checkpoint state between volumes.
# NOTE: this gets expanded in duplicity.commandline
os.environ["XDG_CACHE_HOME"] = os.getenv("XDG_CACHE_HOME", os.path.expanduser("~/.cache"))
archive_dir = os.path.expandvars("$XDG_CACHE_HOME/duplicity")
archive_dir_path = None

# config dir for future use
os.environ["XDG_CONFIG_HOME"] = os.getenv("XDG_CONFIG_HOME", os.path.expanduser("~/.config"))
config_dir = os.path.expandvars("$XDG_CONFIG_HOME/duplicity")
config_dir_path = None

# Restores will try to bring back the state as of the following time.
# If it is None, default to current time.
restore_time = None

# If set, restore only the subdirectory or file specified, not the
# whole root.
restore_path = None

# The backend representing the remote side
backend = None

# Are errors fatal (set for retry decorator in backend.py)
# See example of use in multibackend.py _list()
# Do not use in normal cases!
are_errors_fatal = {
    "delete": (True, None),
    "get": (True, None),
    "list": (True, None),
    "move": (True, None),
    "put": (True, None),
    "query": (True, None),
}

# Select object which iterates paths in the local source dir.
select = None
select_opts = []
select_files = []

# gpg binary to use
gpg_binary = None

# Options to pass to gpg
gpg_options = ""

# Set to GPGProfile that will be used to compress/uncompress encrypted
# files.  Replaces encryption_keys, sign_key, and passphrase settings.
gpg_profile = None

# Maximum file blocksize
max_blocksize = 2048

# If true, filelists and directory statistics will be split on
# nulls instead of newlines.
null_separator = None

# number of retries on network operations
num_retries = 5

# True if Pydev debugger should be activated
pydevd = False

# Character used like the ":" in time strings like
# 2002-08-06T04:22:00-07:00.  The colon isn't good for filenames on
# windows machines.
time_separator = ":"

# Global lockfile used to manage concurrency
lockfile = None
lockpath = ""

# If this is true, only warn and don't raise fatal error when backup
# source directory doesn't match previous backup source directory.
allow_source_mismatch = False

# If set, print the statistics after every backup session
print_statistics = True

# If set, write extra statistic in json format to file
jsonstat = False

# If set, forces a full backup if the last full backup is older than
# the time specified
full_if_older_than = None

# If set the incremental backup will be skipped if not DeltaEntries are detected
skip_if_no_change = False
# Track if incremental backup was skipped, no cli option
skipped_inc = False

# Used to confirm certain destructive operations like deleting old files.
force = None

# If set, signifies the number of backups chains to keep when performing
# a remove-all-but-n-full.
keep_chains = None

# Don't actually do anything, but still report what would be done
dry_run = False

# Compress files on remote system?
compression = True

# Encrypt files on remote system?
encryption = True

# volume size. default 200M
volsize = 200 * 1024 * 1024

# file copy blocksize
copy_blocksize = 128 * 1024

# Swift has a limit on the size of a single uploaded object; by default this is 5GB.
# https://docs.openstack.org/swift/latest/overview_large_objects.html
# With a volume large than this size, we will switch to multipart upload.
mp_segment_size = 5 * 2**30

# Working directory for the tempfile module. Defaults to /tmp on most systems.
temproot = None

# network timeout value
timeout = 30

# FTP data connection type
ftp_connection = "passive"

# Header options for Webdav
webdav_headers = ""

# Asynchronous put/get concurrency limit
# (default of 0 disables asynchronicity).
async_concurrency = 0

# File owner uid keeps number from tar file. Like same option in GNU tar.
numeric_owner = False

# Do no restore the uid/gid when finished, useful if you're restoring
# data without having root privileges or Unix users support
restore_ownership = True

# Whether to use plain HTTP (without SSL) to send data to S3
# See <https://bugs.launchpad.net/duplicity/+bug/433970>.
s3_unencrypted_connection = False

# Whether to use S3 Reduced Redudancy Storage
s3_use_rrs = False

# Whether to use S3 Infrequent Access Storage
s3_use_ia = False

# Whether to use S3 Glacier Storage
s3_use_glacier = False

# Whether to use S3 Glacier IR Storage
s3_use_glacier_ir = False

# Whether to use S3 Glacier Deep Archive Storage
s3_use_deep_archive = False

# Whether to use S3 One Zone Infrequent Access Storage
s3_use_onezone_ia = False

# Chunk size used for S3 multipart uploads.The number of parallel uploads to
# S3 be given by chunk size / volume size. Use this to maximize the use of
# your bandwidth. Defaults to 25MB
s3_multipart_chunk_size = 20 * 1024 * 1024

# Minimum chunk size accepted by S3
s3_multipart_minimum_chunk_size = 5 * 1024 * 1024

# Maximum number of processes to use while doing a multipart upload to S3
s3_multipart_max_procs = 4

# Use server side encryption in s3
s3_use_sse = False

# Use server side kms encryption in s3
s3_use_sse_kms = False
s3_kms_key_id = None
s3_kms_grant = None

# region and endpoint of s3
s3_region_name = None
s3_endpoint_url = None

# Which storage policy to use for Swift containers
swift_storage_policy = ""

# The largest size upload supported in a single put call for azure
azure_max_single_put_size = None

# The size of the blocks put to azure blob storage if bigger than azure_max_single_put_size
azure_max_block_size = None

# Maximum number of parallel connections to use when the blob size for azure exceeds 64MB
azure_max_connections = None

# Standard storage tier used for storring backup blobs (Hot|Cool|Archive).
azure_blob_tier = None

# Whether to use the full email address as the user name when
# logging into an imap server. If false just the user name
# part of the email address is used.
imap_full_address = False

# Name of the imap folder where we want to store backups.
# Can be changed with a command line argument.
imap_mailbox = "INBOX"

# Sync partial metadata by default
metadata_sync_mode = "partial"

# Wheter to specify --use-agent in GnuPG options
use_agent = False

# ssh duplicity_commands to use, used by ssh_pexpect (defaults to sftp, scp)
scp_command = None
sftp_command = None

# default to batch mode using public-key encryption
ssh_askpass = False

# user added ssh options
ssh_options = ""

# default cf backend is pyrax
cf_backend = "pyrax"

# default to fully deleting files in b2
b2_hide_files = False

# HTTPS ssl options (currently only webdav, lftp)
ssl_cacert_file = None
ssl_cacert_path = None
ssl_no_check_certificate = False

# user added rsync options
rsync_options = ""

# will be a Restart object if restarting
restart = None

# ignore (some) errors during operations; supposed to make it more
# likely that you are able to restore data under problematic
# circumstances. the default should absolutely always be True unless
# you know what you are doing.
ignore_errors = False

# Renames (--rename)
rename = {}

# enable data comparison on verify runs
compare_data = False

# sequencial backend tasks by default
concurrency = 0

# When symlinks are encountered, the item they point to is copied rather than
# the symlink.
copy_links = False

# When selected, triggers a dry-run before a full or incremental to compute
# changes, then runs the real operation and keeps track of the real progress
progress = False

# Controls the upload progress messages refresh rate. Default: update each
# 3 seconds
progress_rate = 3

# Level of Redundancy in % for Par2 files
par2_redundancy = 10

# Verbatim par2 other options
par2_options = ""

# Number of par2 volumes
par2_volumes = 1

# If set, log the chnages is the set instead of the normal collection status
show_changes_in_set = None

# If set, collect only the file status, not the whole root.
file_changed = None

# If set collect the files_changed list in statistics
files_changed = True

# delay (in seconds) before next operation after failure
backend_retry_delay = 30

# option for mediafire to purge files on delete instead of sending to trash
mf_purge = False

# Fake root directory path for iDrived backend
idr_fakeroot = None

# whether to check remote manifest (requires private key)
check_remote = True

# log verbosity, default get set in program logic.
verbosity = None

# whether 'inc` is explicit or not
# inc_explicit = True

# used in testing only -- set current time
current_time = None

# used in testing only - raises exception after volume
fail_on_volume = 0

# used in testing only - skips uploading a particular volume
skip_volume = 0

# used in testing only - fail BackendWrapper.put() on difftar volN
put_fail_volume = 0


# default filesystem encoding
# It seems that sys.getfilesystemencoding() will normally return
# 'utf-8' or some other sane encoding, but will sometimes fail and returns
# either 'ascii' or None.  Both are bogus, so default to 'utf-8' if it does.
fsencoding = sys.getfilesystemencoding()
fsencoding = fsencoding if fsencoding not in ["ascii", "ANSI_X3.4-1968", None] else "utf-8"


def dump_dict(config):
    """
    returns "pickleable" config as dict.

    skips all internal attributes (__var__) and atrributes
    where pickling failed.
    Know skipped attributes:
      select: <duplicity.selection.Select object at 0x7fafec27a550>
      lockfile: <fasteners.process_lock.InterProcessLock object at 0x7fafec706290>
    """
    c = {}
    for k, v in config.__dict__.items():
        try:
            if k.startswith("__") and k.endswith("__"):
                continue
            pickle.dumps(v)
        except (pickle.PicklingError, TypeError, AttributeError) as e:
            log.Debug(f"Skip {k}: {v} in config dump")
        else:
            c[k] = v
    return c


def load_dict(config_dict, config):
    """
    update config from a dict.
    """
    for k, v in config_dict.items():
        setattr(config, k, v)
