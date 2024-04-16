
# Networking with Mininet and Ryu: Traffic Prediction in SDN Networks

## Overview

This project aims to analyze traffic patterns and predict traffic in Software-Defined Networking (SDN) environments using Mininet and Ryu. The goal is to capture network traffic, train a machine learning model for traffic prediction, and analyze the model's performance.


## Getting Started
Clone the repository
```bash
git clone https://github.com/MattiaDeMunari/SDN-Traffic-Prediction
```

## Requirements

Mininet and Ryu can be installed following the instructions in its  [website](https://www.granelli-lab.org/researches/relevant-projects/comnetsemu-labs). The application require Python 3.

The required packages can be installed with pip:
```bash
pip3 install -r requirements.txt
```
## Execution
Build the topology and generate traffic:  
```bash
 sudo python3 main.py
```
Start traffic prediction process:  
```bash
 sudo python3 traffic_prediction.py
```
