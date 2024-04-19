from scapy.all import AsyncSniffer, get_if_list
import csv
import sys
import re
import time

if __name__ == '__main__': 
    interface_pattern = re.compile(r's\d+-eth\d+') #find mn interfaces (s1-eth1) etc
    attempts = 0
    interfaces = []
    while attempts < 10:
        interfaces = [i for i in get_if_list() if interface_pattern.match(i)]  
        if len(interfaces)>0:
            break
        print(f"No interface found on attemp {attempts}, retrying in 2 seconds...")
        time.sleep(2)
    else:
        print(f"ERROR: could not find network adapters in {attempts} attempts, quitting")
        exit(1)
    
    sniffers = []
    for i in interfaces:
        csvfile = open(f"{i}.csv", 'w', newline='')
        writer = csv.writer(csvfile)
        writer.writerow(['ds', 'y'])
        
        print (f" Beginning capture on {i}")
        
        packet_handler = lambda pkt, writer=writer:print([pkt.time, len(pkt)])
        
        sniffer = AsyncSniffer(iface=i, store=False, prn=packet_handler)
        sniffer.start()
        
        sniffers.append((sniffer,csvfile))
        
    if len(sniffers)==0:
        print("No mininet switch was found to be running, exiting program...")
        exit(1)
        
    if len(sys.argv) > 1:
        time.sleep(float(sys.argv[1]))
    else:
        input("No test time provided, press Enter to terminate...")
    
    for sniffer, csvfile in sniffers:
        sniffer.stop()
        csvfile.close()