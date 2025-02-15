# -*- Mode:Python; indent-tabs-mode:nil; tab-width:4; encoding:utf-8 -*-
#
# duplicity -- Encrypted bandwidth efficient backup
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
#
# For more information see
#  http://duplicity.us
#  or
#  http://duplicity.gitlab.io
# .
# Please send mail to me or the mailing list if you find bugs or have
# any suggestions.


import os
import platform
import resource
import sys
import time
from dataclasses import dataclass
from textwrap import dedent
from typing import Dict

from duplicity import (
    __version__,
    backend_pool,
    cli_main,
    config,
    diffdir,
    dup_collections,
    dup_temp,
    dup_time,
    file_naming,
    gpg,
    log,
    log_util,
    manifest,
    patchdir,
    path,
    progress,
    tempdir,
    util,
)
from duplicity.errors import BadVolumeException

# If exit_val is not None, exit with given value at end.
exit_val = None


def getpass_safe(message):
    import getpass

    return getpass.getpass(message)


def get_passphrase(n, action, for_signing=False):
    """
    Check to make sure passphrase is indeed needed, then get
    the passphrase from environment, from gpg-agent, or user

    If n=3, a password is requested and verified. If n=2, the current
    password is verified. If n=1, a password is requested without
    verification for the time being.

    @type  n: int
    @param n: verification level for a passphrase being requested
    @type  action: string
    @param action: action to perform
    @type  for_signing: boolean
    @param for_signing: true if the passphrase is for a signing key, false if not
    @rtype: string
    @return: passphrase
    """

    # First try the environment
    try:
        if for_signing:
            return os.environ["SIGN_PASSPHRASE"]
        else:
            return os.environ["PASSPHRASE"]
    except KeyError:
        pass

    # check if we can reuse an already set (signing_)passphrase
    # if signing key is also an encryption key assume that the passphrase is identical
    if (
        for_signing
        and (
            config.gpg_profile.sign_key in config.gpg_profile.recipients
            or config.gpg_profile.sign_key in config.gpg_profile.hidden_recipients
        )
        and "PASSPHRASE" in os.environ
    ):  # noqa
        log.Notice(_("Reuse configured PASSPHRASE as SIGN_PASSPHRASE"))
        return os.environ["PASSPHRASE"]
    # if one encryption key is also the signing key assume that the passphrase is identical
    if (
        not for_signing
        and (
            config.gpg_profile.sign_key in config.gpg_profile.recipients
            or config.gpg_profile.sign_key in config.gpg_profile.hidden_recipients
        )
        and "SIGN_PASSPHRASE" in os.environ
    ):  # noqa
        log.Notice(_("Reuse configured SIGN_PASSPHRASE as PASSPHRASE"))
        return os.environ["SIGN_PASSPHRASE"]

    # Next, verify we need to ask the user

    # Assumptions:
    #   - encrypt-key has no passphrase
    #   - sign-key requires passphrase
    #   - gpg-agent supplies all, no user interaction

    # no passphrase if --no-encryption or --use-agent
    if not config.encryption or config.use_agent:
        return ""

    # these commands don't need a password
    elif action in [
        "collection-status",
        "list-current-files",
        "remove-all-but-n-full",
        "remove-all-inc-of-but-n-full",
        "remove-old",
    ]:
        return ""

    # for a full, inc, verify, we don't need a password if
    # there is no sign_key and there are recipients
    elif (
        action in ("full", "inc", "verify")
        and (config.gpg_profile.recipients or config.gpg_profile.hidden_recipients)
        and (not config.gpg_profile.sign_key or (not config.restart and not for_signing))
    ):
        return ""

    # Finally, ask the user for the passphrase
    else:
        log.Info(_("PASSPHRASE variable not set, asking user."))
        use_cache = True
        while True:
            # ask the user to enter a new passphrase to avoid an infinite loop
            # if the user made a typo in the first passphrase
            if use_cache and n == 2:
                if for_signing:
                    pass1 = config.gpg_profile.signing_passphrase
                else:
                    pass1 = config.gpg_profile.passphrase
            else:
                if for_signing:
                    if use_cache and config.gpg_profile.signing_passphrase:
                        pass1 = config.gpg_profile.signing_passphrase
                    else:
                        pass1 = getpass_safe(f"{_('GnuPG passphrase for signing key:')} ")
                else:
                    if use_cache and config.gpg_profile.passphrase:
                        pass1 = config.gpg_profile.passphrase
                    else:
                        pass1 = getpass_safe(f"{_('GnuPG passphrase for decryption:')} ")

            if n == 1:
                pass2 = pass1
            elif for_signing:
                pass2 = getpass_safe(_("Retype passphrase for signing key to confirm: "))
            else:
                pass2 = getpass_safe(_("Retype passphrase for decryption to confirm: "))

            if not pass1 == pass2:
                log.Log(
                    _("First and second passphrases do not match!  Please try again."), log.WARNING, force_print=True
                )
                use_cache = False
                continue

            if (
                not pass1
                and not (config.gpg_profile.recipients or config.gpg_profile.hidden_recipients)
                and not for_signing
            ):
                log.Log(
                    _("Cannot use empty passphrase with symmetric encryption!  Please try again."),
                    log.WARNING,
                    force_print=True,
                )
                use_cache = False
                continue

            return pass1


def dummy_backup(tarblock_iter):
    """
    Fake writing to backend, but do go through all the source paths.

    @type tarblock_iter: tarblock_iter
    @param tarblock_iter: iterator for current tar block

    @rtype: int
    @return: constant 0 (zero)
    """
    try:
        # Just spin our wheels
        while next(tarblock_iter):
            pass
    except StopIteration:
        pass
    log_util.Progress(None, diffdir.stats.SourceFileSize)
    return 0


def restart_position_iterator(tarblock_iter):
    """
    Fake writing to backend, but do go through all the source paths.
    Stop when we have processed the last file and block from the
    last backup.  Normal backup will proceed at the start of the
    next volume in the set.

    @type tarblock_iter: tarblock_iter
    @param tarblock_iter: iterator for current tar block

    @rtype: int
    @return: constant 0 (zero)
    """
    last_index = config.restart.last_index
    last_block = config.restart.last_block
    try:
        # Just spin our wheels
        iter_result = next(tarblock_iter)
        while iter_result:
            if tarblock_iter.previous_index == last_index:
                # If both the previous index and this index are done, exit now
                # before we hit the next index, to prevent skipping its first
                # block.
                if not last_block and not tarblock_iter.previous_block:
                    break
                # Only check block number if last_block is also a number
                if last_block and tarblock_iter.previous_block and tarblock_iter.previous_block > last_block:
                    break
            if tarblock_iter.previous_index > last_index:
                log.Warn(
                    _("File %s complete in backup set.\n" "Continuing restart on file %s.")
                    % (util.uindex(last_index), util.uindex(tarblock_iter.previous_index)),
                    log.ErrorCode.restart_file_not_found,
                )
                # We went too far! Stuff the data back into place before restarting
                tarblock_iter.queue_index_data(iter_result)
                break
            iter_result = next(tarblock_iter)
    except StopIteration:
        log.Warn(
            _("File %s missing in backup set.\n" "Continuing restart on file %s.")
            % (util.uindex(last_index), util.uindex(tarblock_iter.previous_index)),
            log.ErrorCode.restart_file_not_found,
        )


