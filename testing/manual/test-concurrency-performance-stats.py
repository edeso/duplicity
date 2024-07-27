#!/usr/bin/env python3

import glob
import json
import os
import re
from pprint import pprint as print
import matplotlib.pyplot as plt


DEST_DIR = "/tmp/back-cc-test"

stats = {}
rex = re.compile(r".*tt([0-9]*)-cc([0-9]*).json")

for filename in glob.iglob("/tmp/results-*/jsonstat-tt*.json"):
    print(filename)
    m = rex.match(filename)
    tt, cc = m.groups() if m is not None else ("no", "no")
    tt, cc = int(tt), int(cc)
    with open(filename) as file:
        stats.setdefault(tt, {})[cc] = json.load(file)
        pass
# print(stats)

for tt, cc_dict in sorted(stats.items()):
    time_per_volumes = []
    for cc, values in cc_dict.items():
        time_total = values["ElapsedTime"]
        time_per_volume = time_total / values["ConcurrentTransferStats"]["count"]
        time_per_volumes.append(time_per_volume)
        print(
            f"Backend delay: {tt:5}, Concurrency: {cc} Time: {values['ElapsedTime']:6.2f}, Time per vol: {time_per_volume:5.2f}, avg pur transfer time {values['ConcurrentTransferStats']['time']['avg']:5.2f}, avg throttle {values['ConcurrentTransferStats']['throttle']['avg']:5.2f}, Peak in queue: {values['ConcurrentTransferStats']['peak_in_queue']}",
            width=200,
        )
    x1 = list(sorted(cc_dict.keys()))
    y1 = [y["ElapsedTime"] for y in cc_dict.values()]
    y1 = time_per_volumes
    plt.plot(x1, y1, label=f"TT: {tt}")

# naming the x axis
plt.xlabel("concurrency")
# naming the y axis
plt.ylabel("avg duration per volume")
# giving a title to my graph
plt.title("Backup time by concurrency and transfer speed")

# show a legend on the plot
plt.legend()

# function to show the plot
plt.savefig("/tmp/concurrency-stat.png")
plt.show()
