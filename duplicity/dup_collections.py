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

"""Classes and functions on collections of backup volumes"""

import gzip
import json
import os

from duplicity import (
    config,
    dup_time,
    file_naming,
    log,
    log_util,
    manifest,
    path,
    util,
)
from duplicity.gpg import GPGError


class CollectionsError(Exception):
    pass


class BackupSet(object):
    """
    Backup set - the backup information produced by one session
    """

    def __init__(self, backend, action):
        """
        Initialize new backup set, only backend is required at first
        """
        self.backend = backend
        self.info_set = False  # true if fields are set
        self.volume_name_dict = {}  # dict from volume number to filename
        self.remote_manifest_name = None  # full name of remote manifest
        self.local_manifest_path = None  # full path to local manifest
        self.remote_jsonstat_name = None  # full name of remote jsonstat
        self.local_jsonstat_path = None  # full path to local jsonstat
        self.time = None  # will be set if is full backup set
        self.start_time = None  # will be set if inc
        self.end_time = None  # will be set if inc
        self.partial = False  # true if a partial backup
        self.encrypted = False  # true if an encrypted backup
        self.files_changed = []
        self.action = action

    def is_complete(self):
        """
        Assume complete if found manifest file
        """
        return self.remote_manifest_name

    def add_filename(self, filename, pr=None):
        """
        Add a filename to given set.  Return true if it fits.

        The filename will match the given set if it has the right
        times and is of the right type.  The information will be set
        from the first filename given.

        @param filename: name of file to add
        @type filename: string

        @param pr: pre-computed result of file_naming.parse(filename)
        @type pr: Optional[ParseResults]
        """
        if not pr:
            pr = file_naming.parse(filename)
        if not pr or not (pr.type == "full" or pr.type == "inc" or pr.type == "full-stat" or pr.type == "inc-stat"):
            return False

        if not self.info_set:
            self.set_info(pr)
        else:
            if pr.type.replace("-stat", "") != self.type:
                return False
            if pr.time != self.time:
                return False
            if pr.start_time != self.start_time or pr.end_time != self.end_time:
                return False
            if bool(pr.encrypted) != bool(self.encrypted):
                if self.partial and pr.encrypted:
                    self.encrypted = pr.encrypted

        if "-stat" in pr.type:
            self.type = pr.type.replace("-stat", "")
            self.set_jsonstat(filename)
        elif pr.manifest:
            self.set_manifest(filename)
        else:
            assert pr.volume_number is not None
            assert pr.volume_number not in self.volume_name_dict, (
                f"Volume {int(pr.volume_number)} is already in the volume list as "
                f"{os.fsdecode(self.volume_name_dict[pr.volume_number])}. "
                f"{os.fsdecode(filename)} has the same volume number. "
                f"Please check your command line and retry."
            )
            self.volume_name_dict[pr.volume_number] = filename

        return True

    def set_info(self, pr):
        """
        Set BackupSet information from ParseResults object

        @param pr: parse results
        @type pr: ParseResults
        """
        assert not self.info_set
        self.type = pr.type
        self.time = pr.time
        self.start_time = pr.start_time
        self.end_time = pr.end_time
        self.time = pr.time
        self.partial = pr.partial
        self.encrypted = bool(pr.encrypted)
        self.info_set = True

    def set_jsonstat(self, remote_filename):
        """
        Add local and remote manifest filenames to backup set
        """
        assert (
            not self.remote_jsonstat_name
        ), f"Cannot set filename of remote manifest to {remote_filename}; already set to {self.remote_jsonstat_name}."
        self.remote_jsonstat_name = remote_filename

        local_filename_list = config.archive_dir_path.listdir()
        for local_filename in local_filename_list:
            pr = file_naming.parse(local_filename)
            if (
                pr
                and not pr.manifest
                and pr.type == f"{self.type}-stat"
                and pr.time == self.time
                and pr.start_time == self.start_time
                and pr.end_time == self.end_time
            ):
                self.local_jsonstat_path = config.archive_dir_path.append(local_filename)

                break

    def set_files_changed(self):
        mf = self.get_manifest()
        self.files_changed = mf.get_files_changed()

    def set_manifest(self, remote_filename):
        """
        Add local and remote manifest filenames to backup set
        """
        assert (
            not self.remote_manifest_name
        ), f"Cannot set filename of remote manifest to {remote_filename}; already set to {self.remote_manifest_name}."
        self.remote_manifest_name = remote_filename

        local_filename_list = config.archive_dir_path.listdir()
        for local_filename in local_filename_list:
            pr = file_naming.parse(local_filename)
            if (
                pr
                and pr.manifest
                and pr.type == self.type
                and pr.time == self.time
                and pr.start_time == self.start_time
                and pr.end_time == self.end_time
            ):
                self.local_manifest_path = config.archive_dir_path.append(local_filename)

                self.set_files_changed()
                break

    def delete(self):
        """
        Remove all files in set, both local and remote
        """
        rfn = self.get_filenames()
        rfn.reverse()
        try:
            self.backend.delete(rfn)
        except Exception:
            log.Debug(_("BackupSet.delete: missing %s") % [os.fsdecode(f) for f in rfn])
            pass
        local_filename_list = config.archive_dir_path.listdir()
        for lfn in local_filename_list:
            pr = file_naming.parse(lfn)
            if pr and pr.time == self.time and pr.start_time == self.start_time and pr.end_time == self.end_time:
                try:
                    config.archive_dir_path.append(lfn).delete()
                except Exception:
                    log.Debug(_("BackupSet.delete: missing %s") % [os.fsdecode(f) for f in lfn])
                    pass
        util.release_lockfile()

    def __str__(self):
        """
        For now just list files in set
        """
        filelist = []
        if self.remote_manifest_name:
            filelist.append(self.remote_manifest_name)
        filelist.extend(list(self.volume_name_dict.values()))
        return f"[{', '.join(map(os.fsdecode, filelist))}]"

    def get_timestr(self):
        """
        Return time string suitable for log statements
        """
        return dup_time.timetopretty(self.time or self.end_time)

    def check_manifests(self, check_remote=True):
        """
        Make sure remote manifest is equal to local one
        """
        if not self.remote_manifest_name and not self.local_manifest_path:
            log_util.FatalError(
                _("Fatal Error: No manifests found for most recent backup"),
                log.ErrorCode.no_manifests,
            )
        assert self.remote_manifest_name, "if only one, should be remote"

        remote_manifest = self.get_remote_manifest() if check_remote else None
        if self.local_manifest_path:
            local_manifest = self.get_local_manifest()
        if remote_manifest and self.local_manifest_path and local_manifest:
            if remote_manifest != local_manifest:
                if config.check_remote:
                    log_util.FatalError(
                        _(
                            "Fatal Error: Remote manifest does not match "
                            "local one.  Either the remote backup set or "
                            "the local archive directory has been corrupted."
                        ),
                        log.ErrorCode.mismatched_manifests,
                    )
                else:
                    log.Error(
                        _("Error processing remote manifest (%s): %s")
                        % (os.fsdecode(self.remote_manifest_name), util.uexc(message))
                    )
                    return None
        if not remote_manifest:
            if self.local_manifest_path:
                remote_manifest = local_manifest
            else:
                log_util.FatalError(
                    _("Fatal Error: Neither remote nor local " "manifest is readable."),
                    log.ErrorCode.unreadable_manifests,
                )
        remote_manifest.check_dirinfo()

    def get_local_manifest(self):
        """
        Return manifest object by reading local manifest file
        """
        assert self.local_manifest_path
        manifest_buffer = self.local_manifest_path.get_data()
        log.Info(_("Processing local manifest %s (%s)") % (self.local_manifest_path.uc_name, len(manifest_buffer)))
        return manifest.Manifest().from_string(manifest_buffer)

    def get_remote_manifest(self):
        """
        Return manifest by reading remote manifest on backend
        """
        assert self.remote_manifest_name
        manifest_buffer = self.get_remote_file(self.remote_manifest_name)
        return manifest.Manifest().from_string(manifest_buffer)

    def get_remote_file(self, remote_file):
        try:
            remote_file_buffer = self.backend.get_data(remote_file)
        except GPGError as message:
            log_util.FatalError(_(f"Error processing remote file ({os.fsdecode(remote_file)}): {util.uexc(message)}"))
            return b""
        log.Info(_(f"Processing remote file {os.fsdecode(remote_file)} ({len(remote_file_buffer)})"))
        return remote_file_buffer

    def get_manifest(self):
        """
        Return manifest object, showing preference for local copy
        """
        if self.local_manifest_path:
            return self.get_local_manifest()
        else:
            return self.get_remote_manifest()

    def get_jsonstat(self):
        if self.local_jsonstat_path:
            json_stat_bytes = gzip.decompress(self.local_jsonstat_path.get_data())
        elif self.remote_jsonstat_name:
            json_stat_bytes = self.get_remote_file(self.remote_jsonstat_name)
        else:
            log.Info(_("No Jsonstat file found, return empty."))
            return {}
        return json.loads(json_stat_bytes)

    def get_filenames(self):
        """
        Return sorted list of (remote) filenames of files in set
        """
        assert self.info_set
        volume_num_list = sorted(self.volume_name_dict.keys())
        volume_filenames = [self.volume_name_dict[x] for x in volume_num_list]
        if self.remote_manifest_name:
            # For convenience of implementation for restart support, we treat
            # local partial manifests as this set's remote manifest.  But
            # when specifically asked for a list of remote filenames, we
            # should not include it.
            pr = file_naming.parse(self.remote_manifest_name)
            if pr and not pr.partial:
                volume_filenames.append(self.remote_manifest_name)
        if self.remote_jsonstat_name:
            volume_filenames.append(self.remote_jsonstat_name)
        return volume_filenames

    def get_time(self):
        """
        Return time if full backup, or end_time if incremental
        """
        if self.time:
            return self.time
        if self.end_time:
            return self.end_time
        assert 0, "Neither self.time nor self.end_time set"

    def get_files_changed(self):
        return self.files_changed

    def __len__(self):
        """
        Return the number of volumes in the set
        """
        return len(list(self.volume_name_dict.keys()))

    def __eq__(self, other):
        """
        Return whether this backup set is equal to other
        """
        return (
            self.type == other.type
            and self.time == other.time
            and self.start_time == other.start_time
            and self.end_time == other.end_time
            and len(self) == len(other)
        )