def write_multivol(backup_type, tarblock_iter, man_outfp, sig_outfp, backend):
    """
    Encrypt volumes of tarblock_iter and write to backend

    backup_type should be "inc" or "full" and only matters here when
    picking the filenames.  The path_prefix will determine the names
    of the files written to backend.  Also writes manifest file.
    Returns number of bytes written.

    @type backup_type: string
    @param backup_type: type of backup to perform, either 'inc' or 'full'
    @type tarblock_iter: tarblock_iter
    @param tarblock_iter: iterator for current tar block
    @type backend: callable backend object
    @param backend: I/O backend for selected protocol

    @rtype: int
    @return: bytes written
    """

    def get_indicies(tarblock_iter):
        """Return start_index and end_index of previous volume"""
        start_index, start_block = tarblock_iter.recall_index()
        if start_index is None:
            start_index = ()
            start_block = None
        if start_block:
            start_block -= 1
        end_index, end_block = tarblock_iter.get_previous_index()
        if end_index is None:
            end_index = start_index
            end_block = start_block
        if end_block:
            end_block -= 1
        return start_index, start_block, end_index, end_block

    def put(tdp, dest_filename, vol_num):
        """
        Retrieve file size *before* calling backend.put(), which may (at least
        in case of the localbackend) rename the temporary file to the target
        instead of copying.
        """
        putsize = tdp.getsize()
        if config.skip_volume != vol_num:  # for testing purposes only
            backend.put(tdp, dest_filename)
        res, msg = backend.validate(dest_filename, putsize, source_path=tdp)
        if not res:
            code_extra = f"{util.escape(dest_filename)}: {msg}"
            log_util.FatalError(
                _("File %s was corrupted during upload.") % os.fsdecode(dest_filename),
                log.ErrorCode.backend_validation_failed,
                code_extra,
            )

        if tdp.stat:
            tdp.delete()
        return putsize

    def validate_encryption_settings(backup_set, manifest):
        """
        When restarting a backup, we have no way to verify that the current
        passphrase is the same as the one used for the beginning of the backup.
        This is because the local copy of the manifest is unencrypted and we
        don't need to decrypt the existing volumes on the backend.  To ensure
        that we are using the same passphrase, we manually download volume 1
        and decrypt it with the current passphrase.  We also want to confirm
        that we're using the same encryption settings (i.e. we don't switch
        from encrypted to non in the middle of a backup chain), so we check
        that the vol1 filename on the server matches the settings of this run.
        """
        if (config.gpg_profile.recipients or config.gpg_profile.hidden_recipients) and not config.gpg_profile.sign_key:
            # When using gpg encryption without a signing key, we skip this validation
            # step to ensure that we can still backup without needing the secret key
            # on the machine.
            return

        vol1_filename = file_naming.get(backup_type, 1, encrypted=config.encryption, gzipped=config.compression)
        if vol1_filename != backup_set.volume_name_dict[1]:
            log_util.FatalError(
                _("Restarting backup, but current encryption " "settings do not match original settings"),
                log.ErrorCode.enryption_mismatch,
            )

        # Settings are same, let's check passphrase itself if we are encrypted
        if config.encryption:
            fileobj = restore_get_enc_fileobj(config.backend, vol1_filename, manifest.volume_info_dict[1])
            fileobj.close()

    @dataclass
    class CommandMetaData:
        vol_num: int
        path_obj: path.Path
        vol_info: manifest.VolumeInfo
        transfer_success = False
        manifest_written = False

    def collect_put_results(bytes_written: int, backend_pooler, command2vol_map: Dict[int, CommandMetaData]):
        for result in backend_pooler.results_since_last_call():
            track_id = result.track_id
            size = result.result
            bytes_written += size
            progress.report_transfer(size, size)
            log_util.Progress(_("Processed volume %d") % command2vol_map[track_id].vol_num, bytes_written)
            command2vol_map[track_id].transfer_success = True
            if command2vol_map[track_id].path_obj.stat:
                command2vol_map[track_id].path_obj.delete()
            if config.progress:
                progress.tracker.snapshot_progress(command2vol_map[track_id].vol_num)
            log.Debug(
                f"Transfer of {command2vol_map[track_id].path_obj.get_filename()} with id {track_id} and size "
                f"{size} took {result.get_runtime()}"
            )

    def write_manifest_in_sequence(mf, mf_file, command2vol_map: Dict[int, CommandMetaData]):
        """
        Ensure volume info is written only if the volume transfer was successful and in sequence
        without gap otherwise missing volumes won't be detected and data is missing.
        """
        try:
            i = iter(command2vol_map.keys())
            info = command2vol_map[next(i)]
            while info.manifest_written and info.transfer_success:
                # skip all entries already written
                info = command2vol_map[next(i)]
            while info.transfer_success:
                # if next volumes are transferred
                if not info.manifest_written:
                    mf.add_volume_info(info.vol_info)
                info.manifest_written = True
                info = command2vol_map[next(i)]
                if info.vol_num == 1:
                    mf_file.to_partial()
                else:
                    mf_file.flush()
        except StopIteration:
            pass  # no manifest to update

    if not config.restart:
        # normal backup start
        vol_num = 0
        mf = manifest.Manifest(fh=man_outfp)
        mf.set_dirinfo()
    else:
        # restart from last known position
        mf = config.restart.last_backup.get_local_manifest()
        config.restart.checkManifest(mf)
        config.restart.setLastSaved(mf)
        if not (config.s3_use_deep_archive or config.s3_use_glacier or config.s3_use_glacier_ir):
            validate_encryption_settings(config.restart.last_backup, mf)
        else:
            log.Warn(_("Skipping encryption validation due to glacier/deep storage"))
        mf.fh = man_outfp
        last_block = config.restart.last_block
        log.Notice(
            _("Restarting after volume %s, file %s, block %s")
            % (config.restart.start_vol, util.uindex(config.restart.last_index), config.restart.last_block)
        )
        vol_num = config.restart.start_vol
        restart_position_iterator(tarblock_iter)

    at_end = 0
    bytes_written = 0

    # If --progress option is given, initiate a background thread that will
    # periodically report progress to the Log.
    if config.progress:
        progress.tracker.set_start_volume(vol_num + 1)
        progress.progress_thread.start()

    backend_pooler = None
    command2vol_map: Dict[int, CommandMetaData] = {}
    if config.concurrency > 0:
        backend_pooler = backend_pool.BackendPool(backend.backend.parsed_url.url_string, processes=config.concurrency)

    while not at_end:
        # set up iterator
        tarblock_iter.remember_next_index()  # keep track of start index

        # Create volume
        vol_num += 1
        dest_filename = file_naming.get(backup_type, vol_num, encrypted=config.encryption, gzipped=config.compression)
        tdp = dup_temp.new_tempduppath(file_naming.parse(dest_filename))

        # write volume
        if config.encryption:
            at_end = gpg.GPGWriteFile(tarblock_iter, tdp.name, config.gpg_profile, config.volsize)
        elif config.compression:
            at_end = gpg.GzipWriteFile(tarblock_iter, tdp.name, config.volsize)
        else:
            at_end = gpg.PlainWriteFile(tarblock_iter, tdp.name, config.volsize)
        tdp.setdata()

        # Add volume information to manifest
        vi = manifest.VolumeInfo()
        vi.set_info(vol_num, *get_indicies(tarblock_iter))
        vi.set_hash("SHA1", gpg.get_hash("SHA1", tdp))

        # Checkpoint after each volume so restart has a place to restart.
        # Note that until after the first volume, all files are temporary.
        if vol_num == 1:
            sig_outfp.to_partial()
        else:
            sig_outfp.flush()

        if config.skip_if_no_change and diffdir.stats.DeltaEntries == 0 and at_end and vol_num == 1:
            # if nothing changed, skip upload if configured.
            msg = _("Skipped volume upload, as effectivly nothing has changed")
            log_util.Progress(msg, diffdir.stats.SourceFileSize)
            log.Notice(_(msg))
            config.skipped_inc = True
            tdp.delete()
            continue

        if config.concurrency > 0 and backend_pooler:
            try:
                # use process pool the write volumes in the background.
                progress.report_transfer(0, tdp.getsize())
                track_id = backend_pooler.command_throttled(backend.put_validated.__name__, args=(tdp, dest_filename))
                command2vol_map[track_id] = CommandMetaData(vol_num, tdp, vi)
                collect_put_results(bytes_written, backend_pooler, command2vol_map)
                write_manifest_in_sequence(mf, man_outfp, command2vol_map)
            except (Exception, SystemExit) as e:
                # ensure pool processes terminate clean
                backend_pooler.shutdown()
                raise

        else:
            # write Volume to backend - blocking
            mf.add_volume_info(vi)

            if vol_num == 1:
                man_outfp.to_partial()
            else:
                man_outfp.flush()

            bytes_written += put(tdp, dest_filename, vol_num)

            # Log human-readable version as well as raw numbers for machine consumers
            log_util.Progress(_("Processed volume %d") % vol_num, diffdir.stats.SourceFileSize)
            # Snapshot (serialize) progress now as a Volume has been completed.
            # This is always the last restore point when it comes to restart a failed backup
            if config.progress:
                progress.tracker.snapshot_progress(vol_num)

    if backend_pooler:
        try:
            # wait for background commands, collect some stats and shutdown clean.
            log.Debug("Collecting remaining results from backend pool.")
            while True and backend_pooler:
                collect_put_results(bytes_written, backend_pooler, command2vol_map)
                write_manifest_in_sequence(mf, man_outfp, command2vol_map)
                if backend_pooler.get_queue_length() == 0:
                    break
                else:
                    log.Debug(f"Still {backend_pooler.get_queue_length()} commands left, waiting ...")
                    time.sleep(2)
            # print some stats, that can be used to track efficiency of concurrent transfers.
            stats = backend_pooler.get_stats()
            log.Info(
                f'Transferred {stats["count"]} volumes, a volume took avg: {stats["time"]["avg"]}, '
                + f'max: {stats["time"]["max"]}, min: {stats["time"]["min"]}'
            )
            # double check that all volumes are transferred
            if not any([x.transfer_success for x in command2vol_map.values()]) and not config.skipped_inc:
                failed_volume_numbers = [
                    x.vol_info.volume_number for x in command2vol_map.values() if not x.transfer_success
                ]
                log_util.FatalError(f"Volumes with number {failed_volume_numbers} were not transferred successful.")
            # Add some stats, accessible with `--jsonstats`. Not the most elegant way, but it is working.
            diffdir.stats.stat_attrs += ("ConcurrentTransferStats",)
            diffdir.stats.set_stat("ConcurrentTransferStats", stats)
        finally:
            # make sure pool get terminated gracefully in any case.
            backend_pooler.shutdown()

    # Upload the collection summary.
    # bytes_written += write_manifest(mf, backup_type, backend)
    mf.set_files_changed_info(diffdir.stats.get_delta_entries_file())

    return bytes_written


