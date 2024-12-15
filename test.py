#!/usr/bin/python

from mininet.topo import Topo
from mininet.net import Mininet
from mininet.node import CPULimitedHost
from mininet.link import TCLink
from mininet.util import dumpNodeConnections
from mininet.log import setLogLevel
import time

class SingleSwitchTopo( Topo ):
    "Single switch connected to n hosts."
    def build( self, n=2 ):
    	switch = self.addSwitch('s1')
    	for h in range(n):
    	    # Each host gets 50%/n of system CPU
    	    host = self.addHost( 'h%s' % (h + 1),
    		                 cpu=.5/n )
    	    # 10 Mbps, 5ms delay,  1000 packet queue
    	    self.addLink( host, switch, bw=10, delay='5ms', max_queue_size=1000, use_htb=True )

def perfTest():
    "Create network and run simple performance test"
    topo = SingleSwitchTopo( n=4 )
    net = Mininet( topo=topo,
	           host=CPULimitedHost, link=TCLink )
    net.start()
    print( "Dumping host connections" )
    dumpNodeConnections( net.hosts )
    print( "Testing network connectivity" )
    net.pingAll()
    print( "Testing bandwidth between h1 and h4" )

    
    h1, h4 = net.get( 'h1', 'h4' )
    print("running iperf for 60s")
    h4.cmd("iperf -s -e > iperf_server.log &")
    time.sleep(1)
    h1.cmd(f"iperf -Z prague -c {h4.IP()} -t 60 -i 0.1 -e > iperf_client.log")
    
    # h1.cmd("killall tcpdump")
    h1.cmd("killall iperf")
    
    h4.cmd("killall iperf")
    
    
    net.stop()

if __name__ == '__main__':
    setLogLevel( 'info' )
    perfTest()