class BackupChain(object):
    """
    BackupChain - a number of linked BackupSets

    A BackupChain always starts with a full backup set and continues
    with incremental ones.
    """

    def __init__(self, backend):
        """
        Initialize new chain, only backend is required at first
        """
        self.backend = backend
        self.fullset = None
        self.incset_list = []  # sorted list of BackupSets
        self.start_time, self.end_time = None, None

    def set_full(self, fullset):
        """
        Add full backup set
        """
        assert not self.fullset and isinstance(fullset, BackupSet)
        self.fullset = fullset
        assert fullset.time
        self.start_time, self.end_time = fullset.time, fullset.time

    def add_inc(self, incset):
        """
        Add incset to self.  Return False if incset does not match
        """
        if self.end_time == incset.start_time:
            self.incset_list.append(incset)
        else:
            if (
                self.incset_list
                and incset.start_time == self.incset_list[-1].start_time
                and incset.end_time > self.incset_list[-1].end_time
            ):
                log.Info(_("Preferring Backupset over previous one!"))
                self.incset_list[-1] = incset
            else:
                log.Info(
                    _("Ignoring incremental Backupset (start_time: %s; needed: %s)")
                    % (
                        dup_time.timetopretty(incset.start_time),
                        dup_time.timetopretty(self.end_time),
                    )
                )
                return False
        self.end_time = incset.end_time
        log.Info(
            _("Added incremental Backupset (start_time: %s / end_time: %s)")
            % (
                dup_time.timetopretty(incset.start_time),
                dup_time.timetopretty(incset.end_time),
            )
        )
        assert self.end_time
        return True

    def delete(self, keep_full=False):
        """
        Delete all sets in chain, in reverse order
        """
        for i in range(len(self.incset_list) - 1, -1, -1):
            self.incset_list[i].delete()
        if self.fullset and not keep_full:
            self.fullset.delete()

    def get_sets_at_time(self, time):
        """
        Return a list of sets in chain earlier or equal to time
        """
        older_incsets = [s for s in self.incset_list if s.end_time <= time]
        return [self.fullset] + older_incsets

    def get_last(self):
        """
        Return last BackupSet in chain
        """
        if self.incset_list:
            return self.incset_list[-1]
        else:
            return self.fullset

    def get_first(self):
        """
        Return first BackupSet in chain (ie the full backup)
        """
        return self.fullset

    def short_desc(self):
        """
        Return a short one-line description of the chain,
        suitable for log messages.
        """
        return f"[{dup_time.timetopretty(self.start_time)}]-[{dup_time.timetopretty(self.end_time)}]"

    def to_log_info(self, prefix=""):
        """
        Return summary, suitable for printing to log
        """
        l = []
        for s in self.get_all_sets():
            if s.time:
                btype = "full"
                time = s.time
            else:
                btype = "inc"
                time = s.end_time
            if s.encrypted:
                enc = "enc"
            else:
                enc = "noenc"
            l.append(f"{prefix}{btype} {dup_time.timetostring(time)} {len(s)} {enc}")
        return l

    def __str__(self):
        """
        Return string representation, for testing purposes
        """
        set_schema = "%20s   %30s   %15s"
        l = [
            "-------------------------",
            _("Chain start time: ") + dup_time.timetopretty(self.start_time),
            _("Chain end time: ") + dup_time.timetopretty(self.end_time),
            _("Number of contained backup sets: %d") % (len(self.incset_list) + 1,),
            _("Total number of contained volumes: %d") % (self.get_num_volumes(),),
            set_schema % (_("Type of backup set:"), _("Time:"), _("Num volumes:")),
        ]

        for s in self.get_all_sets():
            if s.time:
                btype = _("Full")
                time = s.time
            else:
                btype = _("Incremental")
                time = s.end_time
            l.append(set_schema % (btype, dup_time.timetopretty(time), len(s)))

        l.append("-------------------------")
        return "\n".join(l)

    def get_num_volumes(self):
        """
        Return the total number of volumes in the chain
        """
        n = 0
        for s in self.get_all_sets():
            n += len(s)
        return n

    def get_all_sets(self):
        """
        Return list of all backup sets in chain
        """
        if self.fullset:
            return [self.fullset] + self.incset_list
        else:
            return self.incset_list


