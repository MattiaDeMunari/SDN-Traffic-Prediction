from mininet.topo import Topo
from mininet.net import Mininet
from mininet.node import OVSKernelSwitch, RemoteController
from mininet.cli import CLI
from mininet.link import TCLink
from mininet.log import setLogLevel, info

from subprocess import *

import time
import random
import os
import networkx as nx
import matplotlib.pyplot as plt
import argparse

#Simulation parameters
TEST_TIME = 30 
folder_captures = "captures" 

#Connection parameters
NUM_IPERF_FLOWS = 0
HOST_LINK_MAX_BW = 2
HOST_LINK_MIN_BW = 1
SWITCH_LINK_MAX_BW = 2
SWITCH_LINK_MIN_BW = 1

class Topology(Topo):
    def __init__(self, num_switches, num_hosts, interconnectivity, seed = 0):
            super().__init__()
            self.num_switches = num_switches
            self.num_hosts = num_hosts
            self.interconnectivity = interconnectivity
            self.seed = seed

            global host_count
            random.seed(self.seed)
            host_count = 0 
            #create all the switces and hosts
            for i in range(self.num_switches):
                switch_dpid = f"s{i+1}"
                self.addSwitch(switch_dpid, stp=True, failMode='standalone')    #stp to avoid loops in the networks 

                if i > 0:
                    self.addLink(switch_dpid, f"s{i}")      #add link to previous switch in a line topology

                #for each switch create and connect all the hosts
                for j in range(random.randrange(self.num_hosts)):
                    host_dpid = f"h{host_count+1}"
                    self.addHost(host_dpid)
                    self.addLink(switch_dpid, host_dpid, bw = random.random()*(SWITCH_LINK_MAX_BW-SWITCH_LINK_MIN_BW) + SWITCH_LINK_MIN_BW )
                    host_count +=1

            # add connections between switches
            connected_pairs = set()
            for i in range(1, self.num_switches + 1):
                for j in range(1, self.num_switches + 1):
                    # do not link with yourself 
                    if i == j:
                        continue
                    # already linked with previous router 
                    if i == j + 1 or i == j - 1:
                        continue
                    # check if the reverse connection already exists
                    if (j, i) in connected_pairs:
                        continue

                    if random.random() < self.interconnectivity:
                        connected_pairs.add((i, j))  # Add the connected pair to the set
                        self.addLink(f"s{i}", f"s{j}", bw = random.random()*(HOST_LINK_MAX_BW-HOST_LINK_MIN_BW) + HOST_LINK_MIN_BW)
    
    def saving_topology(self):
        G = nx.Graph()
        
        switch_color = 'red'
        host_color = 'orange'
        image_file = "topology_image.png"
        
        for node in self.nodes():
            if node.startswith('s'):
                G.add_node(node, color=switch_color, node_type='switch')
            else:
                G.add_node(node, color=host_color, node_type='host')

        for link in self.links():
            G.add_edge(link[0], link[1])

        switch_nodes = [node for node, attr in G.nodes(data=True) if attr['node_type'] == 'switch']
        host_nodes = [node for node, attr in G.nodes(data=True) if attr['node_type'] == 'host']
        
        pos = nx.spring_layout(G, seed=42)
        nx.draw_networkx_nodes(G, pos, nodelist=switch_nodes, node_color=switch_color, node_size=500, label='Switches')
        nx.draw_networkx_nodes(G, pos, nodelist=host_nodes, node_color=host_color, node_size=300, label='Hosts')
        nx.draw_networkx_edges(G, pos)
        nx.draw_networkx_labels(G, pos)

        plt.savefig(image_file)
        print(f"\n*** Topology saved as '{image_file}'")

