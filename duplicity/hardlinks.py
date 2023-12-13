import json
import os
import sys
import time
import platform

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


class HardLinks:
    """
    Class HardLinks represents a utility for retrieving and counting hard links in a directory. It provides methods
    for getting hard links, dumping hard links to a JSON file, and printing a summary of the current state of the
    object.

    Constructor:

        def __init__(self):
            Initializes HardLinks object with the following attributes:
            - inodes: dictionary to store hard links with their corresponding entries
            - num_dirs: number of directories encountered during search
            - num_entries: total number of entries encountered (files + directories)
            - num_files: number of regular files encountered
            - num_nlinks: number of hard links encountered
            - start: start time of the search
            - exclude: list of directories to exclude from the search
            - oserrors: dictionary to store the count of encountered OS errors
            - not_our_filesystem: number of directories not in the current filesystem
            - in_exclusions: number of directories in the exclusions list
            - hlinks_expanded: size if hard links are expanded
            - hlinks_supported: size if hard links are supported
            - hlinks_incomplete: number of hard links outside the based dir

    Methods:

        def get_hardlinks(self, path: str, follow_symlinkks: bool = False) -> None:
            Retrieve and count the hard links at a given path.

            Parameters:
            - path: The path to the directory to search for hard links.
            - follow_symlinks: If True, follow symbolic links. Default is False.

        def dump_hardlinks(self, filename: str = "/tmp/hardlinks.json") -> None:
            Dump hard links to a JSON file.

            Parameters:
            - filename (str): The path of the JSON file where the hard links will be dumped.
                              Default is "/tmp/hardlinks.json".

        def print_summary(self) -> None:
            Prints a summary of the current state of the object.
    """

    def __init__(self):
        self.inodes = dict()
        self.num_dirs = 1
        self.num_entries = 0
        self.num_files = 0
        self.num_nlinks = 0
        self.start = time.time()

        self.exclude = default_excludes.get(platform.system(), "Linux")

        self.oserrors = {
            1: 0,  # operation not permitted
            13: 0,  # permission denied
        }
        self.not_our_filesystem = 0
        self.in_exclusions = 0

        self.hlinks_expanded = 0
        self.hlinks_supported = 0
        self.hlinks_incomplete = 0

    def get_hardlinks(self, path: str, follow_symlinkks: bool = False) -> None:
        our_dev = os.stat(path).st_dev
        for entry in os.scandir(path):
            self.num_entries += 1

            try:
                stat_res = entry.stat(follow_symlinks=follow_symlinkks)
            except OSError as e:
                if e.errno in self.oserrors:
                    self.oserrors[e.errno] += 1
                else:
                    print(str(e))
                continue

            if stat_res.st_dev != our_dev:
                # stay on same filesystem
                # print(f"Skipping {entry.path}.  Not on our filesystem.")
                self.not_our_filesystem += 1
                continue

            if entry.is_file(follow_symlinks=follow_symlinkks):
                self.num_files += 1
                inode = entry.inode()
                if stat_res.st_nlink > 1:
                    self.num_nlinks += 1
                    if inode not in self.inodes:
                        # first of this inode
                        self.inodes[inode] = [entry]
                    else:
                        # subsequent hard link
                        self.inodes[inode].append(entry)

            if entry.is_dir(follow_symlinks=follow_symlinkks):
                skip = False
                for patt in self.exclude:
                    if entry.path.startswith(patt):
                        # some paths are trouble
                        # print(f"Skipping {entry.path}.  In exclusions.")
                        self.in_exclusions += 1
                        skip = True
                        break
                if skip:
                    continue

                self.num_dirs += 1
                try:
                    self.get_hardlinks(entry.path)
                except OSError as e:
                    if e.errno in self.oserrors:
                        self.oserrors[e.errno] += 1
                    else:
                        print(str(e))
                    continue

    def dump_hardlinks(self, filename: str = "/tmp/hardlinks.json") -> None:
        print(f"Dumping hardlinks to {filename}")
        hardlinks = {}
        for inode in self.inodes:
            # entry can't be serialized, so keep just what we need, stat info
            # plus split full path into dir and filename to save space
            hardlinks[inode] = {}
            for entry in self.inodes[inode]:
                path, file = os.path.split(entry.path)
                if path not in hardlinks[inode]:
                    # first path adds stat info
                    hardlinks[inode]["stat"] = entry.stat()
                    hardlinks[inode][path] = [file]
                else:
                    # subsequent paths do not
                    hardlinks[inode][path].append(file)

        with open(filename, "w") as fd:
            fd.write(json.dumps(hardlinks))

    def print_summary(self) -> None:
        print(f"\nSummary of {path}:")

        for inode in self.inodes:
            entry = self.inodes[inode][0]
            self.hlinks_found = len(self.inodes[inode])
            self.hlinks_expanded += entry.stat().st_size * self.hlinks_found
            self.hlinks_supported += entry.stat().st_size
            self.hlinks_outside = entry.stat().st_nlink - self.hlinks_found
            if self.hlinks_outside:
                self.hlinks_incomplete += entry.stat().st_nlink - self.hlinks_found
                print(
                    f"Inode at {entry.path} has {self.hlinks_outside:,} hardlinks outside this directory. "
                    f"({entry.stat().st_nlink:,} > {self.hlinks_found:,})"
                )

        for errno in sorted(self.oserrors.keys()):
            if self.oserrors[errno]:
                print(f"Encountered {self.oserrors[errno]:,} errors: {os.strerror(errno)}")

        if self.in_exclusions:
            print(f"Found {self.in_exclusions:,} dirs in exclusions list.")

        if self.not_our_filesystem:
            print(f"Found {self.not_our_filesystem:,} dirs not in our filesystem.")

        print(
            f"Elapsed (secs):               {f'{time.time()-self.start:.4f}':>20}\n"
            f"inodes:                       {f'{len(self.inodes):,}':>20}\n"
            f"hardlinks:                    {f'{self.num_nlinks:,}':>20}\n"
            f"reg files:                    {f'{self.num_files:,}':>20}\n"
            f"dir entries:                  {f'{self.num_entries:,}':>20}\n"
            f"directories:                  {f'{self.num_dirs:,}':>20}\n"
            f"Size if hardlinks expanded:   {f'{self.hlinks_expanded:,}':>20}\n"
            f"Size if hardlinks supported:  {f'{self.hlinks_supported:,}':>20}\n"
            f"Hardlink support would save:  {f'{self.hlinks_expanded-self.hlinks_supported:,}':>20}\n"
            f"Hardlinks outside based ir:   {f'{self.hlinks_incomplete:,}':>20}"
        )


if __name__ == "__main__":
    try:
        path = sys.argv[1]
    except Exception:
        path = "/usr"

    follow = False

    print(f"\nScanning {path} for hardlinks, follow_symlinks={follow}")
    hl = HardLinks()
    hl.get_hardlinks(path, follow_symlinkks=follow)
    hl.dump_hardlinks()
    hl.print_summary()
