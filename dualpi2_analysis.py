
from argparse import ArgumentParser
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import heatmap as hm

import glob
import os

file_name = "iperf_client*.log"

delays = [4, 10, 20, 80, 100, 200, 400, 1000]
rates = [5, 10, 20, 80, 100, 400, 800, 1000]

heatmap_dict = {}

# This feels stupid :/
for delay in delays:
    heatmap_dict[delay] = {}

for delay in delays:
    for rate in rates:
        heatmap_dict[delay][rate] = []
        
# [ ID] Interval            Transfer    Bandwidth       Write/Err  Rtry     Cwnd/RTT        NetPwr
# [  3] 0.0000-0.1000 sec   230 KBytes  18.9 Mbits/sec  3/0          5       14K/137773 us  17.13

print("This will take some time...")
for delay in delays:
    for rate in rates:
        print(f"{delay}+{rate}")
        files = glob.glob(f"result/dualpi2/{delay}/{rate}/{file_name}")
        
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
                print(file)
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
                        
                        if "Kbit" in lines[-1].split()[7]:
                            heatmap_dict[delay][rate].append(float(lines[-1].split()[6])/1000)
                        else:
                            heatmap_dict[delay][rate].append(float(lines[-1].split()[6]))
                    # lines = lines[100:]
    
                    # We get lines like if we split:
                    #   0    1           2           3      4       5        6           7        8     9         10       11    12
                    # ['[', '3]', '0.0000-0.1000', 'sec', '230', 'KBytes', '18.9', 'Mbits/sec', '3/0', '5', '14K/137773', 'us', '17.13']
                    for line in lines[:-1]:
                        values = line.split()
        
                        t_cwnd = values[10].split("/")[0].strip("K")
                        if t_cwnd == 'NA':
                            continue
                        
                        # Get time; If output is a-b, is it better to get b or a? 
                        times.append(float(values[2].split("-")[1]))

                        t_bw = float(values[6])
                        if "Kbit" in values[7]:
                            t_bw = t_bw/1000
                            
                        bandwidth.append(t_bw)
                        cwnd.append(int(t_cwnd))
                        
                bw_data = pd.DataFrame({"bw": bandwidth})
                bw_rolling = bw_data.bw.rolling(20).mean()
                
                bw_ax.plot(times, bw_rolling, label=cc)
                bw_ax.set_xlabel("Time (s)")
                bw_ax.set_ylabel("Bandwidth (Mbps)")
                bw_ax.set_title(f"TCP Bandwidth rolling mean, run {key} (Base RTT: {delay} ms, Rate {rate} Mbps)")
                bw_ax.legend()
                bw_fig.savefig(f"result/dualpi2/{delay}/{rate}/bw_run_{key}.png")
                
                cwnd_ax.plot(times, cwnd, label=cc)
                cwnd_ax.set_xlabel("Time (s)")
                cwnd_ax.set_ylabel("cwnd")
                cwnd_ax.set_title(f"TCP cwnd, run {key}, (Base RTT: {delay} ms, Rate {rate} Mbps)")
                cwnd_ax.legend()
                cwnd_fig.savefig(f"result/dualpi2/{delay}/{rate}/cwnd_run_{key}.png")
                
            plt.close(bw_fig)
            plt.close(cwnd_fig)

# Print heatmap:
for delay in heatmap_dict:
    for rate in heatmap_dict[rate]:
        mean = np.mean(heatmap_dict[delay][rate]).item()
        print(f"Delay: {delay}, Bottleneck Rate: {rate}, Measured Rate: {mean}, Expected around: {rate/2}")

print("")

text_tabular = f"|c|{'c|'*len(rates)}"
text_header = " delay\\textbackslash rate & " + " & ".join(map(str,rates)) + r"\\"

text_data = "\\hline\n"
for delay in delays:
    text_data += f"{delay} " # We add & in next
    for rate in rates:
        mean = np.mean(heatmap_dict[delay][rate]).item()
        text_data += f"& {round(mean, 2)}"
    text_data += "\\\\\n" # \\\n
    text_data += "\\hline\n" 


print("\\begin{tabular}{"+text_tabular+"}")
print("\\hline")
print(text_header)
print(text_data, end="")
print("\\end{tabular}")
