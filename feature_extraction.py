from scapy.all import PcapReader
import os 
import pandas as pd


folder_path = "captures"
output_csv_path = "train" #not to be confused with the rail transportation vehicle

files = os.listdir(folder_path)



for file in files:
    print(file)
    packets = PcapReader(folder_path+'/'+file)
    data = []
    for packet in packets:
        data.append({
            'ds' : pd.to_datetime(float(packet.time), unit='s'),
            'y'  : len(packet),
        })
    
    df = pd.DataFrame(data)
    df = df.resample('.2S',on='ds').sum(numeric_only=True).fillna(0) 
    print(df)
    df.to_csv(output_csv_path+'/'+file+".csv")
    