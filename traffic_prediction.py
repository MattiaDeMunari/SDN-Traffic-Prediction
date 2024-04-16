import os 
import pandas as pd
import matplotlib.pyplot as plt 
from statsmodels.tsa.arima.model import ARIMA
from scapy.all import PcapReader
    
class TrafficPrediction():
    def feature_extraction(self):
        folder_path = "captures"
        output_csv_path = "train"

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
    
    def run_arima(self):
        #percentage of the input data to be used as training, the rest will just be testing data
        training_split = .80 
        csv_path = "train"
        files = os.listdir(csv_path)

        data = []

        for file in files:
            df = pd.read_csv(csv_path+'/'+file, index_col='ds',parse_dates=True)
            print(f"Fitting model for file {file}")
            
            training_data = df.iloc[:int(training_split*len(df))] 
            model = ARIMA( training_data, order=(30,0,0))
            fitted_model = model.fit()
            
            print("model fitting done")
            print(fitted_model.summary())

            prediction = fitted_model.predict(start=df.index.min(),end=df.index.max())
            plt.plot(prediction, label="prediction")
            plt.plot(df, label="data")
            plt.gca().axvline(x=training_data.index.max(), color='red', linestyle='--', label='Training Split')  
            plt.gca().legend()
            plt.show()


if __name__ == "__main__":
    prediction = TrafficPrediction()
    prediction.feature_extraction()
    prediction.run_arima()


