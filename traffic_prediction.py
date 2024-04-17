import os 
import pandas as pd
import matplotlib.pyplot as plt 
from statsmodels.tsa.arima.model import ARIMA
from scapy.all import PcapReader
import argparse

class TrafficPrediction():
    def feature_extraction(self, filename, output_filaname=None, sample_period='.2S'):
        data = []
        packets = PcapReader(filename)
        for packet in packets:
            data.append({
                'ds' : pd.to_datetime(float(packet.time), unit='s'),
                'y'  : len(packet),
            })
        
        self.df = pd.DataFrame(data)
        self.df = self.df.resample(sample_period,on='ds').sum(numeric_only=True).fillna(0) 
        
        if output_filaname:
            self.df.to_csv(output_filaname)
    
    
    def read_from_csv(self, filename):
        self.df = pd.read_csv(filename, index_col='ds',parse_dates=True)
    
    def run_arima(self, order, training_split=.8):
        #percentage of the input data to be used as training, the rest will just be testing data           
            self.training_data = self.df.iloc[:int(training_split*len(self.df))] 
            model = ARIMA( self.training_data, order=order)
            fitted_model = model.fit()
            
            # print("model fitting done")
            # print(fitted_model.summary())

            self.prediction = fitted_model.predict(start=self.df.index.min(),end=self.df.index.max())
            
    def plot(self, title, output_file):
        ax = plt.gca()
        plt.plot(self.prediction, label="prediction")
        plt.plot(self.df, label="data")
        ax.axvline(x=self.training_data.index.max(), color='red', linestyle='--', label='Training Split')  
        ax.legend()
        plt.title(title)
        plt.savefig(output_file)
        plt.show()
        

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Network traffic prediction script")
    parser.add_argument('--pcap-path', type=str, default="captures", help="Folder containing the .pcap files to use as input")
    parser.add_argument('--csv', type=str, help="Folder containing the csv files to use as input (will ignore pcap-path, store-csv and sample-period)")
    parser.add_argument('--store-csv', type=str, help="Folder where to store the training data in csv files")
    parser.add_argument('--store-plot', type=str, default="plots", help="Folder where to store the plots")
    parser.add_argument('--training-split', type=float, default=.8, help="Percentage of data used for training")
    parser.add_argument('--sample-period', type=str, default=".2S", help="Preiod over which to combine network data")
    
    args = parser.parse_args()
    
    if args.csv:    #list all the files based on what kind was decided by the arguents
        path = args.csv
        files = [file  for file in os.listdir(path) if file.endswith('.csv')]
    else:
        path = args.pcap_path
        files = [file  for file in os.listdir(path) if file.endswith('.pcap')]
        
        
    if not os.path.exists(args.store_plot):    #create folder for plots
        os.mkdir(args.store_plot)
    
    if args.store_csv and not args.csv and not os.path.exists(args.store_csv):   #create folder for csv only when needed
        os.mkdir(args.store_csv)

    for file in files:
        
        prediction = TrafficPrediction()
        
        full_path = os.path.join(path, file)
        print(f"Reading file {full_path}")
        if args.csv:
            prediction.read_from_csv(full_path)
        else:
            prediction.feature_extraction(full_path, output_filaname=os.path.join(args.store_csv,file) if args.store_csv else None, sample_period=args.sample_period)
        
        print("Running ARIMA prediction")
        prediction.run_arima(order=(30,0,0), training_split=args.training_split)
        prediction.plot(file, os.path.join(args.store_plot, file+'.png'))
        
    


