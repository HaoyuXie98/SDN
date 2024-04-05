"""
Three devices on same network and all connected by a switch

	host --- switch ---- host
		   		|
		   		|
		   		|
		  	   host

"""

from mininet.topo import Topo

class MyTopo(Topo):
    "Simple topology example."

    def __init__(self):
	"Create custom topology."

	#Initialize the topology
	Topo.__init__(self)
	
	"""
	[555 Comments]
	Your topology file for scenario 1. Define all the required devices here.
	"""
	host1 = self.addHost("h1", ip = '10.0.0.2/24', defaultRoute = "via 10.0.0.1")
	host2 = self.addHost("h2", ip = '10.0.0.3/24', defaultRoute = "via 10.0.0.1")
	host3 = self.addHost("h3", ip = '10.0.0.4/24', defaultRoute = "via 10.0.0.1")
	#switch start with 1 router start with 2
	switch1 = self.addSwitch('s1', dpid = '11')
	#switch2 = self.addSwitch('Switch2', device = 'switch')
	self.addLink(host1, switch1)
	self.addLink(host2, switch1)
	self.addLink(host3, switch1)

topos = { 'mytopo':(lambda:MyTopo())}