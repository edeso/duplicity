import os
import sys
import time
import platform

exclude_lists = {
    "Darwin": [
        "/System/Volumes/Data/private",
        "/Volumes",
        "/private",
        "/tmp",
        "/var",
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
        "/var",
    ],
}


class HardLinks:
    def __init__(self):
        self.inodes = dict()
        self.num_entries = 0
        self.num_files = 0
        self.num_nlinks = 0

        self.exclude = exclude_lists[platform.system()]

    def get_hardlinks(
        self,
        path,
        follow_symlinkks=False,
    ):
        our_dev = os.stat(path).st_dev
        for entry in os.scandir(path):
            if entry.path in self.exclude:
                continue
            self.num_entries += 1
            try:
                stat = entry.stat(follow_symlinks=follow_symlinkks)
            except OSError as e:
                print(str(e))
                continue
            if stat.st_dev != our_dev:
                # stay on same filesystem
                continue
            if entry.is_file(follow_symlinks=follow_symlinkks):
                self.num_files += 1
                inode = entry.inode()
                if stat.st_nlink > 1:
                    self.num_nlinks += 1
                    if inode not in self.inodes:
                        # first of this inode
                        self.inodes[inode] = [entry]
                    else:
                        # sub sequent hard link
                        self.inodes[inode].append(entry)
            if entry.is_dir(follow_symlinks=follow_symlinkks):
                try:
                    self.get_hardlinks(entry.path)
                except OSError as e:
                    print(str(e))
                    continue

    def print_summary(self):
        hlinks_expanded = 0
        hlinks_supported = 0
        print(f"\nSummary of {path}:")
        for inode in self.inodes:
            entry = self.inodes[inode][0]
            hlinks_expanded += entry.stat().st_size * len(self.inodes[inode])
            hlinks_supported += entry.stat().st_size
            if entry.stat().st_nlink > len(self.inodes[inode]):
                print(
                    f"Inode at {entry.path} has hardlinks outside this directory. "
                    f"({entry.stat().st_nlink:,} > {len(self.inodes[inode]):,})"
                )

        print(
            f"Size if hardlinks expanded:   {f'{hlinks_expanded:,}':>20}\n"
            f"Size if hardlinks supported:  {f'{hlinks_supported:,}':>20}\n"
            f"Support would save:           {f'{hlinks_expanded-hlinks_supported:,}':>20}"
        )


if __name__ == "__main__":
    try:
        path = sys.argv[1]
    except Exception:
        path = "/usr"

    follow = True

    print(f"\nScanning {path} for hardlinks, follow_symlinks={follow}")
    start = time.time()
    hl = HardLinks()
    hl.get_hardlinks(path, follow_symlinkks=follow)
    print(
        f"Elapsed: {time.time()-start:.4f} seconds for {len(hl.inodes):,} "
        f"inodes in {hl.num_nlinks:,} hardlinks out of {hl.num_files:,} files."
    )
    hl.print_summary()