class SignatureChain(object):
    """
    A number of linked SignatureSets

    Analog to BackupChain - start with a full-sig, and continue with
    new-sigs.
    """

    def __init__(self, local, location):
        """
        Return new SignatureChain.

        local should be true iff the signature chain resides in
        config.archive_dir_path and false if the chain is in
        config.backend.

        @param local: True if sig chain in config.archive_dir_path
        @type local: Boolean

        @param location: Where the sig chain is located
        @type location: config.archive_dir_path or config.backend
        """
        if local:
            self.archive_dir_path, self.backend = location, None
        else:
            self.archive_dir_path, self.backend = None, location
        self.fullsig = None  # filename of full signature
        self.inclist = []  # list of filenames of incremental signatures
        self.start_time, self.end_time = None, None

    def __str__(self):
        """
        Local or Remote and List of files in the set
        """
        if self.archive_dir_path:
            place = _("local")
        else:
            place = _("remote")
        filelist = []
        if self.fullsig:
            filelist.append(self.fullsig)
        filelist.extend(self.inclist)
        return f"{place}: [{', '.join(filelist)}]"

    def check_times(self, time_list):
        """
        Check to make sure times are in whole seconds
        """
        for time in time_list:
            if not isinstance(time, int):
                assert 0, f"Time {time} in {time_list} wrong type"

    def islocal(self):
        """
        Return true if represents a signature chain in archive_dir_path
        """
        if self.archive_dir_path:
            return True
        else:
            return False

    def add_filename(self, filename, pr=None):
        """
        Add new sig filename to current chain.  Return true if fits
        """
        if not pr:
            pr = file_naming.parse(filename)
        if not pr:
            return None

        if self.fullsig:
            if pr.type != "new-sig":
                return None
            if pr.start_time != self.end_time:
                return None
            self.inclist.append(filename)
            self.check_times([pr.end_time])
            self.end_time = pr.end_time
            return 1
        else:
            if pr.type != "full-sig":
                return None
            self.fullsig = filename
            self.check_times([pr.time, pr.time])
            self.start_time, self.end_time = pr.time, pr.time
            return 1

    def get_fileobjs(self, time=None):
        """
        Return ordered list of signature fileobjs opened for reading,
        optionally at a certain time
        """
        assert self.fullsig
        if self.archive_dir_path:  # local

            def filename_to_fileobj(filename):
                """Open filename in archive_dir_path, return filtered fileobj"""
                sig_dp = path.DupPath(self.archive_dir_path.name, (filename,))
                return sig_dp.filtered_open("rb")

        else:
            filename_to_fileobj = self.backend.get_fileobj_read
        return [filename_to_fileobj(f) for f in self.get_filenames(time)]

    def delete(self, keep_full=False):
        """
        Remove all files in signature set
        """
        # Try to delete in opposite order, so something useful even if aborted
        if self.archive_dir_path:
            for i in range(len(self.inclist) - 1, -1, -1):
                self.archive_dir_path.append(self.inclist[i]).delete()
            if not keep_full:
                self.archive_dir_path.append(self.fullsig).delete()
        else:
            assert self.backend
            inclist_copy = self.inclist[:]
            inclist_copy.reverse()
            if not keep_full:
                inclist_copy.append(self.fullsig)
            self.backend.delete(inclist_copy)

    def get_filenames(self, time=None):
        """
        Return ordered list of filenames in set, up to a provided time
        """
        if self.fullsig:
            l = [self.fullsig]
        else:
            l = []

        inclist = self.inclist
        if time:
            inclist = [n for n in inclist if file_naming.parse(n).end_time <= time]

        l.extend(inclist)
        return l


