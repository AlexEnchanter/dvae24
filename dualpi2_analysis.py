
from argparse import ArgumentParser
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import heatmap as hm

import glob
import os

file_name = "iperf_client*.log"

delays = [4, 10, 20, 40, 80, 100]
rates = [5, 10, 20, 40, 80, 100, 400]

heatmap_dict = {}

# This feels stupid :/
for dealy in delays:
    heatmap_dict[delay] = {}

for dealy in delays:
    for rate in rates:
        heatmap_dict[ecn][aqm] = []
        
# [ ID] Interval            Transfer    Bandwidth       Write/Err  Rtry     Cwnd/RTT        NetPwr
# [  3] 0.0000-0.1000 sec   230 KBytes  18.9 Mbits/sec  3/0          5       14K/137773 us  17.13

print("This will take some time...")
for delay in delays:
    for rate in rates:
        print(f"{delay}+{rate}")
        files = glob.glob(f"result/dualpu2/{delay}/{rate}/{file_name}")
        
        dictionary = {}
        # Format shoud be iperf_client_<CC>_<run>.log
        for file in files:
            key = os.path.basename(file).rpartition(".log")[0].split("_")[3]
            group = dictionary.get(key, [])
            group.append(file)
            dictionary[key] = group
    

        for key in dictionary:
            bw_fig, bw_ax = plt.subplots()
            cwnd_fig, cwnd_ax = plt.subplots()
            for file in dictionary[key]:
                times = []
                bandwidth = []
                cwnd = []

                # print("file:", file)
                cc = os.path.basename(file).rpartition(".log")[0].split("_")[2]
                with open(file) as f:
                    lines = f.readlines()
     
                    # Read lines until iperf header
                    while "ID" not in lines[0]:
                        lines = lines[1:]
                    lines = lines[1:]


                    if cc == "prague":
                        heatmap_dict[delay][rate].append(float(lines[-1].split()[6]))
                    # lines = lines[100:]
    
                    # We get lines like if we split:
                    #   0    1           2           3      4       5        6           7        8     9         10       11    12
                    # ['[', '3]', '0.0000-0.1000', 'sec', '230', 'KBytes', '18.9', 'Mbits/sec', '3/0', '5', '14K/137773', 'us', '17.13']
                    for line in lines[:-1]:
                        values = line.split()
        
                        # Get time; If output is a-b, is it better to get b or a? 
                        times.append(float(values[2].split("-")[1]))

                        bandwidth.append(float(values[6]))
    
                        cwnd.append(int(values[10].split("/")[0].strip("K")))
                        
                bw_data = pd.DataFrame({"bw": bandwidth})
                bw_rolling = bw_data.bw.rolling(20).mean()
                
                bw_ax.plot(times, bw_rolling, label=cc)
                bw_ax.set_xlabel("Time (s)")
                bw_ax.set_ylabel("Bandwidth (Mbps)")
                bw_ax.set_title(f"TCP Bandwidth rolling mean, 2 flows run {key} ({delay}, {rate})")
                bw_ax.legend()
                bw_fig.savefig(f"result/{delay}/{rate}/bw_run_{key}.png")
                
                cwnd_ax.plot(times, cwnd, label=cc)
                cwnd_ax.set_xlabel("Time (s)")
                cwnd_ax.set_ylabel("cwnd")
                cwnd_ax.set_title(f"TCP cwnd 2 flows run {key}, ({delay}, {rate})")
                cwnd_ax.legend()
                cwnd_fig.savefig(f"result/{delay}/{rate}/cwnd_run_{key}.png")
                
            plt.close(bw_fig)
            plt.close(cwnd_fig)

# Print heatmap:
for delay in heatmap_dict:
    for rate in heatmap_dict[rate]:
        mean = np.mean(heatmap_dict[delay][rate]).item()
        print(f"Delay: {delay}, Bottleneck Rate: {rate}, Measured Rate: {mean}, Expected around: {mean/2}")
