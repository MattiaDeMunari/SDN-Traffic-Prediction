import os 
import pandas as pd
import matplotlib.pyplot as plt 
from statsmodels.tsa.arima.model import ARIMA

csv_path = "train" #not to be confused with the rail transportation vehicle
training_split = .80 #percentage of the input data to be used as training, the rest will just be testing data
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
    
    # # line plot of residuals
    # residuals = pd.DataFrame(fitted_model.resid)
    # residuals.plot()
    # plt.show()
    
    # # density plot of residuals
    # residuals.plot(kind='kde')
    # plt.show()
    
    
    prediction = fitted_model.predict(start=df.index.min(),end=df.index.max())
    plt.plot(prediction, label="prediction")
    plt.plot(df, label="data")
    plt.gca().axvline(x=training_data.index.max(), color='red', linestyle='--', label='Training Split')  # Customize color, linestyle, and label as needed
    plt.gca().legend()
    plt.show()

    