class CollectionsStatus(object):
    """
    Hold information about available chains and sets
    """

    def __init__(self, backend, archive_dir_path, action):
        """
        Make new object.  Does not set values
        """
        self.backend = backend
        self.archive_dir_path = archive_dir_path
        self.action = action

        # Will hold (signature chain, backup chain) pair of active
        # (most recent) chains
        self.matched_chain_pair = None

        # These should be sorted by end_time
        self.all_backup_chains = None
        self.other_backup_chains = None
        self.all_sig_chains = None

        # Other misc paths and sets which shouldn't be there
        self.local_orphaned_sig_names = []
        self.remote_orphaned_sig_names = []
        self.orphaned_backup_sets = None
        self.incomplete_backup_sets = None

        # True if set_values() below has run
        self.values_set = None

    def to_log_info(self):
        """
        Return summary of the collection, suitable for printing to log
        """
        l = [
            f"backend {self.backend.__class__.__name__}",
            f"archive-dir {self.archive_dir_path}",
        ]

        for i in range(len(self.other_backup_chains)):
            # A bit of a misnomer.  Chain might have a sig.
            l.append(f"chain-no-sig {int(i)}")
            l += self.other_backup_chains[i].to_log_info(" ")

        if self.matched_chain_pair:
            l.append("chain-complete")
            l += self.matched_chain_pair[1].to_log_info(" ")

        l.append(f"orphaned-sets-num {len(self.orphaned_backup_sets)}")
        l.append(f"incomplete-sets-num {len(self.incomplete_backup_sets)}")

        return l

    def __str__(self):
        """
        Return string summary of the collection
        """
        l = [
            _("Collection Status"),
            "-----------------",
            _("Connecting with backend: %s") % (self.backend.__class__.__name__,),
            _("Archive dir: %s") % (self.archive_dir_path.uc_name if self.archive_dir_path else "None",),
        ]

        l.append("\n" + _("Found %d secondary backup chain(s).") % len(self.other_backup_chains))
        for i in range(len(self.other_backup_chains)):
            l.append(_("Secondary chain %d of %d:") % (i + 1, len(self.other_backup_chains)))
            l.append(str(self.other_backup_chains[i]))
            l.append("")

        if self.matched_chain_pair:
            l.append("\n" + _("Found primary backup chain with matching " "signature chain:"))
            l.append(str(self.matched_chain_pair[1]))
        else:
            l.append(_("No backup chains with active signatures found"))

        if self.orphaned_backup_sets or self.incomplete_backup_sets:
            l.append(_("Also found %d backup set(s) not part of any chain,") % len(self.orphaned_backup_sets))
            l.append(_("and %d incomplete backup set(s).") % len(self.incomplete_backup_sets))
            # TRANSL: "cleanup" is a hard-coded command, so do not translate it
            l.append(_("These may be deleted by running duplicity with the " '"cleanup" command.'))
        else:
            l.append(_("No orphaned or incomplete backup sets found."))

        return "\n".join(l)

    def set_values(self, sig_chain_warning=1):
        """
        Set values from archive_dir_path and backend.

        Returns self for convenience.  If sig_chain_warning is set to None,
        do not warn about unnecessary sig chains.  This is because there may
        naturally be some unecessary ones after a full backup.
        """
        self.values_set = 1

        # get remote filename list
        backend_filename_list = self.backend.list()
        log.Debug(_("%d file(s) exists on backend") % len(backend_filename_list))

        # get local filename list
        local_filename_list = self.archive_dir_path.listdir()
        log.Debug(_("%d file(s) exist in cache") % len(local_filename_list))

        # check for partial backups
        partials = []
        for local_filename in local_filename_list:
            pr = file_naming.parse(local_filename)
            if pr and pr.partial:
                partials.append(local_filename)

        # get various backup sets and chains
        (
            backup_chains,
            self.orphaned_backup_sets,
            self.incomplete_backup_sets,
        ) = self.get_backup_chains(partials + backend_filename_list)
        backup_chains = self.get_sorted_chains(backup_chains)
        self.all_backup_chains = backup_chains

        assert len(backup_chains) == len(
            self.all_backup_chains
        ), "get_sorted_chains() did something more than re-ordering"

        local_sig_chains, self.local_orphaned_sig_names = self.get_signature_chains(True)
        remote_sig_chains, self.remote_orphaned_sig_names = self.get_signature_chains(
            False, filelist=backend_filename_list
        )
        self.set_matched_chain_pair(local_sig_chains + remote_sig_chains, backup_chains)
        self.warn(sig_chain_warning)
        return self

    def set_matched_chain_pair(self, sig_chains, backup_chains):
        """
        Set self.matched_chain_pair and self.other_sig/backup_chains

        The latest matched_chain_pair will be set.  If there are both
        remote and local signature chains capable of matching the
        latest backup chain, use the local sig chain (it does not need
        to be downloaded).
        """
        sig_chains = sig_chains and self.get_sorted_chains(sig_chains)
        self.all_sig_chains = sig_chains
        self.other_backup_chains = backup_chains[:]
        self.matched_chain_pair = None
        if sig_chains and backup_chains:
            latest_backup_chain = backup_chains[-1]
            for i in range(len(sig_chains) - 1, -1, -1):
                if sig_chains[i].end_time == latest_backup_chain.end_time:
                    pass
                # See if the set before last matches:
                elif (
                    len(latest_backup_chain.get_all_sets()) >= 2
                    and sig_chains[i].end_time == latest_backup_chain.get_all_sets()[-2].end_time
                ):
                    # It matches, remove the last backup set:
                    log.Warn(_("Warning, discarding last backup set, because " "of missing signature file."))
                    self.incomplete_backup_sets.append(latest_backup_chain.incset_list[-1])
                    latest_backup_chain.incset_list = latest_backup_chain.incset_list[:-1]
                else:
                    continue

                # Found a matching pair:
                if self.matched_chain_pair is None:
                    self.matched_chain_pair = (sig_chains[i], latest_backup_chain)

                break

        if self.matched_chain_pair:
            self.other_backup_chains.remove(self.matched_chain_pair[1])

    def warn(self, sig_chain_warning):
        """
        Log various error messages if find incomplete/orphaned files
        """
        assert self.values_set

        if self.local_orphaned_sig_names:
            log.Warn(
                _("Warning, found the following local orphaned signature file(s):")
                + "\n"
                + "\n".join(map(os.fsdecode, self.local_orphaned_sig_names)),
                log.WarningCode.orphaned_sig,
            )

        if self.remote_orphaned_sig_names:
            log.Warn(
                _("Warning, found the following remote orphaned signature file(s):")
                + "\n"
                + "\n".join(map(os.fsdecode, self.remote_orphaned_sig_names)),
                log.WarningCode.orphaned_sig,
            )

        if self.all_sig_chains and sig_chain_warning and not self.matched_chain_pair:
            log.Warn(
                _("Warning, found signatures but no corresponding " "backup files"),
                log.WarningCode.unmatched_sig,
            )

        if self.incomplete_backup_sets:
            log.Warn(
                _("Warning, found incomplete backup sets, probably left " "from aborted session"),
                log.WarningCode.incomplete_backup,
            )

        if self.orphaned_backup_sets:
            log.Warn(
                _("Warning, found the following orphaned backup file(s):")
                + "\n"
                + "\n".join(map(str, self.orphaned_backup_sets)),
                log.WarningCode.orphaned_backup,
            )

    def get_backup_chains(self, filename_list):
        """
        Split given filename_list into chains

        Return value will be tuple (list of chains, list of sets, list
        of incomplete sets), where the list of sets will comprise sets
        not fitting into any chain, and the incomplete sets are sets
        missing files.
        """
        log.Debug(_("Extracting backup chains from list of files: %s") % [os.fsdecode(f) for f in filename_list])
        # First put filenames in set form
        sets = []

        def add_to_sets(filename):
            """
            Try adding filename to existing sets, or make new one
            """
            pr = file_naming.parse(filename)
            for set in sets:  # pylint: disable=redefined-builtin
                if set.add_filename(filename, pr):
                    log.Debug(_("File %s is part of known set") % (os.fsdecode(filename),))
                    break
            else:
                log.Debug(_("File %s is not part of a known set; creating new set") % (os.fsdecode(filename),))
                new_set = BackupSet(self.backend, self.action)
                if new_set.add_filename(filename, pr):
                    sets.append(new_set)
                else:
                    log.Debug(_("Ignoring file (rejected by backup set) '%s'") % os.fsdecode(filename))

        for f in filename_list:
            add_to_sets(f)
        sets, incomplete_sets = self.get_sorted_sets(sets)

        chains, orphaned_sets = [], []

        def add_to_chains(set):  # pylint: disable=redefined-builtin
            """
            Try adding set to existing chains, or make new one
            """
            if set.type == "full":
                new_chain = BackupChain(self.backend)
                new_chain.set_full(set)
                chains.append(new_chain)
                log.Debug(_("Found backup chain %s") % (new_chain.short_desc()))
            else:
                assert set.type == "inc"
                for chain in chains:
                    if chain.add_inc(set):
                        log.Debug(_("Added set %s to pre-existing chain %s") % (set.get_timestr(), chain.short_desc()))
                        break
                else:
                    log.Debug(_("Found orphaned set %s") % (set.get_timestr(),))
                    orphaned_sets.append(set)

        for s in sets:
            add_to_chains(s)
        return chains, orphaned_sets, incomplete_sets

    def get_sorted_sets(self, set_list):
        """
        Sort set list by end time, return (sorted list, incomplete)
        """
        time_set_pairs, incomplete_sets = [], []
        for set in set_list:  # pylint: disable=redefined-builtin
            if not set.is_complete():
                incomplete_sets.append(set)
            elif set.type == "full":
                time_set_pairs.append((set.time, set))
            else:
                time_set_pairs.append((set.end_time, set))
        time_set_pairs.sort(key=lambda x: x[0])
        return [p[1] for p in time_set_pairs], incomplete_sets

    def get_signature_chains(self, local, filelist=None):
        """
        Find chains in archive_dir_path (if local is true) or backend

        Use filelist if given, otherwise regenerate.  Return value is
        pair (list of chains, list of signature paths not in any
        chains).
        """

        def get_filelist():
            if filelist is not None:
                return filelist
            elif local:
                return self.archive_dir_path.listdir()
            else:
                return self.backend.list()

        def get_new_sigchain():
            """
            Return new empty signature chain
            """
            if local:
                return SignatureChain(True, self.archive_dir_path)
            else:
                return SignatureChain(False, self.backend)

        # Build initial chains from full sig filenames
        chains, new_sig_filenames = [], []
        for filename in get_filelist():
            pr = file_naming.parse(filename)
            if pr:
                if pr.type == "full-sig":
                    new_chain = get_new_sigchain()
                    assert new_chain.add_filename(filename, pr)
                    chains.append(new_chain)
                elif pr.type == "new-sig":
                    new_sig_filenames.append(filename)

        # Try adding new signatures to existing chains
        orphaned_filenames = []
        new_sig_filenames.sort(key=lambda x: int(file_naming.parse(x).start_time))
        for sig_filename in new_sig_filenames:
            for chain in chains:
                if chain.add_filename(sig_filename):
                    break
            else:
                orphaned_filenames.append(sig_filename)
        return chains, orphaned_filenames

    def get_sorted_chains(self, chain_list):
        """
        Return chains sorted by end_time.  If tie, local goes last
        """
        # Build dictionary from end_times to lists of corresponding chains
        endtime_chain_dict = {}
        for chain in chain_list:
            if chain.end_time in endtime_chain_dict:
                endtime_chain_dict[chain.end_time].append(chain)
            else:
                endtime_chain_dict[chain.end_time] = [chain]

        # Use dictionary to build final sorted list
        sorted_end_times = sorted(endtime_chain_dict.keys())
        sorted_chain_list = []
        for end_time in sorted_end_times:
            chain_list = endtime_chain_dict[end_time]
            if len(chain_list) == 1:
                sorted_chain_list.append(chain_list[0])
            else:
                assert len(chain_list) == 2
                if chain_list[0].backend:  # is remote, goes first
                    sorted_chain_list.append(chain_list[0])
                    sorted_chain_list.append(chain_list[1])
                else:  # is local, goes second
                    sorted_chain_list.append(chain_list[1])
                    sorted_chain_list.append(chain_list[0])

        return sorted_chain_list

    def get_backup_chain_at_time(self, time):
        """
        Return backup chain covering specified time

        Tries to find the backup chain covering the given time.  If
        there is none, return the earliest chain before, and failing
        that, the earliest chain.
        """
        if not self.all_backup_chains:
            raise CollectionsError("No backup chains found")

        covering_chains = [c for c in self.all_backup_chains if c.start_time <= time <= c.end_time]
        if len(covering_chains) > 1:
            raise CollectionsError("Two chains cover the given time")
        elif len(covering_chains) == 1:
            return covering_chains[0]

        old_chains = [c for c in self.all_backup_chains if c.end_time < time]
        if old_chains:
            return old_chains[-1]
        else:
            return self.all_backup_chains[0]  # no chains are old enough

    def get_signature_chain_at_time(self, time):
        """
        Return signature chain covering specified time

        Tries to find the signature chain covering the given time.  If
        there is none, return the earliest chain before, and failing
        that, the earliest chain.
        """
        if not self.all_sig_chains:
            raise CollectionsError("No signature chains found")

        covering_chains = [c for c in self.all_sig_chains if c.start_time <= time <= c.end_time]
        if covering_chains:
            return covering_chains[-1]  # prefer local if multiple sig chains

        old_chains = [c for c in self.all_sig_chains if c.end_time < time]
        if old_chains:
            return old_chains[-1]
        else:
            # no chains are old enough, give oldest and warn user
            oldest = self.all_sig_chains[0]
            if time < oldest.start_time:
                log.Warn(
                    _(
                        "No signature chain for the requested time. "
                        "Using oldest available chain, starting at time %s."
                    )
                    % dup_time.timetopretty(oldest.start_time),
                    log.WarningCode.no_sig_for_time,
                    dup_time.timetostring(oldest.start_time),
                )
            return oldest

    def get_extraneous(self):
        """
        Return list of the names of extraneous duplicity files

        A duplicity file is considered extraneous if it is
        recognizable as a duplicity file, but isn't part of some
        complete backup set, or current signature chain.
        """
        assert self.values_set
        local_filenames = []
        remote_filenames = []
        ext_containers = self.orphaned_backup_sets + self.incomplete_backup_sets
        for set_or_chain in ext_containers:
            if set_or_chain.backend:
                remote_filenames.extend(set_or_chain.get_filenames())
            else:
                local_filenames.extend(set_or_chain.get_filenames())
        local_filenames += self.local_orphaned_sig_names
        remote_filenames += self.remote_orphaned_sig_names
        return local_filenames, remote_filenames

    def sort_sets(self, setlist):
        """Return new list containing same elems of setlist, sorted by time"""
        pairs = sorted([(s.get_time(), s) for s in setlist])
        return [p[1] for p in pairs]

    def get_chains_older_than(self, t):
        """
        Returns a list of backup chains older than the given time t

        All of the times will be associated with an intact chain.
        Furthermore, none of the times will be of a chain which a newer
        set may depend on.  For instance, if set A is a full set older
        than t, and set B is an incremental based on A which is newer
        than t, then the time of set A will not be returned.
        """
        assert self.values_set
        old_chains = []
        for chain in self.all_backup_chains:
            if chain.end_time < t and (not self.matched_chain_pair or chain is not self.matched_chain_pair[1]):
                # don't delete the active (matched) chain
                old_chains.append(chain)
        return old_chains

    def get_signature_chains_older_than(self, t):
        """
        Returns a list of signature chains older than the given time t

        All of the times will be associated with an intact chain.
        Furthermore, none of the times will be of a chain which a newer
        set may depend on.  For instance, if set A is a full set older
        than t, and set B is an incremental based on A which is newer
        than t, then the time of set A will not be returned.
        """
        assert self.values_set
        old_chains = []
        for chain in self.all_sig_chains:
            if chain.end_time < t and (not self.matched_chain_pair or chain is not self.matched_chain_pair[0]):
                # don't delete the active (matched) chain
                old_chains.append(chain)
        return old_chains

    def get_last_full_backup_time(self):
        """
        Return the time of the last full backup,
        or 0 if there is none.
        """
        return self.get_nth_last_full_backup_time(1)

    def get_nth_last_full_backup_time(self, n):
        """
        Return the time of the nth to last full backup,
        or 0 if there is none.
        """
        chain = self.get_nth_last_backup_chain(n)
        if chain is None:
            return 0
        else:
            return chain.get_first().time

    def get_last_backup_chain(self):
        """
        Return the last full backup of the collection,
        or None if there is no full backup chain.
        """
        return self.get_nth_last_backup_chain(1)

    def get_nth_last_backup_chain(self, n):
        """
        Return the nth-to-last full backup of the collection,
        or None if there is less than n backup chains.

        NOTE: n = 1 -> time of latest available chain (n = 0 is not
        a valid input). Thus the second-to-last is obtained with n=2
        rather than n=1.
        """
        assert self.values_set
        assert n > 0

        if len(self.all_backup_chains) < n:
            return None

        sorted = self.all_backup_chains[:]  # pylint: disable=redefined-builtin
        sorted.sort(key=lambda x: x.get_first().time)

        sorted.reverse()
        return sorted[n - 1]

    def get_older_than(self, t):
        """
        Returns a list of backup sets older than the given time t

        All of the times will be associated with an intact chain.
        Furthermore, none of the times will be of a set which a newer
        set may depend on.  For instance, if set A is a full set older
        than t, and set B is an incremental based on A which is newer
        than t, then the time of set A will not be returned.
        """
        old_sets = []
        for chain in self.get_chains_older_than(t):
            old_sets.extend(chain.get_all_sets())
        return self.sort_sets(old_sets)

    def get_older_than_required(self, t):
        """
        Returns list of old backup sets required by new sets

        This function is similar to the previous one, but it only
        returns the times of sets which are old but part of the chains
        where the newer end of the chain is newer than t.
        """
        assert self.values_set
        new_chains = [c for c in self.all_backup_chains if c.end_time >= t]
        result_sets = []
        for chain in new_chains:
            old_sets = [s for s in chain.get_all_sets() if s.get_time() < t]
            result_sets.extend(old_sets)
        return self.sort_sets(result_sets)

    def get_file_changed_record(self, filepath):
        """
        Returns time line of specified file changed
        """
        # quick fix to spaces in filepath
        modified_filepath = filepath
        if " " in str(filepath):
            modified_filepath = '"' + filepath.replace(" ", r"\x20") + '"'

        if not self.matched_chain_pair:
            return ""

        all_backup_set = self.matched_chain_pair[1].get_all_sets()
        specified_file_backup_set = []
        specified_file_backup_type = []

        modified_filepath = os.fsencode(modified_filepath)
        for bs in all_backup_set:
            filelist = [fileinfo[1] for fileinfo in bs.get_files_changed()]
            if modified_filepath in filelist:
                specified_file_backup_set.append(bs)
                index = filelist.index(modified_filepath)
                specified_file_backup_type.append(bs.get_files_changed()[index][0])

        return FileChangedStatus(filepath, list(zip(specified_file_backup_type, specified_file_backup_set)))

    def get_all_file_changed_records(self, set_index):
        """
        Returns file changes in the specific backup set
        """
        if not self.matched_chain_pair:
            return ""

        all_backup_set = list(reversed(self.matched_chain_pair[1].get_all_sets()))
        return BackupSetChangesStatus(all_backup_set[set_index])

    def get_changes_in_set_json(self, set_index):
        """
        @param idex_set: index of the backup set.
            0: most recent backup
            max: full backup set
            -1 statistics for all sets of the most recent chain will be returned
        @return: statistics for "last - index_set" backup as json formated string.
        """
        if not self.matched_chain_pair:
            return ""
        all_backup_set = list(reversed(self.matched_chain_pair[1].get_all_sets()))
        json_obj = {}
        if set_index >= 0:
            all_backup_set = [all_backup_set[set_index]]
        for set in all_backup_set:
            name = f"{set.type}-{dup_time.timetostring(set.get_time())}"
            json_stat = set.get_jsonstat()
            json_obj[name] = {}
            json_obj[name]["json_stat"] = json_stat
            json_obj[name]["files_changed"] = {}
            for file in set.get_files_changed():
                json_obj[name]["files_changed"][os.fsdecode(file[1])] = file[0]
        return json.dumps(json_obj, cls=util.BytesEncoder, indent=4)


