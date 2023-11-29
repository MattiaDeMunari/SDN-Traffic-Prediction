from mininet.topo import Topo
from mininet.net import Mininet
from mininet.node import OVSKernelSwitch, RemoteController
from mininet.cli import CLI
from mininet.link import TCLink
from mininet.log import setLogLevel, info

from subprocess import Popen

import time
import random

# ---------------------------------------------------------------- #
# -------------------------- Parameters -------------------------- #
# ---------------------------------------------------------------- #
SWITCHES = 5
HOSTS = 3
CROSS_CONNECTION = .30 #30% chance of having cross connections
IDLE_PERCENT = .05 #probability of a host remaining idle
TEST_TIME = 30 #test time in seconds

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
                self.addLink(switch_dpid, host_dpid)
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
                    self.addLink(f"s{i}", f"s{j}")


if __name__ == "__main__":

    #clean mininet istances
    info('*** Clean net\n')
    Popen("mn -c", shell=True).wait()

    #topology creation
    topo = arbitrary_topology(SWITCHES,HOSTS,CROSS_CONNECTION,0)

    #Logging
    setLogLevel('info')

    #Controller
    controller = RemoteController("c0", ip="0.0.0.0", port=6633) 
    
    #Mininet set-up (mac and ip auto-set)
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

    CLI(net)    #once done open the minent Command Line Interface for testing before exiting
    net.stop()

    print("\n\n--------------------------------------------------------------------------------")    
    print("Network built, waiting for STP to configure itself\n\n")    

    s1 = net.get("s1")   #check he state stp, we wait until s1 says "forward" which indicates it is complete
    while(s1.cmdPrint('ovs-ofctl show s1 | grep -o FORWARD | head -n1') != "FORWARD\r\n"): 
        time.sleep(3)
    time.sleep(5)
    print("\n\n--------------------------------------------------------------------------------")    
    print("STP ok, testing ping connectivity\n\n")    

    net.pingAll()

    print("\n\n--------------------------------------------------------------------------------")    
    print("Begin traffic generation\n\n")    
    
    random.seed(0)


    #Hosts array
    hs = [net.get(f"h{host}") for host in range(1,host_count+1)]


    #Start a HTTP server on Host h1
    http_server = random.choice(hs)
    http_server.cmd('python2 -m SimpleHTTPServer 80 &')

    #Start iperf (TCP and UDP) server on Random Hosts
    iperf_TCP_server = random.choice(hs)
    iperf_TCP_server.cmd('iperf -s -p 5050 &') 
    
    iperf_UDP_server = random.choice(hs)
    iperf_UDP_server.cmd('iperf -s -u -p 5051 &')


    end_time = time.time() + TEST_TIME  
    while time.time() < end_time:  #do this for 30 seconds
        for h in hs:
            if random.random() < IDLE_PERCENT:  #sometimes the client doesn't do anything
                continue
            actions = [ lambda: h.cmd(f"iperf -p 5050 -t 1 -c {iperf_TCP_server.IP()}"),      #iperf server TCP
                        lambda: h.cmd(f"iperf -p 5051 -t 1 -u -c {iperf_UDP_server.IP()}"),   #iperf random host UDP 
                        lambda: h.cmd(f"wget  http://{http_server.IP()} -O /dev/null"),                     #http request
                        lambda: h.cmd(f"wget  http://{http_server.IP()}/test.zip -O /dev/null")]            #http download file
            random.choice(actions)() #call a random action 

    


    CLI(net)    #once done open the minent Command Line Interface for testing before exiting
    net.stop()