#!/usr/bin/env python
import time, sys

fn = "test-data.txt"
try:
    f = open(fn, "r")
    n = int(f.read())
    f.close()
except:
    n = 0
n += 1

for i in range(n, n+9):
    time.sleep(1)
    f = open(fn, "w")
    f.write(str(i))
    f.close()
    stream = sys.stdout if i%2==0 else sys.stderr
    stream.write("[{i:2d}] {clock}\n".format(clock=time.clock(), i=i))
    stream.flush()