def get_man_fileobj(backup_type):
    """
    Return a fileobj opened for writing, save results as manifest

    Save manifest in config.archive_dir_path gzipped.
    Save them on the backend encrypted as needed.

    @type man_type: string
    @param man_type: either "full" or "new"

    @rtype: fileobj
    @return: fileobj opened for writing
    """
    assert backup_type == "full" or backup_type == "inc"

    part_man_filename = file_naming.get(backup_type, manifest=True, partial=True)
    perm_man_filename = file_naming.get(backup_type, manifest=True)
    remote_man_filename = file_naming.get(backup_type, manifest=True, encrypted=config.encryption)

    fh = dup_temp.get_fileobj_duppath(
        config.archive_dir_path, part_man_filename, perm_man_filename, remote_man_filename
    )
    return fh


def get_sig_fileobj(sig_type):
    """
    Return a fileobj opened for writing, save results as signature

    Save signatures in config.archive_dir gzipped.
    Save them on the backend encrypted as needed.

    @type sig_type: string
    @param sig_type: either "full-sig" or "new-sig"

    @rtype: fileobj
    @return: fileobj opened for writing
    """
    assert sig_type in ["full-sig", "new-sig"]

    part_sig_filename = file_naming.get(sig_type, gzipped=False, partial=True)
    perm_sig_filename = file_naming.get(sig_type, gzipped=True)
    remote_sig_filename = file_naming.get(sig_type, encrypted=config.encryption, gzipped=config.compression)

    fh = dup_temp.get_fileobj_duppath(
        config.archive_dir_path, part_sig_filename, perm_sig_filename, remote_sig_filename, overwrite=True
    )
    return fh


def get_stat_fileobj(stat_type):
    """
    Return a fileobj opened for writing, save statistic as json

    Save statistics in config.archive_dir gzipped.
    Save them on the backend encrypted as needed.

    @type stat_type: string
    @param stat_type: either "full-stat" or "new-stat"

    @rtype: fileobj
    @return: fileobj opened for writing
    """
    assert stat_type in ["full-stat", "inc-stat"]

    part_stat_filename = file_naming.get(stat_type, gzipped=False, partial=True)
    perm_stat_filename = file_naming.get(stat_type, gzipped=True)
    remote_stat_filename = file_naming.get(stat_type, encrypted=config.encryption, gzipped=config.compression)

    fh = dup_temp.get_fileobj_duppath(
        config.archive_dir_path, part_stat_filename, perm_stat_filename, remote_stat_filename, overwrite=True
    )
    return fh


