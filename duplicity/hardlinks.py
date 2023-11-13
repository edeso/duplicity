import os
import sys
import time


class HardLinks:
    def __init__(self):
        self.inodes = dict()
        self.num_entries = 0
        self.num_files = 0
        self.num_nlinks = 0

    def get_hardlinks(self, path, follow_symlinkks=False):
        our_dev = os.stat(path).st_dev
        for entry in os.scandir(path):
            self.num_entries += 1
            if entry.is_file(follow_symlinks=follow_symlinkks):
                self.num_files += 1
                inode = entry.inode()
                stat = entry.stat(follow_symlinks=follow_symlinkks)
                if stat.st_nlink > 1:
                    self.num_nlinks += 1
                    if inode not in self.inodes:
                        # first of this inode
                        self.inodes[inode] = []
                    # subsequent hard link
                    self.inodes[inode].append(entry)
            if entry.is_dir(follow_symlinks=follow_symlinkks) and entry.stat().st_dev == our_dev:
                try:
                    self.get_hardlinks(entry.path)
                except (OSError, PermissionError) as e:
                    print(str(e))

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

    follow = False

    print(f"\nScanning {path} for hardlinks, follow_symlinks={follow}")
    start = time.time()
    hl = HardLinks()
    hl.get_hardlinks(path, follow_symlinkks=follow)
    print(
        f"Elapsed: {time.time()-start:.4f} for {len(hl.inodes):,} "
        f"inodes in {hl.num_nlinks:,} out of {hl.num_files:,} files."
    )
    hl.print_summary()