class FileChangedStatus(object):
    def __init__(self, filepath, fileinfo_list):
        self.filepath = filepath
        self.fileinfo_list = fileinfo_list

    def __str__(self):
        set_schema = "%20s   %30s  %20s"
        l = [
            "-------------------------",
            _("File: %s") % self.filepath,
            _("Total number of backup: %d") % len(self.fileinfo_list),
            set_schema % (_("Type of backup set:"), _("Time:"), _("Type of file change:")),
        ]

        for s in self.fileinfo_list:
            backup_type = s[0]
            backup_set = s[1]
            if backup_set.time:
                type = _("Full")  # pylint: disable=redefined-builtin
            else:
                type = _("Incremental")
            l.append(
                set_schema
                % (
                    type,
                    dup_time.timetopretty(backup_set.get_time()),
                    backup_type.title(),
                )
            )

        l.append("-------------------------")
        return "\n".join(l)


class BackupSetChangesStatus(object):
    def __init__(self, backup_set):
        self.backup_set = backup_set

    def __str__(self):
        changed_files = self.backup_set.get_files_changed()
        max_file_path_len = max([len(c[1]) for c in changed_files] + [5])
        set_schema = "%%-%ds  %%20s" % max_file_path_len
        l = (
            [
                "-------------------------",
                _(" Backup set time: %s") % (self.backup_set.get_timestr()),
                _("Total number of changes: %d") % len(changed_files),
                set_schema % (_("File:"), _("Type of file change:")),
            ]
            + [set_schema % (c[1].decode("utf-8"), c[0].decode("utf-8")) for c in changed_files]
            + ["-------------------------"]
        )
        return "\n".join(l)