def full_backup(col_stats):
    """
    Do full backup of directory to backend, using archive_dir_path

    @type col_stats: CollectionStatus object
    @param col_stats: collection status

    @rtype: void
    @return: void
    """
    if config.progress:
        progress.tracker = progress.ProgressTracker()
        # Fake a backup to compute total of moving bytes
        tarblock_iter = diffdir.DirFull(config.select)
        dummy_backup(tarblock_iter)
        # Store computed stats to compute progress later
        progress.tracker.set_evidence(diffdir.stats, True)
        # Reinit the config.select iterator, so
        # the core of duplicity can rescan the paths
        cli_main.set_selection()
        progress.progress_thread = progress.LogProgressThread()

    if config.dry_run:
        tarblock_iter = diffdir.DirFull(config.select)
        bytes_written = dummy_backup(tarblock_iter)
        col_stats.set_values(sig_chain_warning=None)
    else:
        sig_outfp = get_sig_fileobj("full-sig")
        man_outfp = get_man_fileobj("full")
        tarblock_iter = diffdir.DirFull_WriteSig(config.select, sig_outfp)
        bytes_written = write_multivol("full", tarblock_iter, man_outfp, sig_outfp, config.backend)

        # close sig file, send to remote, and rename to final
        sig_outfp.close()
        sig_outfp.to_remote()
        sig_outfp.to_final()

        # close manifest, send to remote, and rename to final
        man_outfp.close()
        man_outfp.to_remote()
        man_outfp.to_final()

        if config.progress:
            # Terminate the background thread now, if any
            progress.progress_thread.finished = True
            progress.progress_thread.join()
            log_util.TransferProgress(
                100.0,
                0,
                progress.tracker.total_bytecount,
                progress.tracker.total_elapsed_seconds(),
                progress.tracker.speed,
                False,
            )

        col_stats.set_values(sig_chain_warning=None)

    write_json_stat("full-stat", bytes_written, col_stats)
    print_statistics(diffdir.stats, bytes_written)


def check_sig_chain(col_stats):
    """
    Get last signature chain for inc backup, or None if none available

    @type col_stats: CollectionStatus object
    @param col_stats: collection status
    """
    if not col_stats.matched_chain_pair:
        if config.action == "inc" and not config.implied_inc:
            log_util.FatalError(
                _(
                    "Fatal Error: Unable to start incremental backup.  "
                    "Old signatures not found and incremental specified"
                ),
                log.ErrorCode.inc_without_sigs,
            )
        else:
            log.Warn(_("No signatures found, switching to full backup."))
        return None
    return col_stats.matched_chain_pair[0]


def print_statistics(stats, bytes_written):  # pylint: disable=unused-argument
    """
    If config.print_statistics, print stats after adding bytes_written

    @rtype: void
    @return: void
    """
    if config.print_statistics:
        diffdir.stats.TotalDestinationSizeChange = bytes_written
        logstring = diffdir.stats.get_stats_logstring(_("Backup Statistics"))
        log.Log(logstring, log.NOTICE, force_print=True)


def incremental_backup(sig_chain, col_stats=None):
    """
    Do incremental backup of directory to backend, using archive_dir_path

    @rtype: void
    @return: void
    """
    if not config.restart:
        dup_time.setprevtime(sig_chain.end_time)
        if dup_time.curtime == dup_time.prevtime:
            time.sleep(2)
            dup_time.setcurtime()
            assert (
                dup_time.curtime != dup_time.prevtime
            ), "time not moving forward at appropriate pace - system clock issues?"

    if config.progress:
        progress.tracker = progress.ProgressTracker()
        # Fake a backup to compute total of moving bytes
        tarblock_iter = diffdir.DirDelta(config.select, sig_chain.get_fileobjs())
        dummy_backup(tarblock_iter)
        # Store computed stats to compute progress later
        progress.tracker.set_evidence(diffdir.stats, False)
        # Reinit the config.select iterator, so
        # the core of duplicity can rescan the paths
        cli_main.set_selection()
        progress.progress_thread = progress.LogProgressThread()

    if config.dry_run:
        tarblock_iter = diffdir.DirDelta(config.select, sig_chain.get_fileobjs())
        bytes_written = dummy_backup(tarblock_iter)
    else:
        new_sig_outfp = get_sig_fileobj("new-sig")
        new_man_outfp = get_man_fileobj("inc")
        tarblock_iter = diffdir.DirDelta_WriteSig(config.select, sig_chain.get_fileobjs(), new_sig_outfp)
        bytes_written = write_multivol("inc", tarblock_iter, new_man_outfp, new_sig_outfp, config.backend)

        if not config.skipped_inc:
            # write metadata to cache and remote
            # close sig file and rename to final
            new_sig_outfp.close()
            new_sig_outfp.to_remote()
            new_sig_outfp.to_final()

            # close manifest and rename to final
            new_man_outfp.close()
            new_man_outfp.to_remote()
            new_man_outfp.to_final()

        else:
            # drop metadata as no files as changed.
            new_sig_outfp.close()
            new_sig_outfp.clean_up()
            new_man_outfp.close()
            new_man_outfp.clean_up()

        if config.progress:
            # Terminate the background thread now, if any
            progress.progress_thread.finished = True
            progress.progress_thread.join()
            log_util.TransferProgress(
                100.0,
                0,
                progress.tracker.total_bytecount,
                progress.tracker.total_elapsed_seconds(),
                progress.tracker.speed,
                False,
            )

    write_json_stat("inc-stat", bytes_written, col_stats)
    print_statistics(diffdir.stats, bytes_written)


def write_json_stat(stat_type, bytes_written, col_stats):
    """
    If "--jsonstat" is given in the command line, write extra statistic file.

    @type stat_type: string
    @param stat_type: Name of the json_stat should be full-stat or inc-stat
    @type bytes_written: int
    @param bytes_written: no of bytes written, in this run
    @type col_stats: CollectionStatus object
    @param col_stats: collection status
    """
    if config.jsonstat:
        json_stat = diffdir.stats.get_stats_json(col_stats)
        log.Log(json_stat, log.NOTICE, force_print=True)
        if not config.dry_run:
            stat_outfp = get_stat_fileobj(stat_type)
            diffdir.stats.TotalDestinationSizeChange = bytes_written
            stat_outfp.write(json_stat.encode())
            stat_outfp.close()
            if not config.skipped_inc:
                stat_outfp.to_remote()
                stat_outfp.to_final()
            else:
                stat_outfp.clean_up()


def list_current(col_stats):
    """
    List the files current in the archive (examining signature only)

    @type col_stats: CollectionStatus object
    @param col_stats: collection status

    @rtype: void
    @return: void
    """
    time = config.restore_time or dup_time.curtime
    sig_chain = col_stats.get_signature_chain_at_time(time)
    path_iter = diffdir.get_combined_path_iter(sig_chain.get_fileobjs(time))
    for path in path_iter:
        if path.difftype != "deleted":
            user_info = f"{dup_time.timetopretty(path.getmtime())} {os.fsdecode(path.get_relative_path())}"
            log_info = f"{dup_time.timetostring(path.getmtime())} {util.escape(path.get_relative_path())} {path.type}"
            log.Log(user_info, log.INFO, log.InfoCode.file_list, log_info, True)


def restore(col_stats):
    """
    Restore archive in config.backend to config.local_path

    @type col_stats: CollectionStatus object
    @param col_stats: collection status

    @rtype: void
    @return: void
    """
    if config.dry_run:
        # Only prints list of required volumes when running dry
        restore_get_patched_rop_iter(col_stats)
        return
    if not patchdir.Write_ROPaths(config.local_path, restore_get_patched_rop_iter(col_stats)):
        if config.restore_path:
            log_util.FatalError(
                _("%s not found in archive - no files restored.") % (os.fsdecode(config.restore_path)),
                log.ErrorCode.restore_path_not_found,
            )
        else:
            log_util.FatalError(_("No files found in archive - nothing restored."), log.ErrorCode.no_restore_files)


