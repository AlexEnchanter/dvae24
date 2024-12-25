from argparse import ArgumentParser
import matplotlib.pyplot as plt
import glob


file_name = "iperf_client*.log"

parser = ArgumentParser()
parser.add_argument("input_folder", help="input folder with iperf2 files")
args = parser.parse_args()

print(args.input_folder + '/' + file_name)

files = glob.glob(args.input_folder + '/' + file_name)
print(files)
print(files[0].rpartition(".log")[0].split("_")[3])


dictionary = {}


# [ ID] Interval            Transfer    Bandwidth       Write/Err  Rtry     Cwnd/RTT        NetPwr
# [  3] 0.0000-0.1000 sec   230 KBytes  18.9 Mbits/sec  3/0          5       14K/137773 us  17.13

# Format shoud be iperf_client_<CC>_<run>.log
for file in files:
    key = file.rpartition(".log")[0].split("_")[3]
    group = dictionary.get(key, [])
    group.append(file)
    dictionary[key] = group
    

for key in dictionary:
    plt.clf()
    for file in dictionary[key]:
        times = []
        bandwidth = []
        cwnd = []

        print("file:", file)
        cc = file.rpartition(".log")[0].split("_")[2]
        with open(file) as f:
            lines = f.readlines()
     
            # Read lines until iperf header
            while "ID" not in lines[0]:
                lines = lines[1:]
            lines = lines[1:]

            # Remove Last line, as that is a summary
            lines = lines[0:-1]

            # lines = lines[100:]
    
            # We get lines like if we split:
            #   0    1           2           3      4       5        6           7        8     9         10       11    12
            # ['[', '3]', '0.0000-0.1000', 'sec', '230', 'KBytes', '18.9', 'Mbits/sec', '3/0', '5', '14K/137773', 'us', '17.13']
            for line in lines:
                values = line.split()
        
                # Get time; If output is a-b, is it better to get b or a? 
                times.append(float(values[2].split("-")[1]))

                bandwidth.append(float(values[6]))
    
                cwnd.append(int(values[10].split("/")[0].strip("K")))
                
        plt.plot(times, bandwidth, label=cc)
        plt.xlabel("Time (s)")
        plt.ylabel("Bandwidth (Mbps)")
        plt.title(f"TCP Bandwidth 2 flows run {key}")
        plt.legend()
        plt.savefig(f"{args.input_folder}/{key}.png")
