from mininet.topo import Topo
from mininet.net import Mininet
from mininet.node import OVSKernelSwitch, RemoteController
from mininet.cli import CLI
from mininet.link import TCLink
from mininet.log import setLogLevel, info

from subprocess import *

import time
import re
import random
import os


# ---------------------------------------------------------------- #
# -------------------------- Parameters -------------------------- #
# ---------------------------------------------------------------- #

SWITCHES = 5
HOSTS = 3
CROSS_CONNECTION = .30    #30% chance of having cross connections


IDLE_PERCENT = .2         #probability of a host remaining idle
TEST_TIME = 30            #test time in seconds
IPERF_TIME_TCP = 2
IPERF_TIME_UDP = 0.2
HOST_LINK_MAX_BW = 2
HOST_LINK_MIN_BW = 0.2
SWITCH_LINK_MAX_BW = 5
SWITCH_LINK_MIN_BW = 1

folder_path = "captures"  #folder to temporarily store the .pcap captures in 

NUM_BASE_FLOWS = 3 #number of iperf flows in the background

class arbitrary_topology(Topo):
    def build(self, total_switches, max_hosts_per_switch, interconnectivity, seed=0):
        global host_count
        random.seed(seed)

        host_count = 0 
        #create all the switces and hosts
        for i in range(total_switches):
            switch_dpid = f"s{i+1}"
            self.addSwitch(switch_dpid, stp=True, failMode='standalone')    #stp to avoid loops in the networks 

            if i > 0:
                self.addLink(switch_dpid, f"s{i}")      #add link to previous switch in a line topology

            #for each switch create and connect all the hosts
            for j in range(random.randrange(max_hosts_per_switch)):
                host_dpid = f"h{host_count+1}"
                self.addHost(host_dpid)
                self.addLink(switch_dpid, host_dpid, bw = random.random()*(SWITCH_LINK_MAX_BW-SWITCH_LINK_MIN_BW) + SWITCH_LINK_MIN_BW )
                host_count +=1
    

        # add connections between switches
        connected_pairs = set()
        for i in range(1, total_switches + 1):
            for j in range(1, total_switches + 1):
                # do not link with yourself 
                if i == j:
                    continue
                # already linked with previous router 
                if i == j + 1 or i == j - 1:
                    continue
                # check if the reverse connection already exists
                if (j, i) in connected_pairs:
                    continue

                if random.random() < interconnectivity:
                    connected_pairs.add((i, j))  # Add the connected pair to the set
                    self.addLink(f"s{i}", f"s{j}", bw = random.random()*(HOST_LINK_MAX_BW-HOST_LINK_MIN_BW) + HOST_LINK_MIN_BW)

if __name__ == "__main__":

    #clean mininet istances without print stdout
    info('*** Clean net\n')
    Popen("mn -c", shell=True, stdout=DEVNULL, stderr=STDOUT).wait()

    #topology creation
    topo = arbitrary_topology(SWITCHES,HOSTS,CROSS_CONNECTION,0)

    #logging
    setLogLevel('info')

    #controller
    controller = RemoteController("c0", ip="0.0.0.0", port=6633) 
    
    #mininet set-up (mac and ip auto-set)
    net = Mininet(                                                
        topo=topo,
        switch=OVSKernelSwitch,
        build=False,
        autoSetMacs=True,
        autoStaticArp=True,
        link=TCLink,
        controller=controller
    )

    net.build()     
    net.start()
    ##-----------------------------TESTING--------------------------------------
    # time.sleep(1)
    # print("TESSTSTSSTSTT")
    
    # print(net.switches)
    
    # time.sleep(1)
    # net.stop()
    # exit()
    ##-----------------------------TESTING--------------------------------------
    

    print("\n\n--------------------------------------------------------------------------------")    
    print("Network built, waiting for STP to configure itself\n\n")    

    s1 = net.get("s1")   #check he state stp, we wait until s1 says "forward" which indicates it is complete
    while(s1.cmdPrint('ovs-ofctl show s1 | grep -o FORWARD | head -n1') != "FORWARD\r\n"): 
        time.sleep(3)
    print("STP ok, waiting 5 seconds...")
    time.sleep(5)
    
    print("\n\n--------------------------------------------------------------------------------")    
    print("Testing ping connectivity\n\n")    

    net.pingAll()
    time.sleep(1)
    
    print("\n\n--------------------------------------------------------------------------------")    
    print("Begin traffic capturing\n\n")    
    
    #empty folder 
    Popen(f"rm -rf {folder_path}", shell=True, stdout=DEVNULL, stderr=STDOUT).wait()    #delete the folder contents before starting
    os.mkdir(folder_path)   

    for s in net.switches:                 #run tcpdump to capture all packets passing through every switch
        s.cmd(f"tcpdump -w {folder_path}/{s.name}_capture.pcap &")


    time.sleep(2)
    
    print("\n\n--------------------------------------------------------------------------------")    
    print("Begin traffic generation\n\n")    
    
    random.seed(time.time())
    
    
    
    #Start iperf (TCP and UDP) server on Hosts
    for h in net.hosts:
        h.cmd('iperf -s -p    5050 &') #start iperf -Server on -Port 5050
        h.cmd('iperf -s -u -p 5051 &') #start -UDP server as well

    for h in random.sample(net.hosts, NUM_BASE_FLOWS):
        hosts = net.hosts.copy()
        hosts.remove(h)  #do not pick yourself
        h.cmd(f"iperf -c -p 5050 {random.choice(hosts)} &")  #start iperf client
        
    for h in net.hosts:
        hosts = net.hosts.copy()
        hosts.remove(h)  #do not pick yourself
        host_ips = [h.IP() for h in hosts]
        h.cmd(f"python3 host_traffic_gen.py {' '.join(map(str, host_ips))} &")
        
        
    print(f"Test traffic started, waiting for test time ({TEST_TIME} seconds)")
    time.sleep(TEST_TIME)

    
    net.stop()