def restore_get_patched_rop_iter(col_stats):
    """
    Return iterator of patched ROPaths of desired restore data

    @type col_stats: CollectionStatus object
    @param col_stats: collection status
    """
    if config.restore_path:
        index = tuple(config.restore_path.split(b"/"))
    else:
        index = ()
    time = config.restore_time or dup_time.curtime
    backup_chain = col_stats.get_backup_chain_at_time(time)
    assert backup_chain, col_stats.all_backup_chains
    backup_setlist = backup_chain.get_sets_at_time(time)
    num_vols = 0
    for s in backup_setlist:
        num_vols += len(s)
    cur_vol = [0]

    def get_fileobj_iter(backup_set):
        """Get file object iterator from backup_set contain given index"""
        manifest = backup_set.get_manifest()
        volumes = manifest.get_containing_volumes(index)
        for vol_num in volumes:
            try:
                fobj = restore_get_enc_fileobj(
                    backup_set.backend, backup_set.volume_name_dict[vol_num], manifest.volume_info_dict[vol_num]
                )
                if fobj is not None:
                    yield fobj
            except BadVolumeException as e:
                yield e

            cur_vol[0] += 1
            log_util.Progress(_("Processed volume %d of %d") % (cur_vol[0], num_vols), cur_vol[0], num_vols)

    if hasattr(config.backend, "pre_process_download_batch") or config.dry_run:
        file_names = []
        for backup_set in backup_setlist:
            manifest = backup_set.get_manifest()
            volumes = manifest.get_containing_volumes(index)
            for vol_num in volumes:
                file_names.append(backup_set.volume_name_dict[vol_num])
        if config.dry_run:
            log.Notice("Required volumes to restore:\n\t" + "\n\t".join(file_name.decode() for file_name in file_names))
            return None
        else:
            config.backend.pre_process_download_batch(file_names)

    fileobj_iters = list(map(get_fileobj_iter, backup_setlist))
    tarfiles = list(map(patchdir.TarFile_FromFileobjs, fileobj_iters))
    return patchdir.tarfiles2rop_iter(tarfiles, index)


def restore_get_enc_fileobj(backend, filename, volume_info):
    """
    Return plaintext fileobj from encrypted filename on backend

    If volume_info is set, the hash of the file will be checked,
    assuming some hash is available.  Also, if config.sign_key is
    set, a fatal error will be raised if file not signed by sign_key.

    with --ignore-errors set continue on hash mismatch

    """
    for n in range(1, config.num_retries + 1):
        """get the remote file"""
        parseresults = file_naming.parse(filename)
        tdp = dup_temp.new_tempduppath(parseresults)
        backend.get(filename, tdp)

        """ verify hash of the remote file """
        verified, hash_pair, calculated_hash = restore_check_hash(volume_info, tdp)
        if verified:
            break
        else:
            error_msg = "%s\n %s\n %s\n %s\n" % (
                _("Invalid data - %s hash mismatch for file:") % hash_pair[0],
                os.fsdecode(filename),
                _("Calculated hash: %s") % calculated_hash,
                _("Manifest hash: %s") % hash_pair[1],
            )
            log.Error(error_msg, code=log.ErrorCode.mismatched_hash)
    else:
        if config.ignore_errors:
            exc = BadVolumeException(f"Hash mismatch for: {os.fsdecode(filename)}")
            log.Warn(
                _("IGNORED_ERROR: Warning: ignoring error as requested: %s: %s")
                % (exc.__class__.__name__, util.uexc(exc))
            )
            # Do not try to actually read it as it is corrupted!
            return None
        else:
            log_util.FatalError(error_msg, code=log.ErrorCode.mismatched_hash)
    fileobj = tdp.filtered_open_with_delete("rb")
    if parseresults.encrypted and config.gpg_profile.sign_key:
        restore_add_sig_check(fileobj)
    return fileobj


def restore_check_hash(volume_info, vol_path):
    """
    Check the hash of vol_path path against data in volume_info

    @rtype: boolean
    @return: true (verified) / false (failed)
    """
    hash_pair = volume_info.get_best_hash()
    if hash_pair:
        calculated_hash = gpg.get_hash(hash_pair[0], vol_path)
        if calculated_hash != hash_pair[1]:
            return False, hash_pair, calculated_hash
    """ reached here, verification passed """
    return True, hash_pair, calculated_hash


def restore_add_sig_check(fileobj):
    """
    Require signature when closing fileobj matches sig in gpg_profile

    @rtype: void
    @return: void
    """
    assert isinstance(fileobj, dup_temp.FileobjHooked) and isinstance(fileobj.fileobj, gpg.GPGFile), fileobj

    def check_signature():
        """Thunk run when closing volume file"""
        actual_sig = fileobj.fileobj.get_signature()
        actual_sig = "None" if actual_sig is None else actual_sig
        sign_key = config.gpg_profile.sign_key
        sign_key = "None" if sign_key is None else sign_key
        ofs = -min(len(actual_sig), len(sign_key))
        if actual_sig[ofs:] != sign_key[ofs:]:
            log_util.FatalError(
                _("Volume was signed by key %s, not %s") % (actual_sig[ofs:], sign_key[ofs:]),
                log.ErrorCode.unsigned_volume,
            )

    fileobj.addhook(check_signature)


def verify(col_stats):
    """
    Verify files, logging differences

    @type col_stats: CollectionStatus object
    @param col_stats: collection status

    @rtype: void
    @return: void
    """
    global exit_val
    collated = diffdir.collate2iters(restore_get_patched_rop_iter(col_stats), config.select)
    diff_count = 0
    total_count = 0
    for backup_ropath, current_path in collated:
        if not backup_ropath:
            backup_ropath = path.ROPath(current_path.index)
        if not current_path:
            current_path = path.ROPath(backup_ropath.index)
        if not backup_ropath.compare_verbose(current_path, config.compare_data):
            diff_count += 1
        total_count += 1
    # Unfortunately, ngettext doesn't handle multiple number variables, so we
    # split up the string.
    log.Notice(
        _("Verify complete: %s, %s.")
        % (_("%d file(s) compared") % total_count, _("%d difference(s) found") % diff_count)
    )
    if diff_count >= 1:
        exit_val = 1


def cleanup(col_stats):
    """
    Delete the extraneous files in the current backend

    @type col_stats: CollectionStatus object
    @param col_stats: collection status

    @rtype: void
    @return: void
    """
    ext_local, ext_remote = col_stats.get_extraneous()
    extraneous = ext_local + ext_remote
    if not extraneous:
        log.Warn(_("No extraneous files found, nothing deleted in cleanup."))
        return

    filestr = "\n".join(map(os.fsdecode, extraneous))
    if config.force:
        log.Notice(f"{_('Deleting these file(s) from backend:')}\n{filestr}")
        if not config.dry_run:
            col_stats.backend.delete(ext_remote)
            for fn in ext_local:
                try:
                    config.archive_dir_path.append(fn).delete()
                except Exception:
                    pass
    else:
        log.Notice(
            _("Found the following file(s) to delete:")
            + "\n"
            + filestr
            + "\n"
            + _("Run duplicity again with the --force option to actually delete.")
        )


def remove_all_but_n_full(col_stats):
    """
    Remove backup files older than the last n full backups.

    @type col_stats: CollectionStatus object
    @param col_stats: collection status

    @rtype: void
    @return: void
    """
    assert config.keep_chains is not None

    config.remove_time = col_stats.get_nth_last_full_backup_time(config.keep_chains)

    remove_old(col_stats)


