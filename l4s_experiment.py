
#!/usr/bin/python

import os
import time
import subprocess

from mininet.topo import Topo
from mininet.net import Mininet
from mininet.node import CPULimitedHost
from mininet.link import TCLink
from mininet.util import dumpNetConnections
from mininet.log import setLogLevel, info
from mininet.cli import CLI


def assert_cc(node, CC, net):
    res = node.cmd("sysctl net.ipv4.tcp_congestion_control")
    if CC in res:
        return True
    print(f"ERR: CCA {CC} did not correctly apply to node: {node}")
    net.stop()
    exit()


def assert_tcp_Prague():
    res = subprocess.run(["sysctl", "net.ipv4.tcp_available_congestion_control"], capture_output=True, text=True)
    if "prague" in res.stdout:
        return True
    print("Prague not avalable")
    return False

def load_modules():
    res = subprocess.run(["modprobe", "sch_dualpi2"], capture_output=True, text=True)
    if "FATAL" in res.stdout:
        print(f"Dualpi2 not avalable: {res.stdout}")
        return False
    return True
    
    res = subprocess.run(["modprobe", "tcp_prague"], capture_output=True, text=True)
    if "FATAL" in res.stdout:
        print(f"Prague not avalable: {res.stdout}")
        return False
    return True


# ecn = 0|1|2|3; https://github.com/L4STeam/linux?tab=readme-ov-file#accurate-ecn-negotiation 
# run = run id.
def test(data_rate=100, RTT=20, competing_CC="cubic", ecn=1, aqm="dualpi2", ecn_fallback=0, run=1, out_folder="result"):
    if not assert_tcp_Prague:
        exit(1)
    if not load_modules():
        exit(1)
        
    if not os.path.exists(out_folder):
        os.makedirs(out_folder)
    
    BDP = int((RTT * 10**-3) * (data_rate * 10**6))
    BDP_B = int(BDP//8)
    print(f"Run {run}, RTT: {RTT}ms, data rate: {data_rate}Mbps, BDP: {BDP} bits, BDP: {BDP_B} Bytes, Competing CC: {competing_CC}, result folder: {out_folder}")
    net = Mininet(waitConnected=True, link=TCLink, autoStaticArp=True)

    net.addController("c0")

    # Sender
    l4s_s = net.addHost("l4s_s")
    classic_s = net.addHost("classic_s")
    
    # Reciver
    l4s_r = net.addHost("l4s_r")
    classic_r = net.addHost("classic_r")

    s1 = net.addSwitch("s1")
    s2 = net.addSwitch("s2")
    s3 = net.addSwitch("s3")

    l4s_s_eth0 = "l4s_s-eth0"
    l4s_r_eth0 = "l4s_r-eth0"
    classic_s_eth0 = "classic_s-eth0"
    classic_r_eth0 = "classic_r-eth0"
    
    net.addLink(l4s_s, s1, intfName1=l4s_s_eth0)
    net.addLink(classic_s, s1, intfName1=classic_s_eth0)
    
    net.addLink(s1, s2)
    net.addLink(s2, s3)

    net.addLink(l4s_r, s3, intfName1=l4s_r_eth0)
    net.addLink(classic_r, s3, intfName1=classic_r_eth0)

    net.start()

    dumpNetConnections(net)

    # TODO: Assert 
    print("*** Setting fq at end nodes")
    l4s_s.cmd(f"ethtool -K {l4s_s_eth0} tso off gso off gro off lro off")
    l4s_s.cmd(f"tc qdisc replace dev {l4s_s_eth0} root handle 1: fq limit 20480 flow_limit 10240")
    
    l4s_r.cmd(f"ethtool -K {l4s_r_eth0} tso off gso off gro off lro off")
    l4s_r.cmd(f"tc qdisc replace dev {l4s_r_eth0} root handle 1: fq limit 20480 flow_limit 10240")
    
    
    # Do I need to set ecn_fallback on receiver too?
    l4s_s.cmd(f"echo {ecn_fallback} > /sys/module/tcp_prague/parameters/prague_ecn_fallback")
    
    # Set prague on l4s sender and receiver 
    l4s_s.cmd(f"sysctl -w net.ipv4.tcp_congestion_control=prague")
    l4s_r.cmd(f"sysctl -w net.ipv4.tcp_congestion_control=prague")

    # Set classic CCA
    classic_s.cmd(f"sysctl -w net.ipv4.tcp_congestion_control={competing_CC}")
    classic_r.cmd(f"sysctl -w net.ipv4.tcp_congestion_control={competing_CC}")
    
    # Set classic ecn mode
    # !!! Not sure if this works... Initial testing this seems to have no effect
    # Could be I forgot to set flow_limit on fifo+ecn, so no packets got marked
    classic_s.cmd(f"sysctl -w net.ipv4.tcp_ecn={ecn}")
    classic_r.cmd(f"sysctl -w net.ipv4.tcp_ecn={ecn}")
    

    # Assert CC
    assert_cc(l4s_s, "prague", net)
    assert_cc(l4s_r, "prague", net)
    assert_cc(classic_s, competing_CC, net)
    assert_cc(classic_r, competing_CC, net)
    

    print("*** adding delay on s1")
    for intf in s1.intfList():
        if "lo" in intf.name:
            continue
        print(f"interface {intf}")
        s1.cmd(f"tc qdisc replace dev {intf} root netem delay {RTT//2}ms limit {4*BDP_B}")
    


    # TODO: assert 
    print("*** replacing qdisc on s2")
    for srcIntf, _ in s2.connectionsTo(s3):
        # Might want to increase limit on tbf, as not to make that a bottleneck
        s2.cmd(f"tc qdisc replace dev {srcIntf} root handle 1: tbf rate {data_rate}mbit burst 10000 limit {2*BDP_B}")
        
        if aqm == "dualpi2":
            s2.cmd(f"tc qdisc add dev {srcIntf} parent 1: dualpi2")
        elif aqm == "FIFO+ECN":
            s2.cmd(f"tc qdisc add dev {srcIntf} parent 1: fq limit {2*BDP_B} flow_limit {2*BDP_B} orphan_mask 0 ce_threshold 5ms") # 5ms is the default for CoDel (target)
        elif aqm == "FIFO":
            s2.cmd(f"tc qdisc add dev {srcIntf} parent 1: bfifo limit {2*BDP_B}")
        elif aqm == "CoDel":
            s2.cmd(f"tc qdisc add dev {srcIntf} parent 1: codel ecn limit {2*BDP_B}")
        else:
            print(f"Could not find aqm {aqm}")
            net.stop()
            exit()
        
    s2.cmd("tc qdisc")        

    time.sleep(1)
    
    # Send Prague h1 -> h2
    print("running iperf for 60s")
    l4s_r.cmd("iperf -s -e -P 1 &")
    classic_r.cmd("iperf -s -e -P 1 &")
    
    time.sleep(1)
    
    l4s_s.cmd(f"iperf -c {l4s_r.IP()} -t 60 -i 0.1 -e > {out_folder}/iperf_client_prague_{run}.log &")
    classic_s.cmd(f"iperf -c {classic_r.IP()} -t 60 -i 0.1 -e > {out_folder}/iperf_client_{competing_CC}_{run}.log &")
    
    
    l4s_r.cmd("wait")
    classic_r.cmd("wait")
    
    l4s_s.cmd("killall iperf")
    classic_s.cmd("killall iperf")
    
    l4s_r.cmd("killall iperf")
    classic_r.cmd("killall iperf")
    
    net.stop()

if __name__ == "__main__":
    setLogLevel("info")
    test()
