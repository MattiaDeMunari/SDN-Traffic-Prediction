import os 
import math
import argparse


import pandas as pd
import matplotlib.pyplot as plt 
from statsmodels.tsa.arima.model import ARIMA

class TrafficPrediction():
    
    def read_from_csv(self, filename, sample_period):
        self.df = pd.read_csv(filename)
        self.df['ds'] = pd.to_datetime(self.df['ds'], unit='s')   #parse time to a pandas format
        self.df.set_index('ds', inplace=True)  
        self.df = self.df.resample(sample_period).sum(numeric_only=True).fillna(0) 
    
    def run_arima(self, order, training_split=.8):
        #percentage of the input data to be used as training, the rest will just be testing data           
            self.training_data = self.df.iloc[:int(training_split*len(self.df))] 
            model = ARIMA( self.training_data, order=order)
            fitted_model = model.fit()
            
            # print("model fitting done")
            # print(fitted_model.summary())

            self.prediction = fitted_model.predict(start=self.df.index.min(),end=self.df.index.max())
            
    def plot(self, ax):
        ax.plot(self.prediction, label="prediction")
        ax.plot(self.df, label="data")
        ax.axvline(x=self.training_data.index.max(), color='red', linestyle='--', label='Training Split')  
        # ax.legend()
        # plt.title(title)
        # plt.savefig(output_file)
        # plt.show()
        

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Network traffic prediction script")
    parser.add_argument('--csv', type=str, default = "captures", help="Folder containing the csv files to use as input (will ignore pcap-path, store-csv and sample-period)")
    parser.add_argument('--store-plot', type=str, default="plots", help="Folder where to store the plots")
    parser.add_argument('--training-split', type=float, default=.8, help="Percentage of data used for training")
    parser.add_argument('--sample-period', type=str, default=".2S", help="Preiod over which to combine network data")
    
    args = parser.parse_args()
    
        
    if not os.path.exists(args.store_plot):    #create folder for plots
        os.mkdir(args.store_plot)
    
    path = args.csv
    for switch in os.listdir(path):
        intf_csv = [file  for file in os.listdir(os.path.join(path,switch)) if file.endswith('.csv')]
        plot_count = len(intf_csv)
        
        # calculate square to best fit all interfaces
        num_cols = math.ceil(math.sqrt(plot_count)) 
        num_rows = math.ceil(plot_count / num_cols)
        
        fig, axs = plt.subplots(num_rows, num_cols)
        
        fig.suptitle(switch)
        
        for ax, interface in zip(axs.flatten(), intf_csv):
                
            prediction = TrafficPrediction()
            
            full_path = os.path.join(path, switch, interface)
            print(f"Reading file {full_path}")
            
            prediction.read_from_csv(full_path, args.sample_period)
            print("Running ARIMA prediction...")
            prediction.run_arima(order=(30,0,0), training_split=args.training_split)
            
            prediction.plot(ax)
            ax.set_title(interface)

        
    
        plt.tight_layout()
        plt.show()
        
            
    


