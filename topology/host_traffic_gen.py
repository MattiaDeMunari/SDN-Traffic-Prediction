import sys
import subprocess 
import random
import time

MAX_RANDOM_FLOW_BW = 1.5
MAX_RANDOM_FLOW_DURATION = 2
MAX_IDLE_TIME = .4 
TCP_BIAS = 0.7


if __name__ == "__main__":
    host_ips = sys.argv[1:]
    
    while True:
        duration = random.random()*MAX_RANDOM_FLOW_DURATION
        bw =       random.random()*MAX_RANDOM_FLOW_BW
        ip =       random.choice(host_ips)
        
        cmd = f'iperf -t {duration} -c -b {bw}M {ip} '
        
        if random.random()>TCP_BIAS:
            cmd += '-u -p 5051'
        else:
            cmd += '-p 5050' 
        
        subprocess.Popen( cmd ,shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT).wait()
        
        time.sleep(random.random()*MAX_IDLE_TIME)