def remove_old(col_stats):
    """
    Remove backup files older than config.remove_time from backend

    @type col_stats: CollectionStatus object
    @param col_stats: collection status

    @rtype: void
    @return: void
    """
    assert config.remove_time is not None

    def set_times_str(setlist):
        """Return string listing times of sets in setlist"""
        return "\n".join([dup_time.timetopretty(s.get_time()) for s in setlist])

    def chain_times_str(chainlist):
        """Return string listing times of chains in chainlist"""
        return "\n".join([dup_time.timetopretty(s.end_time) for s in chainlist])

    req_list = col_stats.get_older_than_required(config.remove_time)
    if req_list:
        log.Warn(
            "%s\n%s\n%s"
            % (
                _("There are backup set(s) at time(s):"),
                set_times_str(req_list),
                _("Which can't be deleted because newer sets depend on them."),
            )
        )

    if col_stats.matched_chain_pair and col_stats.matched_chain_pair[1].end_time < config.remove_time:
        log.Warn(
            _(
                "Current active backup chain is older than specified time.  "
                "However, it will not be deleted.  To remove all your backups, "
                "manually purge the repository."
            )
        )

    chainlist = col_stats.get_chains_older_than(config.remove_time)

    if config.action == "remove-all-inc-of-but-n-full":
        # ignore chains without incremental backups:
        chainlist = list(
            x
            for x in chainlist
            if (isinstance(x, dup_collections.SignatureChain) and x.inclist)
            or (isinstance(x, dup_collections.BackupChain) and x.incset_list)
        )

    if not chainlist:
        log.Notice(_("No old backup sets found, nothing deleted."))
        return
    if config.force:
        log.Notice(_("Deleting backup chain(s) at time:") + "\n" + chain_times_str(chainlist))
        # Add signature files too, since they won't be needed anymore
        chainlist += col_stats.get_signature_chains_older_than(config.remove_time)
        chainlist.reverse()  # save oldest for last
        for chain in chainlist:
            # if action is remove_all_inc_of_but_n_full, remove only
            # incrementals one and not full
            if config.action == "remove-all-inc-of-but-n-full":
                if isinstance(chain, dup_collections.SignatureChain):
                    chain_desc = _("Deleting any incremental signature chain rooted at %s")
                else:
                    chain_desc = _("Deleting any incremental backup chain rooted at %s")
            else:
                if isinstance(chain, dup_collections.SignatureChain):
                    chain_desc = _("Deleting complete signature chain %s")
                else:
                    chain_desc = _("Deleting complete backup chain %s")
            log.Notice(chain_desc % dup_time.timetopretty(chain.end_time))
            if not config.dry_run:
                chain.delete(keep_full=(config.action == "remove-all-inc-of-but-n-full"))
        col_stats.set_values(sig_chain_warning=None)
    else:
        log.Notice(
            _("Found old backup chain(s) at the following time:")
            + "\n"
            + chain_times_str(chainlist)
            + "\n"
            + _("Rerun command with --force option to actually delete.")
        )


def sync_archive(col_stats):
    """
    Synchronize local archive manifest file and sig chains to remote archives.
    Copy missing files from remote to local as needed to make sure the local
    archive is synchronized to remote storage.

    @rtype: void
    @return: void
    """
    suffixes = [b".g", b".gpg", b".z", b".gz", b".part"]

    def is_needed(filename):
        """Indicates if the metadata file should be synced.

        In full sync mode, or if there's a collection misbehavior, all files
        are needed.

        Otherwise, only the metadata for the target chain needs sync.
        """
        if config.metadata_sync_mode == "full":
            return True
        assert config.metadata_sync_mode == "partial"
        parsed = file_naming.parse(filename)
        try:
            target_chain = col_stats.get_backup_chain_at_time(config.restore_time or dup_time.curtime)
        except dup_collections.CollectionsError:
            # With zero or multiple chains at this time, do a full sync
            return True
        if parsed.start_time is None and parsed.end_time is None:
            start_time = end_time = parsed.time
        else:
            start_time = parsed.start_time
            end_time = parsed.end_time

        return end_time >= target_chain.start_time and start_time <= target_chain.end_time

    def get_metafiles(filelist):
        """
        Return metafiles of interest from the file list.
        Files of interest are:
          sigtar - signature files
          manifest - signature files
          duplicity partial versions of the above
        Files excluded are:
          non-duplicity files

        @rtype: list
        @return: list of duplicity metadata files
        """
        metafiles = {}
        partials = {}
        need_passphrase = False
        for fn in filelist:
            pr = file_naming.parse(fn)
            if not pr:
                continue
            if pr.encrypted:
                need_passphrase = True
            if pr.type in ["full-sig", "new-sig"] or pr.manifest:
                base, ext = os.path.splitext(fn)
                if ext not in suffixes:
                    base = fn
                if pr.partial:
                    partials[base] = fn
                else:
                    metafiles[base] = fn
        return metafiles, partials, need_passphrase

    def copy_raw(src_iter, filename):
        """
        Copy data from src_iter to filename
        """
        file = open(filename, "wb")
        while True:
            try:
                data = src_iter.__next__().data
            except StopIteration:
                break
            file.write(data)
        file.close()

    def resolve_basename(fn):
        """
        @return: (parsedresult, local_name, remote_name)
        """
        pr = file_naming.parse(fn)

        base, ext = os.path.splitext(fn)
        if ext not in suffixes:
            base = fn

        suffix = file_naming.get_suffix(False, not pr.manifest)
        loc_name = base + suffix

        return pr, loc_name, fn

    def remove_local(fn):
        del_name = config.archive_dir_path.append(fn).name

        log.Notice(_("Deleting local %s (not authoritative at backend).") % os.fsdecode(del_name))
        try:
            util.ignore_missing(os.unlink, del_name)
        except Exception as e:
            log.Warn(_("Unable to delete %s: %s") % (os.fsdecode(del_name), util.uexc(e)))

    def copy_to_local(fn):
        """
        Copy remote file fn to local cache.
        """

        class Block(object):
            """
            Data block to return from SrcIter
            """

            def __init__(self, data):
                self.data = data

        class SrcIter(object):
            """
            Iterate over source and return Block of data.
            """

            def __init__(self, fileobj):
                self.fileobj = fileobj

            def __next__(self):
                try:
                    res = Block(self.fileobj.read(self.get_read_size()))
                except Exception as e:
                    if hasattr(self.fileobj, "name"):
                        name = self.fileobj.name
                        # name may be a path
                        if hasattr(name, "name"):
                            name = name.name
                    else:
                        name = None
                    log_util.FatalError(
                        _("Failed to read %s: %s") % (os.fsdecode(fn), util.uexc(e)), log.ErrorCode.generic
                    )
                if not res.data:
                    self.fileobj.close()
                    raise StopIteration
                return res

            def get_read_size(self):
                return 128 * 1024

            def get_footer(self):
                return b""

        log.Notice(_("Copying %s to local cache.") % os.fsdecode(fn))

        pr, loc_name, rem_name = resolve_basename(fn)

        fileobj = config.backend.get_fileobj_read(fn)
        src_iter = SrcIter(fileobj)
        tdp = dup_temp.new_tempduppath(file_naming.parse(loc_name))
        if pr.manifest:
            copy_raw(src_iter, tdp.name)
        else:
            gpg.GzipWriteFile(src_iter, tdp.name, size=sys.maxsize)
        tdp.setdata()
        tdp.move(config.archive_dir_path.append(loc_name))

    # get remote metafile list
    remlist = config.backend.list()
    remote_metafiles, ignored, rem_needpass = get_metafiles(remlist)

    # get local metafile list
    loclist = config.archive_dir_path.listdir()
    local_metafiles, local_partials, loc_needpass = get_metafiles(loclist)

    # we have the list of metafiles on both sides. remote is always
    # authoritative. figure out which are local spurious (should not
    # be there) and missing (should be there but are not).
    local_keys = list(local_metafiles.keys())
    remote_keys = list(remote_metafiles.keys())

    local_missing = []
    local_spurious = []

    for key in remote_keys:
        # If we lost our cache, re-get the remote file.  But don't do it if we
        # already have a local partial.  The local partial will already be
        # complete in this case (seems we got interrupted before we could move
        # it to its final location).
        if key not in local_keys and key not in local_partials and is_needed(key):
            local_missing.append(remote_metafiles[key])

    for key in local_keys:
        # If we have a file locally that is unnecessary, delete it.  Also
        # delete final versions of partial files because if we have both, it
        # means the write of the final version got interrupted.
        if key not in remote_keys or key in local_partials:
            local_spurious.append(local_metafiles[key])

    # finally finish the process
    if not local_missing and not local_spurious:
        log.Notice(_("Local and Remote metadata are synchronized, no sync needed."))
    else:
        local_missing.sort()
        local_spurious.sort()
        if not config.dry_run:
            log.Notice(_("Synchronizing remote metadata to local cache..."))
            if local_missing and (rem_needpass or loc_needpass):
                # password for the --encrypt-key
                config.gpg_profile.passphrase = get_passphrase(1, "sync")
            for fn in local_spurious:
                remove_local(fn)
            if hasattr(config.backend, "pre_process_download_batch"):
                config.backend.pre_process_download_batch(local_missing)
            for fn in local_missing:
                copy_to_local(fn)
            col_stats.set_values()
        else:
            if local_missing:
                log.Notice(
                    _("Sync would copy the following from remote to local:")
                    + "\n"
                    + "\n".join(map(os.fsdecode, local_missing))
                )
            if local_spurious:
                log.Notice(
                    _("Sync would remove the following spurious local files:")
                    + "\n"
                    + "\n".join(map(os.fsdecode, local_spurious))
                )


