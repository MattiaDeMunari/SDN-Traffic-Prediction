from mininet.topo import Topo
from mininet.net import Mininet
from mininet.node import OVSKernelSwitch, RemoteController
from mininet.cli import CLI
from mininet.link import TCLink
from mininet.log import setLogLevel, info


from subprocess import Popen

import time
import random


class arbitrary_topology(Topo):
    def build(self, total_switches, max_hosts_per_switch, interconnectivity, seed=0):
        global host_count
        random.seed(seed)

        host_count =0 
        #create all the switces and hosts
        for i in range(total_switches):
            switch_dpid = f"s{i+1}"
            self.addSwitch(switch_dpid, stp=True, failMode='standalone')    #stp to avoid loops in the networks 
            #for each switch create and connect all the hosts
            for j in range(random.randrange(max_hosts_per_switch)):
                host_dpid = f"h{host_count+1}"
                self.addHost(host_dpid)
                self.addLink(switch_dpid, host_dpid)
                host_count +=1
        
        # add connections between switches
        for i in range(total_switches):
            for j in range(total_switches):
                # you can't connect to yourself 
                if j == i:
                    continue

                # j == i+1 ensures a line topology connection through all the hosts
                # we then use the interconnectivity percentage to add extra links in a random way
                if j == i+1 or random.random() < interconnectivity:
                    switch1_dpid = f"s{i+1}"
                    switch2_dpid = f"s{j+1}"
                    try:
                        #check if reverse link already exists
                        #garbage hack but it works
                        self.linkInfo(switch2_dpid,switch1_dpid)
                        print(f"Link {switch1_dpid} <-> {switch2_dpid} Already exists")
                    except:
                        self.addLink(switch1_dpid, switch2_dpid)



if __name__ == "__main__":
    info('*** Clean net\n')
    cmd = "mn -c"                      #run sudo mn -c to clear mininet
    Popen(cmd, shell=True).wait()
    
    idle_percent = .05
    NUM_ITERATIONS = 512
    topo = arbitrary_topology(5,3,.3,0)     #crete a network with 5 switches, each with 0-3 hosts and a 30% chance of having cross connections

    setLogLevel( 'info' )
    controller = RemoteController("c0", ip="0.0.0.0", port=6633) 
    net = Mininet(                                                #configure miniset, autoatically set mac and ip addresses 
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

    #gather hosts in an easy-to-access array
    hs = [net.get(f"h{host+1}") for host in range(host_count)]
    
    #start a http server on host h1
    http_server = random.choice(hs)
    http_server.cmd('python2 -m SimpleHTTPServer 80 &')

    iperf_TCP_server = random.choice(hs)
    iperf_TCP_server.cmd('iperf -s -p 5050 &') 
    
    iperf_UDP_server = random.choice(hs)
    iperf_UDP_server.cmd('iperf -s -u -p 5051 &')



    end_time = time.time() + 30  
    while time.time() < end_time:  #do this for 30 seconds
        for j,h in enumerate(hs):
            if random.random() < idle_percent:  #sometimes the client doesn't do anything
                continue
            actions = [ lambda: h.cmd(f"iperf -p 5050 -t 1 -c {iperf_TCP_server.IP()}"),      #iperf server TCP
                        lambda: h.cmd(f"iperf -p 5051 -t 1 -u -c {iperf_UDP_server.IP()}"),   #iperf random host UDP 
                        lambda: h.cmd(f"wget  http://{http_server.IP()} -O /dev/null"),                     #http request
                        lambda: h.cmd(f"wget  http://{http_server.IP()}/test.zip -O /dev/null")]            #http download file
            random.choice(actions)() #call a random action 

    


    CLI(net)    #once done open the minent Command Line Interface for testing before exiting
    net.stop()