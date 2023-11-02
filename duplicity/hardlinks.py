import os
import sys
import time
from humanize import intcomma


def get_hardlinks(path):
    saved = 0
    inodes = dict()
    it = os.scandir(path)
    for entry in it:
        inode = entry.inode()
        nlinks = entry.stat().st_nlink
        if nlinks > 1 and not entry.is_symlink():
            if inode not in inodes:
                inodes[inode] = []
            inodes[inode].append(entry.path)
            size = entry.stat().st_size
            savings = size * (nlinks - 1)
            print(f"{entry.path}, {nlinks}, {size}, {savings}")
            saved += savings
    return inodes, saved


if __name__ == "__main__":
    try:
        path = sys.argv[1]
    except:
        path = "/usr/bin"

    print(f"Scanning {path} for hardlinks")
    start = time.time()
    inodes, saved = get_hardlinks(path)
    print(f"Elapsed: {time.time()-start} for {len(inodes)} entries.\nWould save {intcomma(saved)} bytes on backup.")
