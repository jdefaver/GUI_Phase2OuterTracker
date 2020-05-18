#!/usr/bin/env python3
import sys
import json
import random
import time

print("test 2 running")
sys.stdout.flush()
sys.stderr.write("Error in test 2\n")
sys.stderr.flush()

with open('/tmp/my_fifo','w') as pipe:
    pipe.write(json.dumps({'type':'message', 'data':'Starting data taking'})+"\n")
    pipe.flush()

    for i in range(20):
        time.sleep(0.5)
        data = {'type': 'data', 'data': [i, random.random()+0.5]}
        pipe.write(json.dumps(data)+"\n")
        pipe.flush()

    pipe.write(json.dumps({'type':'message', 'data':'End of data taking'})+"\n")
    pipe.flush()

print("test 2 run is done")
sys.stdout.flush()
sys.stderr.write("Error in test 2 at end\n")
sys.stderr.flush()