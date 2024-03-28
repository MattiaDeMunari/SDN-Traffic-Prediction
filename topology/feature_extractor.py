from scapy.all import PcapReader, IP, TCP, UDP, ICMP
import os 
import pandas as pd


folder_path = "captures"
output_csv_path = "train.csv" #not to be confused with the rail transportation vehicle

files = os.listdir(folder_path)

data = []

for file in files:
    print(file)
    packets = PcapReader(folder_path+'/'+file)
    hostname=file.split('_')[0]
    
    for packet in packets:
        
        protocol = packet.name
        
        if IP in packet:  # Ensure the packet has an IP layer
            if TCP in packet:
                protocol = "TCP"
            elif UDP in packet:
                protocol = "UDP"
            elif ICMP in packet:
                protocol = "ICMP"
            else:
                protocol = "IP"
            
        data.append({
            
            'Time' :          packet.time,
            'Hostname':       hostname,
            'Source IP':      packet['IP'].src if 'IP' in packet else None,
            'Destination IP': packet['IP'].dst if 'IP' in packet else None,
            'Protocol':       protocol,
            'Length': len(packet),
        })

df = pd.DataFrame(data)
df = df.sort_values(by='Time', ascending=True)  #sort by time
df.reset_index(drop=True, inplace=True)

start_time = df['Time'][0]
df['Time'] = df['Time'] -  start_time #time offset so it's 0 and not unix time


df.to_csv(output_csv_path, index=True)  