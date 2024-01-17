#!/usr/bin/env pytho3

import json
import multiprocessing as mp
import os
import platform
import queue
import sys
import time
from copy import copy
from dataclasses import dataclass
from queue import Empty, Full

mp.set_start_method("fork")

entry_kwargs = {"follow_symlinks": False}

default_excludes = {
    "Darwin": [
        "/System/Volumes",
        # "/Volumes",
        "/cores",
        "/dev",
        "/lost+found",
        "/private",
        "/run",
        "/tmp",
    ],
    "Linux": [
        "/boot",
        "/dev",
        "/lost+found",
        "/media",
        "/mnt",
        "/proc",
        "/swapfile",
        "/tmp",
    ],
}

exclude = default_excludes.get(platform.system(), "Linux")


@dataclass
class Results:
    num_dirs: int
    num_entries: int
    num_files: int
    num_nlinks: int
    not_our_fs: int
    in_exclusions: int
    oserrors: dict
    hardlinks: dict

    def __init__(self):
        self.num_dirs = 0
        self.num_entries = 0
        self.num_files = 0
        self.num_nlinks = 0
        self.not_our_fs = 0
        self.in_exclusions = 0
        self.oserrors = dict(((1, 0), (13, 0)))
        self.hardlinks = dict()


task_queue = mp.Queue()


def main(basepath: str):
    Totals = Results()

    def err(e):
        print(f"Callback Error: {str(e)}")

    tasks = os.cpu_count()
    with mp.Pool(tasks) as pool:
        # prime the pump
        task_queue.put(basepath)

        # get all rewults
        results = [pool.apply_async(get_hardlinks, (), error_callback=err) for _ in range(tasks)]

        # total results
        for result in results:
            total_results(Totals, result.get())

    return Totals


def get_hardlinks():
    res = Results()

    our_dev = os.stat(dirpath).st_dev

    while True:
        try:
            dpath = task_queue.get(timeout=2)
        except queue.Empty:
            break
        # print(f"Entering {dpath}")
        try:
            for entry in os.scandir(dpath):
                res.num_entries += 1

                stat_res = entry.stat(**entry_kwargs)

                if stat_res.st_dev != our_dev:
                    # stay on same filesystem
                    # print(f"Skipping {entry.path}.  Not on our filesystem.")
                    res.not_our_fs += 1
                    continue

                if entry.is_file(**entry_kwargs):
                    res.num_files += 1
                    if stat_res.st_nlink > 1:
                        # entry can't be serialized, so keep just what we need, stat info
                        # plus split full path into dir and filename to save space
                        inode = entry.inode()
                        if inode not in res.hardlinks:
                            res.hardlinks[inode] = dict()
                        if entry.path not in res.hardlinks[inode]:
                            # first path adds stat info
                            res.hardlinks[inode]["stat"] = entry.stat()
                            res.hardlinks[inode][entry.path] = [entry.name]
                        else:
                            # subsequent paths do not
                            res.hardlinks[inode][entry.path].append(entry.name)

                if entry.is_dir(**entry_kwargs):
                    skip = False
                    for patt in exclude:
                        if entry.path.startswith(patt):
                            # some paths are trouble
                            # print(f"Skipping {entry.path}.  In exclusions.")
                            res.in_exclusions += 1
                            skip = True
                            break
                    if skip:
                        continue
                    res.num_dirs += 1
                    task_queue.put(entry.path)

        except OSError as e:
            if e.errno in res.oserrors:
                res.oserrors[e.errno] += 1
            else:
                print(str(e))

    return res


def total_results(Totals: Results, result: Results):
    def merge_hardlinks(tot: dict, res: dict):
        for inode in res.keys():
            if inode not in tot:
                # just a straight copy
                tot[inode] = copy(res[inode])
            else:
                # merge the data
                for k in res[inode].keys():
                    if k == "stat":
                        # stat present and does not change
                        continue
                    if k in tot[inode]:
                        # add the two lists of filenames
                        tot[inode][k] += res[inode][k]
                    else:
                        # just copy the list of filenames
                        tot[inode][k] = copy(res[inode][k])
        return tot

    Totals.hardlinks = merge_hardlinks(Totals.hardlinks, result.hardlinks)
    Totals.num_entries += result.num_entries
    Totals.num_dirs += result.num_dirs
    Totals.num_files += result.num_files
    Totals.num_nlinks += result.num_nlinks
    Totals.in_exclusions += result.in_exclusions
    for key in Totals.oserrors.keys():
        Totals.oserrors[key] += result.oserrors[key]

    return Totals


def dump_hardlinks(totals: Results, filename: str = "/tmp/hardlinks.json"):
    print(f"Dumping hardlinks to {filename}")

    with open(filename, "w") as fd:
        fd.write(json.dumps(totals.hardlinks))


def print_summary(totals: Results):
    print(f"\nSummary of {dirpath}:")

    hlinks_incomplete = 0
    hlinks_expanded = 0
    hlinks_supported = 0

    for inode in totals.hardlinks.keys():
        hlinks_found = len(totals.hardlinks[inode]) - 1
        stat = totals.hardlinks[inode]["stat"]
        hlinks_expanded += stat.st_size * hlinks_found
        hlinks_supported += stat.st_size
        hlinks_outside = stat.st_nlink - hlinks_found
        if hlinks_outside:
            hlinks_incomplete += stat.st_nlink - hlinks_found
            print(f"Inode {inode} has {stat.st_nlink:,} hardlinks, {hlinks_outside:,} outside this directory.")

    for errno in sorted(totals.oserrors.keys()):
        if totals.oserrors[errno]:
            print(f"Encountered {totals.oserrors[errno]:,} errors: {os.strerror(errno)}")

    if totals.in_exclusions:
        print(f"Found {in_exclusions:,} dirs in exclusions list.")

    if totals.not_our_fs:
        print(f"Found {totals.not_our_fs:,} dirs not in our filesystem.")

    for inode in totals.hardlinks.keys():
        totals.num_nlinks += totals.hardlinks[inode]["stat"].st_nlink

    print(
        f"Elapsed (secs):               {f'{time.time()-start:.4f}':>20}\n"
        f"inodes:                       {f'{len(totals.hardlinks):,}':>20}\n"
        f"hardlinks:                    {f'{totals.num_nlinks:,}':>20}\n"
        f"reg files:                    {f'{totals.num_files:,}':>20}\n"
        f"dir entries:                  {f'{totals.num_entries:,}':>20}\n"
        f"directories:                  {f'{totals.num_dirs:,}':>20}\n"
        f"Size if hardlinks expanded:   {f'{hlinks_expanded:,}':>20}\n"
        f"Size if hardlinks supported:  {f'{hlinks_supported:,}':>20}\n"
        f"Hardlink support would save:  {f'{hlinks_expanded-hlinks_supported:,}':>20}\n"
        f"Hardlinks outside base dir:   {f'{hlinks_incomplete:,}':>20}"
    )


if __name__ == "__main__":
    try:
        dirpath = sys.argv[1]
    except Exception:
        dirpath = "/usr"

    dirpath = os.path.abspath(dirpath)

    start = time.time()

    print(f"\nScanning {dirpath} for hardlinks.")
    totals = main(dirpath)
    dump_hardlinks(totals)
    print_summary(totals)
