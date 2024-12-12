import matplotlib.pyplot as plt

# BTW iperf csv is useless
file = "iperf_client.log"

times = []
cwnd = []

# TODO: Maybe add plot title/name in the first line of data file (or other useful data)

with open(file) as f:
    lines = f.readlines()

    # [ ID] Interval            Transfer    Bandwidth       Write/Err  Rtry     Cwnd/RTT        NetPwr
    # [  3] 0.0000-0.1000 sec   230 KBytes  18.9 Mbits/sec  3/0          5       14K/137773 us  17.13
     
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

        # get cwnd
        cwnd.append(int(values[10].split("/")[0].strip("K")))
    
plt.plot(times, cwnd)
plt.xlabel("Time (s)")
plt.ylabel("cwnd (KBytes)")
plt.title("TCP Prague")
plt.savefig("cwnd_plot.png")
