import os 
import math
import argparse


import pandas as pd
import matplotlib.pyplot as plt 
from statsmodels.tsa.arima.model import ARIMA

class TrafficPrediction():
    
    def read_from_csv(self, filename, sample_period):
        self.df = pd.read_csv(filename)
        # parse time from unix to pandas format
        self.df['ds'] = pd.to_datetime(self.df['ds'], unit='s')   
        
        # resample
        self.df.set_index('ds', inplace=True)  
        self.df = self.df.resample(sample_period).sum(numeric_only=True).fillna(0) 
        
        # convert from bytes to Mbps
        self.df['y'] /= pd.Timedelta(sample_period).total_seconds()
        self.df['y'] *= 8 
        self.df['y'] /= 2**20
        
    
    def run_arima(self, order, training_split=.8):
        # percentage of the input data to be used as training, the rest will just be testing data           
        self.training_data = self.df.iloc[:int(training_split*len(self.df))] 
        
        model = ARIMA( self.training_data, order=order)
        fitted_model = model.fit()
        
        # print(fitted_model.summary())

        self.prediction = fitted_model.predict(start=self.df.index.min(),end=self.df.index.max())
            
    def plot(self, ax):
        ax.plot(self.prediction, label="prediction") 
        ax.plot(self.df, label="data", linestyle = 'dotted')
        ax.axvline(x=self.training_data.index.max(), color='red', linestyle='--', label='Training Split')  
        

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Network traffic prediction script")
    parser.add_argument('--csv', type=str, default = "captures", help="Folder containing the csv files to use as input")
    parser.add_argument('--store-plot', type=str, default="plots", help="Folder where to store the plots")
    parser.add_argument('--training-split', type=float, default=.8, help="Percentage of data used for training")
    parser.add_argument('--sample-period', type=str, default="0.2S", help="Preiod over which to combine network data")
    
    args = parser.parse_args()
    
        
    if not os.path.exists(args.store_plot):    #create folder for plots
        os.mkdir(args.store_plot)
    
    
    path = args.csv
    for switch in os.listdir(path):
        intf_csv = [file  for file in os.listdir(os.path.join(path,switch)) if file.endswith('.csv')]
        
        # calculate square to best fit all interfaces
        plot_count = len(intf_csv)
        
        if plot_count == 0:
            print(f"No .csv file found in {switch} folder")
            continue
        
        num_cols = math.ceil(math.sqrt(plot_count)) 
        num_rows = math.ceil(plot_count / num_cols)
        
        fig, axs = plt.subplots(num_rows, num_cols, sharey=True, sharex=False, figsize=(12, 8))
        
        # makes subplots a 1d array so we can access it with a single for loop
        axs = axs.flatten()
        
        for ax, interface in zip(axs, intf_csv):
            prediction = TrafficPrediction()
            
            full_path = os.path.join(path, switch, interface)
            
            print(f"Reading file {full_path}")
            prediction.read_from_csv(full_path, args.sample_period)
            
            print("Running ARIMA prediction...")
            prediction.run_arima(order=(30,0,0), training_split=args.training_split)
            
            prediction.plot(ax)
            ax.set_title(interface[:-4]) # remove ".csv" from the plot name

        #disable all unused plots
        for ax in axs[plot_count:]:
            ax.axis('off')
        
        fig.legend(*axs[0].get_legend_handles_labels(),fancybox=True)
        fig.suptitle(switch, fontsize=29)
        
        plt.tight_layout(pad=0.5)
        plt.savefig(os.path.join(args.store_plot,switch)+'.png')
        plt.show()
        
            
    


