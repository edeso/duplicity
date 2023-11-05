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
        self.total_dirsize = 0
        self.total_without = 0
        self.would_save = 0

    def get_hardlinks(self):
        for entry in os.scandir(self.path):
            self.num_entries += 1
            if not entry.is_file(follow_symlinks=False):
                continue
            self.num_files += 1
            inode = entry.inode()
            stat = entry.stat(follow_symlinks=False)
            size = stat.st_size
            self.total_without += size
            if (nlinks := stat.st_nlink) > 1:
                if inode not in self.inodes:
                    # first of this inode
                    self.inodes[inode] = []
                    self.total_dirsize += size
                else:
                    # subsequent hard link
                    self.would_save += size
                self.inodes[inode].append(entry.path)
                print(f"{entry.path:40}: {nlinks:4}: {intcomma(size):>20}")
            else:
                # normal entry
                if not entry.is_symlink():
                    self.total_dirsize += size


if __name__ == "__main__":
    try:
        path = sys.argv[1]
    except Exception:
        path = "/usr/bin"

    print(f"Scanning {path} for hardlinks")
    start = time.time()
    hl = HardLinks(path)
    hl.get_hardlinks()
    print(
        f"Directory size is {intcomma(hl.total_dirsize)} in {hl.num_files} of {hl.num_entries} entries.\n"
        f"Would cosumee {intcomma(hl.total_without)} without hard link support.\n"
        f"Would save {intcomma(hl.would_save)} with hard link support."
    )
    print(f"Elapsed: {time.time()-start:.4f} for {len(hl.inodes)} entries.")
