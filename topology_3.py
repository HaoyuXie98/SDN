"""
A complex containing 3 routers, 5 switches, 5 subnets and 15 hosts.
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
		Your topology file for scenario 3. Define all the required devices here.
		"""
		#add switch and switch
		router1 = self.addSwitch('r1', dpid = '21')
		router2 = self.addSwitch('r2', dpid = '22')
		router3 = self.addSwitch('r3', dpid = '23')
		switch4 = self.addSwitch('s4', dpid = '14')
		switch5 = self.addSwitch('s5', dpid = '15')
		switch6 = self.addSwitch('s6', dpid = '16')
		switch7 = self.addSwitch('s7', dpid = '17')
		switch8 = self.addSwitch('s8', dpid = '18')

		#add host
		host9 = self.addHost("h9", ip = '172.17.16.2/24', defaultRoute = "via 172.17.16.1")
		host10 = self.addHost("h10", ip = '172.17.16.3/24', defaultRoute = "via 172.17.16.1")
		host11 = self.addHost("h11", ip = '172.17.16.4/24', defaultRoute = "via 172.17.16.1")

		host12 = self.addHost("h12", ip = '10.0.0.2/25', defaultRoute = "via 10.0.0.1")
		host13 = self.addHost("h13", ip = '10.0.0.3/25', defaultRoute = "via 10.0.0.1")
		host14 = self.addHost("h14", ip = '10.0.0.4/25', defaultRoute = "via 10.0.0.1")

		host15 = self.addHost("h15", ip = '10.0.0.130/25', defaultRoute = "via 10.0.0.129")
		host16 = self.addHost("h16", ip = '10.0.0.131/25', defaultRoute = "via 10.0.0.129")
		host17 = self.addHost("h17", ip = '10.0.0.132/25', defaultRoute = "via 10.0.0.129")

		host18 = self.addHost("h18", ip = '20.0.0.2/25', defaultRoute = "via 20.0.0.1")
		host19 = self.addHost("h19", ip = '20.0.0.3/25', defaultRoute = "via 20.0.0.1")
		host20 = self.addHost("h20", ip = '20.0.0.4/25', defaultRoute = "via 20.0.0.1")

		host21 = self.addHost("h21", ip = '20.0.0.130/25', defaultRoute = "via 20.0.0.129")
		host22 = self.addHost("h22", ip = '20.0.0.131/25', defaultRoute = "via 20.0.0.129")
		host23 = self.addHost("h23", ip = '20.0.0.132/25', defaultRoute = "via 20.0.0.129")

		#add link

		self.addLink(router1, switch4)
		self.addLink(router2, switch5)
		self.addLink(router2, switch6)
		self.addLink(router1, router2)
		self.addLink(router3, switch7)
		self.addLink(router3, switch8)
		self.addLink(router1, router3)

		self.addLink(host9, switch4)
		self.addLink(host10, switch4)
		self.addLink(host11, switch4)

		self.addLink(host12, switch5)
		self.addLink(host13, switch5)
		self.addLink(host14, switch5)

		self.addLink(host15, switch6)
		self.addLink(host16, switch6)
		self.addLink(host17, switch6)

		self.addLink(host18, switch7)
		self.addLink(host19, switch7)
		self.addLink(host20, switch7)

		self.addLink(host21, switch8)
		self.addLink(host22, switch8)
		self.addLink(host23, switch8)

topos = { 'mytopo':(lambda:MyTopo())}