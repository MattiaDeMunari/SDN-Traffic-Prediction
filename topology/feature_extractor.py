from scapy.all import PcapReader, IP, TCP, UDP, ICMP
import os 
import pandas as pd
from prophet import Prophet
import matplotlib.pyplot as plt 


folder_path = "captures"
output_csv_path = "train.csv" #not to be confused with the rail transportation vehicle

files = os.listdir(folder_path)

data = []

for file in files:
    print(file)
    packets = PcapReader(folder_path+'/'+file)

    for packet in packets:
        data.append({
            'ds'    : pd.to_datetime(float(packet.time), unit='s'),
            'y': len(packet),
        })
    
    df = pd.DataFrame(data)
    df = df.resample('.1S',on='ds').sum(numeric_only=True).fillna(0)       #take the total bandwidth every second for each switch
    df = df.reset_index()
    
    
    print(f"Fitting model for file {file}")
    model = Prophet()
    model.fit(df)
    print("Model fit")
    future = model.make_future_dataframe(periods=5,freq='1S',include_history=True) 
    forecast = model.predict(future)
    print(forecast)
    model.plot(forecast)
    plt.show()