class NetworkManager:
    def __init__(self):
        self.net = None

    def clean_network(self):
        info('*** Clean network instances\n')
        Popen("mn -c", shell=True, stdout=DEVNULL, stderr=STDOUT).wait()
    
    def create_net(self, topology):
        self.net = Mininet(                                                
            topo=topology,
            switch=OVSKernelSwitch,
            build=False, 
            autoSetMacs=True,
            autoStaticArp=True,
            link=TCLink
        )
        return self.net

    def check_stp_configuration(self):
        s1 = self.net.get("s1")   #check he state stp, we wait until s1 says "forward" which indicates it is complete
        while(s1.cmdPrint('ovs-ofctl show s1 | grep -o FORWARD | head -n1') != "FORWARD\r\n"): 
            time.sleep(3)

    def start_servers(self, base_flows):    
        random.seed(time.time()) #reset random seed
        for h in self.net.hosts:
            h.cmd('iperf -s -p 5050 &') #start iperf -Server on -Port 5050

        # for h in random.sample(self.net.hosts, base_flows):
        #     hosts = self.net.hosts.copy()
        #     hosts.remove(h)  #do not pick yourself
        #     h.cmd(f"iperf -c -p 5050 {random.choice(hosts)} &")  #start iperf client
            
        for h in self.net.hosts:
            hosts = self.net.hosts.copy()
            hosts.remove(h)  #do not pick yourself
            host_ips = [h.IP() for h in hosts]
            h.cmd(f"python3 utils/traffic_generation.py {' '.join(map(str, host_ips))} &")
    
    def create_captures_folder(self): 
        Popen(f"rm -rf {folder_captures}", shell=True, stdout=DEVNULL, stderr=STDOUT).wait()    #delete the folder contents before starting
        os.mkdir(folder_captures) 

    def start_switch_tcpdump(self, combine_interfaces):
        for s in self.net.switches: #run tcpdump to capture all packets passing through every switch
            if combine_interfaces:
                s.cmd(f"tcpdump -w {folder_captures}/{s.name}.pcap &")
            else:
                for i in s.intfList():
                    if i.name != 'lo': #avoid loopback address
                        s.cmd(f"sudo tcpdump -i {i.name} -w {folder_captures}/{i.name}.pcap &")
                    
            print(f"started capturing on {s}")
        
    def stop_switch_tcpdump(self):
        for s in self.net.switches:
            s.cmd('pkill -f "tcpdump"')

if __name__ == "__main__":

    parser = argparse.ArgumentParser(description="Network Testing Script")
    parser.add_argument('--switches', type=int, default=7, help="Number of switches")
    parser.add_argument('--hosts', type=int, default=2, help="Number of hosts per switch")
    parser.add_argument('--cross-connection', type=float, default=0.30, help="Percentage of cross-connections between non-adjacent switches")
    parser.add_argument('--time', type=int, default=30, help="Duration of the test in seconds")
    parser.add_argument('--base-flows', type=int, default=0, help="Number of constant iperf flows")
    parser.add_argument('--combine-interfaces', type=bool, default=False, help="Enable to combine all the interfaces of 1 switch into a single .pcap")
    args = parser.parse_args()

    #Arguments
    SWITCHES = args.switches
    HOSTS_PER_SWITCH = args.hosts
    CROSS_CONNECTION = args.cross_connection
    TEST_TIME = args.time 
    NUM_IPERF_FLOWS = args.base_flows
    
    network = NetworkManager()
    network.clean_network()

    topology = Topology(SWITCHES, HOSTS_PER_SWITCH, CROSS_CONNECTION, 0)
    topology.saving_topology()

    setLogLevel('info')
    net = network.create_net(topology)
    
    net.build()     
    net.start()
    time.sleep(1)
    
    print("\n*** Network built, waiting for STP to configure itself")    
    network.check_stp_configuration()
    
    print("\n*** STP ok, waiting 5 seconds...")
    time.sleep(5)
    
    print("\n*** Testing ping connectivity...")    
    net.pingAll()
    time.sleep(1)
    # CLI(net)


    print("\n*** Begin traffic generation\n\n")    
    network.start_servers(NUM_IPERF_FLOWS)
    random.seed(time.time())
    time.sleep(5)
        
    print("\n*** Begin traffic capturing\n\n")    
    network.create_captures_folder()
    network.start_switch_tcpdump(args.combine_interfaces)

    print(f"\n*** Test traffic started, waiting for test time ({TEST_TIME} seconds)")
    time.sleep(TEST_TIME)

    print("\n*** Stopping traffic capture...")
    network.stop_switch_tcpdump()
    net.stop()