def check_last_manifest(col_stats):
    """
    Check consistency and hostname/directory of last manifest

    @type col_stats: CollectionStatus object
    @param col_stats: collection status

    @rtype: void
    @return: void
    """
    assert col_stats.all_backup_chains
    last_backup_set = col_stats.all_backup_chains[-1].get_last()
    # check remote manifest only if we can decrypt it (see #1729796)
    check_remote = not config.encryption or config.gpg_profile.passphrase
    last_backup_set.check_manifests(check_remote=check_remote)


def check_resources(action):
    """
    Check for sufficient resources:
    - temp space for volume build
    - enough max open files
    Put out fatal error if not sufficient to run

    @type action: string
    @param action: action in progress

    @rtype: void
    @return: void
    """
    if action in ["full", "inc", "restore"]:
        # Make sure we have enough resouces to run
        # First check disk space in temp area.
        tempfile, tempname = tempdir.default().mkstemp()
        os.close(tempfile)
        # strip off the temp dir and file
        tempfs = os.path.sep.join(tempname.split(os.path.sep)[:-2])
        try:
            stats = os.statvfs(tempfs)
        except Exception:
            log_util.FatalError(_("Unable to get free space on temp."), log.ErrorCode.get_freespace_failed)
        # Calculate space we need for at least 2 volumes of full or inc
        # plus about 30% of one volume for the signature files.
        freespace = stats.f_frsize * stats.f_bavail
        needspace = ((config.concurrency + 2) * config.volsize) + int(0.30 * config.volsize)
        if freespace < needspace:
            log_util.FatalError(
                _(f"Temp space has {freespace:,} available, backup needs approx {needspace:,}."),
                log.ErrorCode.not_enough_freespace,
            )
        else:
            log.Info(_(f"Temp has {freespace:,} available, backup will use approx {needspace:,}."))

        # Some environments like Cygwin run with an artificially
        # low value for max open files.  Check for safe number.
        try:
            soft, hard = resource.getrlimit(resource.RLIMIT_NOFILE)
        except resource.error:
            log_util.FatalError(_("Unable to get max open files."), log.ErrorCode.get_ulimit_failed)
        maxopen = min([l for l in (soft, hard) if l > -1])
        if maxopen < 1024:
            log_util.FatalError(
                _(
                    f"Max open files of {maxopen} is too low, should be >= 1024.\n"
                    f"Use 'ulimit -n 1024' or higher to correct.\n"
                ),
                log.ErrorCode.maxopen_too_low,
            )


def log_startup_parms():
    """
    log Python, duplicity, and system versions
    """
    log.Notice("=" * 80)
    log.Notice(f"duplicity {__version__}")
    log.Notice(f"Args: {' '.join([os.fsdecode(arg) for arg in sys.argv])}")
    log.Notice(" ".join(platform.uname()))
    log.Notice(f"{sys.executable or sys.platform} {sys.version}")
    log.Notice("=" * 80)


class Restart(object):
    """
    Class to aid in restart of inc or full backup.
    Instance in config.restart if restart in progress.
    """

    def __init__(self, last_backup):
        self.type = None
        self.start_time = None
        self.end_time = None
        self.start_vol = None
        self.last_index = None
        self.last_block = None
        self.last_backup = last_backup
        self.setParms(last_backup)

    def setParms(self, last_backup):
        if last_backup.time:
            self.type = "full"
            self.time = last_backup.time
        else:
            self.type = "inc"
            self.end_time = last_backup.end_time
            self.start_time = last_backup.start_time
        # We start one volume back in case we weren't able to finish writing
        # the most recent block.  Actually checking if we did (via hash) would
        # involve downloading the block.  Easier to just redo one block.
        self.start_vol = max(len(last_backup) - 1, 0)

    def checkManifest(self, mf):
        mf_len = len(mf.volume_info_dict)
        if (mf_len != self.start_vol) or not (mf_len and self.start_vol):
            if self.start_vol == 0:
                # upload of 1st vol failed, clean and restart
                log.Notice(
                    _(
                        "RESTART: The first volume failed to upload before termination.\n"
                        "         Restart is impossible...starting backup from beginning."
                    )
                )
                self.last_backup.delete()
                os.execve(sys.argv[0], sys.argv, os.environ)
            elif mf_len - self.start_vol > 0:
                # upload of N vols failed, fix manifest and restart
                log.Notice(
                    _(
                        "RESTART: Volumes %d to %d failed to upload before termination.\n"
                        "         Restarting backup at volume %d."
                    )
                    % (self.start_vol + 1, mf_len, self.start_vol + 1)
                )
                for vol in range(self.start_vol + 1, mf_len + 1):
                    mf.del_volume_info(vol)
            else:
                # this is an 'impossible' state, remove last partial and restart
                log.Notice(
                    _(
                        "RESTART: Impossible backup state: manifest has %d vols, remote has %d vols.\n"
                        "         Restart is impossible ... duplicity will clean off the last partial\n"
                        "         backup then restart the backup from the beginning."
                    )
                    % (mf_len, self.start_vol)
                )
                self.last_backup.delete()
                os.execve(sys.argv[0], sys.argv, os.environ)

    def setLastSaved(self, mf):
        vi = mf.volume_info_dict[self.start_vol]
        self.last_index = vi.end_index
        self.last_block = vi.end_block or 0


