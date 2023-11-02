import os
import sys
import time
from humanize import intcomma


def get_hardlinks(path):
    saved = 0
    total = 0
    inodes = dict()
    it = os.scandir(path)
    for entry in it:
        inode = entry.inode()
        nlinks = entry.stat().st_nlink
        size = entry.stat().st_size
        total += size
        if nlinks > 1 and not entry.is_symlink():
            if inode not in inodes:
                inodes[inode] = []
            else:
                saved += size
            inodes[inode].append(entry.path)
            print(f"{entry.path}, {nlinks}, {intcomma(size)}")
    return inodes, saved, total


if __name__ == "__main__":
    try:
        path = sys.argv[1]
    except Exception:
        path = "/usr/bin"

    print(f"Scanning {path} for hardlinks")
    start = time.time()
    inodes, saved, total = get_hardlinks(path)
    print(f"Elapsed: {time.time()-start:.4f} for {len(inodes)} entries.")
    print(f"Would save {intcomma(saved)} bytes of {intcomma(total)} without hard link support.")
