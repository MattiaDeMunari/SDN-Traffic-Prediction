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
            self.addSwitch(switch_dpid, stp=True, failMode='standalone')
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
    cmd = "mn -c"
    Popen(cmd, shell=True).wait()
    
    idle_percent = .05
    NUM_ITERATIONS = 512
    topo = arbitrary_topology(5,3,.3,0)

    setLogLevel( 'info' )
    controller = RemoteController("c0", ip="0.0.0.0", port=6633) #ifconfig - copy and past ip
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


    print("\n\n--------------------------------------------------------------------------------")    
    print("Network built, waiting for STP to configure itself\n\n")    


    s1 = net.get("s1")
    while(s1.cmdPrint('ovs-ofctl show s1 | grep -o FORWARD | head -n1') != "FORWARD\r\n"):
        time.sleep(3)
    print("\n\n--------------------------------------------------------------------------------")    
    print("STP ok, testing ping connectivity\n\n")    

    net.pingAll()

    print("\n\n--------------------------------------------------------------------------------")    
    print("Begin traffic generation\n\n")    

    hs = [net.get(f"h{host+1}") for host in range(host_count)]
    
    
    hs[0].cmd('python2 -m SimpleHTTPServer 80 &')

    random.seed(0)

    for i in range (NUM_ITERATIONS):
        for j,h in enumerate(hs):
            if random.random() < idle_percent:
                continue
            print("aaa")
            actions = [ lambda: h.cmd(f"iperf -p 5050 -c {random.choice(hs).IP}"),     #iperf random host
                        lambda: h.cmd(f"iperf -p 5050 -c {hs[(i+1)%host_count].IP}"),  #iperf specifc host
                        lambda: h.cmd(f"iperf -p 5050 -u -c {random.choice(hs).IP}"),  #iperf random host UDP
                        lambda: h.cmd(f"wget  http://{hs[0].IP}"),                     #http request
                        lambda: h.cmd(f"wget  http://{hs[0].IP}/test.zip")]            #http download file

            random.choice(actions)()

    


    CLI(net)
    net.stop()