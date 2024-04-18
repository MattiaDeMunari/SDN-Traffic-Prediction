import os 
import pandas as pd
import matplotlib.pyplot as plt 
from statsmodels.tsa.arima.model import ARIMA
from scapy.all import PcapReader
import argparse

class TrafficPrediction():
    
    def read_from_csv(self, filename, sample_period):
        self.df = pd.read_csv(filename, index_col='ds',parse_dates=True)
        self.df = self.df.resample(sample_period,on='ds').sum(numeric_only=True).fillna(0) 
    
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
    parser.add_argument('--csv', type=str, default = "captures", help="Folder containing the csv files to use as input (will ignore pcap-path, store-csv and sample-period)")
    parser.add_argument('--store-plot', type=str, default="plots", help="Folder where to store the plots")
    parser.add_argument('--training-split', type=float, default=.8, help="Percentage of data used for training")
    parser.add_argument('--sample-period', type=str, default=".2S", help="Preiod over which to combine network data")
    
    args = parser.parse_args()
    
    path = args.csv
    files = [file  for file in os.listdir(path) if file.endswith('.csv')]
        
    if not os.path.exists(args.store_plot):    #create folder for plots
        os.mkdir(args.store_plot)

    for file in files:
        
        prediction = TrafficPrediction()
        
        full_path = os.path.join(path, file)
        print(f"Reading file {full_path}")
        
        prediction.read_from_csv(full_path, args.sample_period)
      
        print("Running ARIMA prediction")
        prediction.run_arima(order=(30,0,0), training_split=args.training_split)
        prediction.plot(file, os.path.join(args.store_plot, file+'.png'))
        
    


