import json
import os
import sys
import time
import platform

default_excludes = {
    "Darwin": [
        "/System/Volumes/Data",
        "/Volumes",
        "/private",
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
    def __init__(self):
        self.inodes = dict()
        self.num_dirs = 1
        self.num_entries = 0
        self.num_files = 0
        self.num_nlinks = 0
        self.start = time.time()

        self.exclude = default_excludes.get(platform.system(), "Linux")

    def get_hardlinks(self, path: str, follow_symlinkks: bool = False) -> None:
        our_dev = os.stat(path).st_dev
        for entry in os.scandir(path):
            self.num_entries += 1

            try:
                stat_res = entry.stat(follow_symlinks=follow_symlinkks)
            except OSError as e:
                print(str(e))
                continue

            if stat_res.st_dev != our_dev:
                # stay on same filesystem
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
                        # sub sequent hard link
                        self.inodes[inode].append(entry)

            if entry.is_dir(follow_symlinks=follow_symlinkks):
                skip = False
                for patt in self.exclude:
                    if entry.path.startswith(patt):
                        # some paths are trouble
                        skip = True
                        break
                if skip:
                    continue

                self.num_dirs += 1
                try:
                    self.get_hardlinks(entry.path)
                except OSError as e:
                    print(str(e))
                    continue

    def dump_hardlinks(self, filename: str = "/tmp/hardlinks.json") -> None:
        print(f"Dumping hardlinks to {filename}")
        hardlinks = {}
        for inode in self.inodes:
            hardlinks[inode] = {}
            for entry in self.inodes[inode]:
                path, file = os.path.split(entry.path)
                if path not in hardlinks[inode]:
                    hardlinks[inode]["stat"] = entry.stat()
                    hardlinks[inode][path] = [file]
                else:
                    hardlinks[inode][path].append(file)

        with open(filename, "w") as fd:
            fd.write(json.dumps(hardlinks, indent=2))

    def print_summary(self) -> None:
        hlinks_expanded = 0
        hlinks_supported = 0
        hlinks_incomplete = 0

        print(f"\nSummary of {path}:")

        for inode in self.inodes:
            entry = self.inodes[inode][0]
            hlinks_found = len(self.inodes[inode])
            hlinks_expanded += entry.stat().st_size * hlinks_found
            hlinks_supported += entry.stat().st_size
            hlinks_outside = entry.stat().st_nlink - hlinks_found
            if hlinks_outside:
                hlinks_incomplete += entry.stat().st_nlink - hlinks_found
                print(
                    f"Inode at {entry.path} has {hlinks_outside:,} hardlinks outside this directory. "
                    f"({entry.stat().st_nlink:,} > {hlinks_found:,})"
                )

        print(
            f"Elapsed (secs):               {f'{time.time()-self.start:.4f}':>20}\n"
            f"inodes:                       {f'{len(self.inodes):,}':>20}\n"
            f"hardlinks:                    {f'{self.num_nlinks:,}':>20}\n"
            f"reg files:                    {f'{self.num_files:,}':>20}\n"
            f"dir entries:                  {f'{self.num_entries:,}':>20}\n"
            f"directories:                  {f'{self.num_dirs:,}':>20}\n"
            f"Size if hardlinks expanded:   {f'{hlinks_expanded:,}':>20}\n"
            f"Size if hardlinks supported:  {f'{hlinks_supported:,}':>20}\n"
            f"Hardlink support would save:  {f'{hlinks_expanded-hlinks_supported:,}':>20}\n"
            f"inode paths outside dir:      {f'{hlinks_incomplete:,}':>20}"
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