def main():
    """
    Start/end here
    """
    # per bug https://bugs.launchpad.net/duplicity/+bug/931175
    # duplicity crashes when PYTHONOPTIMIZE is set, so check
    # and refuse to run if it is set.
    if "PYTHONOPTIMIZE" in os.environ:
        log_util.FatalError(
            dedent(
                _(
                    """\
                PYTHONOPTIMIZE in the environment causes duplicity to fail to
                recognize its own backups.  Please remove PYTHONOPTIMIZE from
                the environment and rerun the backup.

                See https://bugs.launchpad.net/duplicity/+bug/931175
                """
                )
            ),
            log.ErrorCode.pythonoptimize_set,
        )

    # if python is run setuid, it's only partway set,
    # so make sure to run with euid/egid of root
    if os.geteuid() == 0:
        # make sure uid/gid match euid/egid
        os.setuid(os.geteuid())
        os.setgid(os.getegid())

    # set the current time strings (make it available for command line processing)
    dup_time.setcurtime()

    # determine what action we're performing and process command line
    action = cli_main.process_command_line(sys.argv[1:])

    # make sure we have lock
    util.acquire_lockfile()

    # log some status info
    log_startup_parms()

    try:
        do_backup(action)
    finally:
        util.release_lockfile()


def do_backup(action):
    # set the current time strings again now that we have time separator
    if config.current_time:
        dup_time.setcurtime(config.current_time)
    else:
        dup_time.setcurtime()

    # check for disk space and available file handles
    check_resources(action)

    # get current collection status
    col_stats = dup_collections.CollectionsStatus(config.backend, config.archive_dir_path, action).set_values()

    # check archive synch with remote, fix if needed
    if action not in [
        "collection-status",
        "remove-all-but-n-full",
        "remove-all-inc-of-but-n-full",
        "remove-old",
    ]:
        sync_archive(col_stats)

    while True:
        # if we have to clean up the last partial, then col_stats are invalidated
        # and we have to start the process all over again until clean.
        if action in ["full", "inc", "cleanup"]:
            last_full_chain = col_stats.get_last_backup_chain()
            if not last_full_chain:
                break
            last_backup = last_full_chain.get_last()
            if last_backup.partial:
                if action in ["full", "inc"]:
                    # set restart parms from last_backup info
                    config.restart = Restart(last_backup)
                    # (possibly) reset action
                    action = config.restart.type
                    # reset the time strings
                    if action == "full":
                        dup_time.setcurtime(config.restart.time)
                    else:
                        dup_time.setcurtime(config.restart.end_time)
                        dup_time.setprevtime(config.restart.start_time)
                    # log it -- main restart heavy lifting is done in write_multivol
                    log.Notice(_(f"Last {action} backup left a partial set, restarting."))
                    break
                else:
                    # remove last partial backup and get new collection status
                    log.Notice(_(f"Cleaning up previous partial {action} backup set, restarting."))
                    last_backup.delete()
                    col_stats = dup_collections.CollectionsStatus(
                        config.backend, config.archive_dir_path, action
                    ).set_values()
                    continue
            break
        break

    # OK, now we have a stable collection
    last_full_time = col_stats.get_last_full_backup_time()
    if last_full_time > 0:
        log.Notice(f"{_('Last full backup date:')} {dup_time.timetopretty(last_full_time)}")
    else:
        log.Notice(_("Last full backup date: none"))
    if (
        not config.restart
        and action in ["inc"]
        and config.full_if_older_than is not None
        and last_full_time < dup_time.curtime - config.full_if_older_than
    ):
        log.Notice(_("Last full backup is too old, forcing full backup"))
        action = "full"
    log_util.PrintCollectionStatus(col_stats)

    # get the passphrase if we need to based on action/options
    config.gpg_profile.passphrase = get_passphrase(1, action)

    if action == "restore":
        restore(col_stats)
    elif action == "verify":
        verify(col_stats)
    elif action == "list-current-files":
        list_current(col_stats)
    elif action == "collection-status":
        if config.show_changes_in_set is not None:
            if not config.jsonstat:
                # print classic stats
                log_util.PrintCollectionChangesInSet(col_stats, config.show_changes_in_set, True)
            else:
                # print json stat
                json_stat = col_stats.get_changes_in_set_json(config.show_changes_in_set)
                log.Log(str(json_stat), 8, log.InfoCode.collection_status, None, True)
        elif not config.file_changed:
            log_util.PrintCollectionStatus(col_stats, True)
        else:
            log_util.PrintCollectionFileChangedStatus(col_stats, config.file_changed, True)
    elif action == "cleanup":
        cleanup(col_stats)
    elif action == "remove-older-than":
        remove_old(col_stats)
    elif action == "remove-all-but-n-full" or action == "remove-all-inc-of-but-n-full":
        remove_all_but_n_full(col_stats)
    elif action == "sync":
        sync_archive(col_stats)
    else:
        assert action in ["full", "inc"], action
        # the passphrase for full and inc is used by --sign-key
        # the sign key can have a different passphrase than the encrypt
        # key, therefore request a passphrase
        if config.gpg_profile.sign_key:
            config.gpg_profile.signing_passphrase = get_passphrase(1, action, True)

        # if there are no recipients (no --encrypt-key), it must be a
        # symmetric key. Therefore, confirm the passphrase
        if not (config.gpg_profile.recipients or config.gpg_profile.hidden_recipients):
            config.gpg_profile.passphrase = get_passphrase(2, action)
            # a limitation in the GPG implementation does not allow for
            # inputting different passphrases, this affects symmetric+sign.
            # Allow an empty passphrase for the key though to allow a non-empty
            # symmetric key
            if (
                config.gpg_profile.signing_passphrase
                and config.gpg_profile.passphrase != config.gpg_profile.signing_passphrase
            ):
                log_util.FatalError(
                    _(
                        "When using symmetric encryption, the signing passphrase "
                        "must equal the encryption passphrase."
                    ),
                    log.ErrorCode.user_error,
                )

        if action == "full":
            full_backup(col_stats)
        else:  # attempt incremental
            sig_chain = check_sig_chain(col_stats)
            # action == "inc" was requested, but no full backup is available
            if not sig_chain:
                full_backup(col_stats)
            else:
                if not config.restart:
                    # only ask for a passphrase if there was a previous backup
                    if col_stats.all_backup_chains:
                        config.gpg_profile.passphrase = get_passphrase(1, action)
                        check_last_manifest(col_stats)  # not needed for full backups
                incremental_backup(sig_chain, col_stats)

    config.backend.close()
    log.shutdown()
    if exit_val is not None:
        sys.exit(exit_val)
