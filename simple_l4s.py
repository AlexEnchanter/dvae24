#!/usr/bin/python

import time

from mininet.topo import Topo
from mininet.net import Mininet
from mininet.node import CPULimitedHost
from mininet.link import TCLink
from mininet.util import dumpNetConnections
from mininet.log import setLogLevel, info
from mininet.cli import CLI

def assert_tcp_Prague_Avalable(node):
    res = node.cmd("sysctl net.ipv4.tcp_available_congestion_control")
    if "prague" in res:
        return True
    print("Prague not avalable")
    return False

def test():
    net = Mininet(waitConnected=True, link=TCLink, autoStaticArp=True)

    net.addController("c0")

    h1 = net.addHost("h1", ip="10.0.0.1")
    h2 = net.addHost("h2", ip="10.0.0.2")

    s1 = net.addSwitch("s1")
    s2 = net.addSwitch("s2")
    
    net.addLink(h1, s1)
    net.addLink(s1, s2)
    net.addLink(s2, h2)

    net.start()

    dumpNetConnections(net)


    # TODO: Assert 
    print("*** Setting fq at end nodes")
    h1.cmd(f"ethtool -K h1-eth0 tso off gso off gro off lro off")
    h1.cmd("tc qdisc replace dev h1-eth0 root handle 1: fq limit 20480 flow_limit 10240")
    print(h1.cmd("tc qdisc"))
    
    h2.cmd(f"ethtool -K h2-eth0 tso off gso off gro off lro off")
    h2.cmd("tc qdisc replace dev h2-eth0 root handle 1: fq limit 20480 flow_limit 10240")
    h2.cmd("tc qdisc")
    

    # Set congestion controll to use on h2
    h2.cmd("sysctl -w net.ipv4.tcp_congestion_control=prague")
    print(h2.cmd("sysctl net.ipv4.tcp_congestion_control"))

    print("*** adding delay on s1")
    for intf in s1.intfList():
        if "lo" in intf.name:
            continue
        print(f"interface {intf}")
        # Total of 40ms; limit IDK Just copied value from "To switch or not to switch"
        s1.cmd(f"tc qdisc replace dev {intf} root netem delay 20ms limit 60000")
    s1.cmd("tc qdisc")
    
    # Maybe does what I think it does, ASSERT dualpi2 later
    print("*** replacing qdisc on s2")
    for intf in s2.intfList():
        if "lo" in intf.name:
            continue
        print(f"interface {intf}")
        # Burst/limit idk what to set here.
        s2.cmd(f"tc qdisc replace dev {intf} root handle 1: tbf rate 100mbit burst 2048 limit 60000 ")
        
        # s2.cmd(f"tc qdisc add dev {intf} parent 1: bfifo limit 500000")
        s2.cmd(f"tc qdisc add dev {intf} parent 1: dualpi2")
    s2.cmd("tc qdisc")
        

    a = assert_tcp_Prague_Avalable(h1)
    if a == False:
        net.stop()        
        return


    # h1.cmd("tcpdump -w capture_h1_prague.pcap &")
    # h2.cmd("tcpdump -w capture_h2_prague.pcap &")
    
    time.sleep(1)
    
    # Send Prague h1 -> h2
    print("running iperf for 60s")
    h2.cmd("iperf -s -e > iperf_server.log &")
    time.sleep(1)
    h1.cmd(f"iperf -Z prague -c {h2.IP()} -t 60 -i 0.1 -e > iperf_client.log")
    # h1.cmd(f"iperf -Z cubic -c {h2.IP()} -t 60 -i 0.1 -e > iperf_client.log")
    
    h1.cmd("killall iperf")
    # h1.cmd("killall tcpdump")
    
    h2.cmd("killall iperf")
    # h2.cmd("killall tcpdump")
    
    net.stop()

if __name__ == "__main__":
    setLogLevel("info")
    test()
