from mininet.topo import Topo
from mininet.node import Node

class MyTopo(Topo):
    "Simple topology example."

    def __init__(self):
        "Create custom topology."

        # Initialize the topology
        Topo.__init__(self)

        # Hosts and switch
        host1 = self.addHost("h1", ip='10.0.0.2/24', defaultRoute="via 10.0.0.1")
        host2 = self.addHost("h2", ip='20.0.0.2/24', defaultRoute="via 20.0.0.1")
        host3 = self.addHost("h3", ip='30.0.0.2/24', defaultRoute="via 30.0.0.1")
        switch1 = self.addSwitch('s2', dpid='21')

        # Gateway host (assuming it's connected to the Mininet host's external network interface)
        gateway = self.addHost('gateway', ip='192.168.210.133/24', inNamespace=False)

        # Links
        self.addLink(host1, switch1)
        self.addLink(host2, switch1)
        self.addLink(host3, switch1)
        self.addLink(gateway, switch1)

topos = {'mytopo': (lambda: MyTopo())}
