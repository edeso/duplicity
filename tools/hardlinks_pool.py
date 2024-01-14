import json
import multiprocessing as mp
import os
import platform
import queue
import sys
import time
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
    hardlinks: dict
    num_dirs: int
    num_entries: int
    num_files: int
    num_nlinks: int
    not_our_fs: int
    in_exclusions: int
    oserrors: dict

    def __init__(self):
        self.hardlinks = dict()
        self.num_dirs = 0
        self.num_entries = 0
        self.num_files = 0
        self.num_nlinks = 0
        self.not_our_fs = 0
        self.in_exclusions = 0
        self.oserrors = dict(((1, 0), (13, 0)))


res_queue = mp.Queue()
path_queue = mp.Queue()

Totals = Results()


def run(basepath: str):
    start = time.time()

    def err(e):
        print(f"Callback Error: {str(e)}")

    tasks = os.cpu_count()
    with mp.Pool(tasks) as pool:
        # prime the pump
        path_queue.put(basepath)

        # get all rewults
        results = [pool.apply_async(get_hardlinks, (), error_callback=err) for _ in range(tasks)]

        for result in results:
            result = result.get()
            if result is not None:
                total_results(result)


def total_results(result: Results):
    global Totals
    Totals.hardlinks = Totals.hardlinks.update(result.hardlinks)
    Totals.num_entries += result.num_entries
    Totals.num_dirs += result.num_dirs
    Totals.num_files += result.num_files
    Totals.num_nlinks += result.num_nlinks
    Totals.in_exclusions += result.in_exclusions
    for key in Totals.oserrors.keys():
        Totals.oserrors[key] += result.oserrors[key]


def get_hardlinks() -> None:
    res = Results()

    our_dev = os.stat(dirpath).st_dev

    while True:
        try:
            dpath = path_queue.get(timeout=2)
        except queue.Empty as e:
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
                    path_queue.put(entry.path)

        except OSError as e:
            if e.errno in res.oserrors:
                res.oserrors[e.errno] += 1
            else:
                print(str(e))

    return res


def dump_hardlinks(filename: str = "/tmp/hardlinks.json") -> None:
    print(f"Dumping hardlinks to {filename}")

    with open(filename, "w") as fd:
        fd.write(json.dumps(hardlinks))


def print_summary() -> None:
    print(f"\nSummary of {basepath}:")

    for inode in res.hardlinks:
        entry = res.hardlinks[inode][0]
        hlinks_found = len(res.hardlinks[inode])
        hlinks_expanded += entry.stat().st_size * hlinks_found
        hlinks_supported += entry.stat().st_size
        hlinks_outside = entry.stat().st_nlink - hlinks_found
        if hlinks_outside:
            hlinks_incomplete += entry.stat().st_nlink - hlinks_found
            print(
                f"Inode at {entry.path} has {hlinks_outside:,} hardlinks outside this directory. "
                f"({entry.stat().st_nlink:,} > {hlinks_found:,})"
            )

    for errno in sorted(res.oserrors.keys()):
        if res.oserrors[errno]:
            print(f"Encountered {res.oserrors[errno]:,} errors: {os.strerror(errno)}")

    if res.in_exclusions:
        print(f"Found {in_exclusions:,} dirs in exclusions list.")

    if res.not_our_fs:
        print(f"Found {res.not_our_fs:,} dirs not in our filesystem.")

    print(
        f"Elapsed (secs):               {f'{time.time()-start:.4f}':>20}\n"
        f"res.hardlinks:                       {f'{len(res.hardlinks):,}':>20}\n"
        f"hardlinks:                    {f'{res.num_num_nlinks:,}':>20}\n"
        f"reg files:                    {f'{res.num_files:,}':>20}\n"
        f"dir entries:                  {f'{res.num_entries:,}':>20}\n"
        f"directories:                  {f'{res.num_dirs:,}':>20}\n"
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

    print(f"\nScanning {dirpath} for hardlinks.")
    run(dirpath)
    # dump_hardlinks()
    # print_summary()
