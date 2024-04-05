# Copyright 2012 James McCauley
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at:
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
[555 Comments]
This is the controller file corresponding to scenario 3.
"""

from pox.core import core
import pox.openflow.libopenflow_01 as of
from pox.lib.packet.arp import arp
from pox.lib.packet.ethernet import *
from pox.lib.addresses import *
from pox.lib.packet.icmp import *
from pox.lib.packet.ipv4 import *
from switch import *
from router import *
from pox.lib.util import dpid_to_str

log = core.getLogger()

class Tutorial (object):
  """
  A Tutorial object is created for each switch that connects.
  A Connection object for that switch is passed to the __init__ function.
  """
  routing_table = {}
  allRouter = {}
  allSwitch = {}

  def __init__ (self, connection):
    # Keep track of the connection to the switch so that we can
    # send it messages!
    self.connection = connection

    # This binds our PacketIn event listener
    connection.addListeners(self)
    self.routing_table_r1 = { "172.17.16.0":  {"prefix": 24, "port": 1, "mac_interface": "02:00:DE:AD:BE:11", "router_interface": "172.17.16.1", "next_hop": "0.0.0.0"},
                              "10.0.0.0":     {"prefix": 24, "port": 2, "mac_interface": "02:00:DE:AD:BE:12", "router_interface": "192.168.0.1", "next_hop": "192.168.0.2"},
                              "20.0.0.0":     {"prefix": 24, "port": 3, "mac_interface": "02:00:DE:AD:BE:13", "router_interface": "192.168.0.5", "next_hop": "192.168.0.6"}}

    self.routing_table_r2 = { "172.17.16.0":  {"prefix": 24, "port": 3, "mac_interface": "02:00:DE:AD:BE:23", "router_interface": "192.168.0.2", "next_hop": "192.168.0.1"},
                              "0.0.0.0":      {"prefix": 0,  "port": 3, "mac_interface": "02:00:DE:AD:BE:23", "router_interface": "192.168.0.2", "next_hop": "192.168.0.1"},
                              "10.0.0.0":     {"prefix": 25, "port": 1, "mac_interface": "02:00:DE:AD:BE:21", "router_interface": "10.0.0.1",    "next_hop": "0.0.0.0"},
                              "10.0.0.128":   {"prefix": 25, "port": 2, "mac_interface": "02:00:DE:AD:BE:22", "router_interface": "10.0.0.129",  "next_hop": "0.0.0.0"}}

    self.routing_table_r3 = { "172.17.16.0":  {"prefix": 24, "port": 3, "mac_interface": "02:00:DE:AD:BE:33", "router_interface": "192.168.0.6", "next_hop": "192.168.0.5"},
                              "10.0.0.0":     {"prefix": 24, "port": 3, "mac_interface": "02:00:DE:AD:BE:33", "router_interface": "192.168.0.6", "next_hop": "192.168.0.5"},
                              "20.0.0.0":     {"prefix": 25, "port": 1, "mac_interface": "02:00:DE:AD:BE:31", "router_interface": "20.0.0.1",    "next_hop": "0.0.0.0"},
                              "20.0.0.128":   {"prefix": 25, "port": 2, "mac_interface": "02:00:DE:AD:BE:32", "router_interface": "20.0.0.129",  "next_hop": "0.0.0.0"}}

    self.firewall_rule = {"ICMP_ban": ["10.0.0.2", "10.0.0.132"],
                          "ICMP_allow": [{"172.17.16.2" : "10.0.0.132"}, {"172.17.16.3" : "10.0.0.132"},{"172.17.16.4" : "10.0.0.132"}],
                          "TCP_ban" : ["10.0.0.2", "10.0.0.132"],
                          "TCP_allow": [{"20.0.0.2": "10.0.0.132"}]                          
                         }
    if dpid_to_str(connection.dpid)[-2] == '2':
      if connection.dpid not in self.allRouter:
          # mainSwitch = mySwitch(dpid_to_str(connection.dpid))
          # self.allSwitch[dpid_to_str(connection.dpid)] = mainSwitch
          mainRouter = myRouter(connection.dpid)
          self.allRouter[connection.dpid] = mainRouter
          if dpid_to_str(connection.dpid)[-1] == '1':
            self.routing_table[connection.dpid] = self.routing_table_r1
          elif dpid_to_str(connection.dpid)[-1] == '2':
            self.routing_table[connection.dpid] = self.routing_table_r2
          elif dpid_to_str(connection.dpid)[-1] == '3':
            self.routing_table[connection.dpid] = self.routing_table_r3
    else:
      if connection.dpid not in self.allSwitch:
          # mainSwitch = mySwitch(dpid_to_str(connection.dpid))
          # self.allSwitch[dpid_to_str(connection.dpid)] = mainSwitch
          mainSwitch = mySwitch(connection.dpid)
          self.allSwitch[connection.dpid] = mainSwitch
    # print(self.allRouter)
    # print(self.allSwitch)
    # print(self.routing_table)  

    
    """
    [555 Comments]
    In scenario 3, there are many routers and switches. You need to classify a device as a router or a switch based on its DPID
    Remember one thing very carefully. The DPID gets assigned based on how you define tour devices in the topology file.
    So, be careful and DPID here should be coordinated with your definition in topology file.
    For the details of port info table, routing table, of different routers look into the project description document provided.
    Initialize any other data structures you wish to for the routers and switches here

    A word of caution:
    Your router and switch code should be the same for all scenarios. So, be careful to design your data structures for router
    and switches in such a way that your single piece of switch code and router code along with your data structure design
    should work for all the scenarios
    """

  def resend_packet (self, packet_in, out_port):
    """
    Instructs the switch to resend a packet that it had sent to us.
    "packet_in" is the ofp_packet_in object the switch had sent to the
    controller due to a table-miss.
    """
    msg = of.ofp_packet_out()
    msg.data = packet_in

    # Add an action to send to the specified port
    action = of.ofp_action_output(port = out_port)
    msg.actions.append(action)

    # Send message to switch
    self.connection.send(msg)
    
  def _handle_PacketIn (self, event):
    """
    Handles packet in messages from the switch.
    """
    packet = event.parsed # This is the parsed packet data.
    if not packet.parsed:
      log.warning("Ignoring incomplete packet")
      return

    packet_in = event.ofp # The actual ofp_packet_in message.

    """
    [555 Comments]
    You need to classify a device as either switch or router based on its DPID received in the connection object during
    initialization in __init__ function in tutorial class. Based on the device type you need to call the respective function
    Here is the pseudo code to write

    if packet received from device type is switch:
      invoke switch_handler and pass the object (i.e., self) and the packet and packet_in
    else: (if it is not switch, it means router. We have only two kinds of devices, one is switch and one is router)
      invoke router_handler and pass the object (i.e., self) and the packet and packet_in
    """
    #print(event.connection.dpid)
    if dpid_to_str(event.connection.dpid)[-2] == '2':
      self.mainRouter = self.allRouter[event.connection.dpid]
      router_handler(self, packet, packet_in)
      #print("router")
    elif dpid_to_str(event.connection.dpid)[-2] == '1':
      self.mainSwitch = self.allSwitch[event.connection.dpid]
      switch_handler(self, packet, packet_in)
      #print(event.connection.dpid)

def launch ():
  """
  Starts the component
  """
  def start_switch (event):
    #log.debug("Controlling %s" % (event.connection,))
    Tutorial(event.connection)
  core.openflow.addListenerByName("ConnectionUp", start_switch)