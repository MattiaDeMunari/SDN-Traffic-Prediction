import sys
import os
import subprocess 
import random
import time

MAX_RANDOM_FLOW_BW = .5
MAX_RANDOM_FLOW_DURATION = 2
MAX_IDLE_TIME = 2

if __name__ == "__main__":
    host_ip = sys.argv[1]
    
    duration = random.random()*MAX_RANDOM_FLOW_DURATION
    bw = random.random()*MAX_RANDOM_FLOW_BW
    idle_time = random.random()*MAX_IDLE_TIME
    cmd = f'iperf -t {duration} -c {host_ip} -b {bw}M -p 5050'
    while True:
        subprocess.Popen( cmd, shell=True).wait()
        time.sleep(idle_time)