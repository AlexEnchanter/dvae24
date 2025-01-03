from argparse import ArgumentParser
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import heatmap as hm

import glob
import os

dirs = ["ECN1", "noECN", "ECN_fallback"]
aqms = ["CoDel", "dualpi2", "fifo", "fifoWithEcn"]

file_name = "iperf_client*.log"

# parser = ArgumentParser()
# parser.add_argument("input_folder", help="input folder with iperf2 files")
# args = parser.parse_args()

# print(args.input_folder + '/' + file_name)

# print(files)
# print(files[0].rpartition(".log")[0].split("_")[3])


heatmap_dict = {}

# This feels stupid :/
for ecn in dirs:
    heatmap_dict[ecn] = {}

for ecn in dirs:
    for aqm in aqms:
        heatmap_dict[ecn][aqm] = []
        
# [ ID] Interval            Transfer    Bandwidth       Write/Err  Rtry     Cwnd/RTT        NetPwr
# [  3] 0.0000-0.1000 sec   230 KBytes  18.9 Mbits/sec  3/0          5       14K/137773 us  17.13

print("This will take some time...")
for dir in dirs:
    for aqm in aqms:
        print(f"{dir}+{aqm}")
        files = glob.glob(f"result/{dir}/{aqm}/{file_name}")
        
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
                        heatmap_dict[dir][aqm].append(float(lines[-1].split()[6]))
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
                bw_ax.set_title(f"TCP Bandwidth rolling mean, 2 flows run {key}")
                bw_ax.legend()
                bw_fig.savefig(f"result/{dir}/{aqm}/bw_run_{key}.png")
                
                cwnd_ax.plot(times, cwnd, label=cc)
                cwnd_ax.set_xlabel("Time (s)")
                cwnd_ax.set_ylabel("cwnd")
                cwnd_ax.set_title(f"TCP cwnd 2 flows run {key}")
                cwnd_ax.legend()
                cwnd_fig.savefig(f"result/{dir}/{aqm}/cwnd_run_{key}.png")
                
            plt.close(bw_fig)
            plt.close(cwnd_fig)

# Print heatmap:
aqm_heatmap = ["FIFO", "FIFO+ECN", "CoDel+ECN", "DualPI2"]
ecn_heatmap = ["ECN", "No ECN", "ECN Fallback"]

# dirs = ["ECN1", "noECN", "ECN_fallback"]
# aqms = ["CoDel", "dualpi2", "fifo", "fifoWithEcn"]

# [ECN][aqm]
#        FIFO, FIFO+ECN, CoDel, DualPI2
# no ECN, 
# ECN 
# ECN Fallback
heatmap_array = [[0 for i in range(4)] for i in range(3)]

name_to_index = {"noECN": 0, "ECN1": 1, "ECN_fallback": 2, "fifo": 0, "fifoWithEcn": 1, "CoDel": 2, "dualpi2": 3}

print(heatmap_dict)

for ecn in heatmap_dict:
    for aqm in heatmap_dict[ecn]:
        heatmap_dict[ecn][aqm] = np.mean(heatmap_dict[ecn][aqm])
        heatmap_array[name_to_index[ecn]][name_to_index[aqm]] = heatmap_dict[ecn][aqm].item()


for key in heatmap_dict:
    print(key,  heatmap_dict[key])
for a in heatmap_array:
    print(a)
        
fig, ax = plt.subplots()

im, cbar = hm.heatmap(np.array(heatmap_array), ecn_heatmap, aqm_heatmap, ax=ax, cmap="coolwarm", cbarlabel="Throughput [Mbps]")
texts = hm.annotate_heatmap(im, valfmt="{x:.1f}")

fig.tight_layout()
fig.savefig("result/heatmap.png")
plt.close(fig)
