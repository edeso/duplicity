import os
import sys
import time
from humanize import intcomma


class HardLinks:
    def __init__(self, path):
        self.inodes = dict()
        self.num_entries = 0
        self.num_files = 0
        self.path = path

    def get_hardlinks(self):
        for entry in os.scandir(self.path):
            self.num_entries += 1
            if entry.is_file(follow_symlinks=False):
                self.num_files += 1
                inode = entry.inode()
                stat = entry.stat(follow_symlinks=False)
                if (nlinks := stat.st_nlink) > 1:
                    if inode not in self.inodes:
                        # first of this inode
                        self.inodes[inode] = []
                    # subsequent hard link
                    self.inodes[inode].append(entry)


if __name__ == "__main__":
    try:
        path = sys.argv[1]
    except Exception:
        path = "/usr/bin"

    print(f"Scanning {path} for hardlinks")
    start = time.time()
    hl = HardLinks(path)
    hl.get_hardlinks()
    print(f"Elapsed: {time.time()-start:.4f} for {len(hl.inodes)} entries.")

    hlinks_expanded = 0
    hlinks_supported = 0
    print(f"\nSummary of {path}:")
    for inode in hl.inodes:
        entry = hl.inodes[inode][0]
        hlinks_expanded += entry.stat().st_size * len(hl.inodes[inode])
        hlinks_supported += entry.stat().st_size
        if entry.stat().st_nlink > len(hl.inodes[inode]):
            print(
                f"Inode at {entry.path} has hardlinks outside this directory. "
                f"({entry.stat().st_nlink} > {len(hl.inodes[inode])})"
            )

    print(
        f"Size if hardlinks expanded:   {intcomma(hlinks_expanded):>20}\n"
        f"Size if hardlinks supported:  {intcomma(hlinks_supported):>20}\n"
        f"Support would save:           {intcomma(hlinks_expanded-hlinks_supported):>20}"
    )
