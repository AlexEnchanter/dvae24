#!/usr/bin/python

import time

from mininet.topo import Topo
from mininet.net import Mininet
from mininet.node import CPULimitedHost
from mininet.link import TCLink
from mininet.util import dumpNodeConnections
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
    net.addLink(h1, s1, bw=100, delay="10ms")
    net.addLink(h2, s1)

    net.start()

    dumpNodeConnections(net.hosts)


    # TODO: Assert 
    print("*** Setting fq at end nodes")
    h1.cmd(f"ethtool -K h1-eth0 tso off gso off gro off lro off")
    h1.cmd("tc qdisc replace dev h1-eth0 root handle 1: fq limit 20480 flow_limit 10240")
    h2.cmd(f"ethtool -K h2-eth0 tso off gso off gro off lro off")
    h2.cmd("tc qdisc replace dev h2-eth0 root handle 1: fq limit 20480 flow_limit 10240")
    
    # Maybe does what I think it does, ASSERT dualpi2 later
    print("*** replacing qdisc on s1")
    for intf in s1.intfList():
        if "lo" in intf.name:
            continue
        print(f"interface {intf}")
        s1.cmd(f"tc qdisc replace dev {intf} root dualpi2")

    a = assert_tcp_Prague_Avalable(h1)
    if a == False:
        net.stop()        
        return
    time.sleep(1)
    
    # Send Prague h1 -> h2
    print("running iperf for 60s")
    h2.cmd("iperf -s -e > iperf_server.log &")
    time.sleep(1)
    h1.cmd(f"iperf -Z prague -c {h2.IP()} -t 60 -i 0.1 -e > iperf_client.log")
    
    h1.cmd("killall iperf")
    h2.cmd("killall iperf")
    
    net.stop()

if __name__ == "__main__":
    setLogLevel("info")
    test()
