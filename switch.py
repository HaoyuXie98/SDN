"""
[555 Comments]
Your switch code and any other helper functions related to switch should be written in this file
"""
from pox.core import core
import pox.openflow.libopenflow_01 as of
from pox.lib.packet.arp import arp
from pox.lib.packet.ethernet import *
from pox.lib.addresses import *
from pox.lib.packet.icmp import *
from pox.lib.packet.ipv4 import *
from pox.lib.util import dpid_to_str

log = core.getLogger()

"""
[555 Comments]
  Function : switch_handler
  Input Parameters:
      sw_object : The switch object. This will be initialized in the controller file corresponding to the scenario in __init__
                  function of tutorial class. Any data structures you would like to use for a switch should be initialized
                  in the contoller file corresponding to the scenario.
      packet    : The packet that is received from the packet forwarding switch.
      packet_in : The packet_in object that is received from the packet forwarding switch
"""
class mySwitch:
  def __init__ (self, dpid):
    self.DPID = dpid
    self.ipToPort = {}
    self.macToPort ={}

def generate_icmp_reply(sw_object, packet, icmp_type, packet_in):
  p_icmp = icmp()
  p_icmp.type = icmp_type

  if icmp_type == TYPE_ECHO_REPLY:
    p_icmp.payload = packet.next.next.payload

  elif icmp_type == TYPE_DEST_UNREACH:
    ip = packet.find('ipv4')
    dest_unreach = ip.pack()
    dest_unreach = dest_unreach[:ip.hl * 4 + 8] # add 'destination unreachable" icmp code
    dest_unreach = struct.pack("!HH", 0, 0) + dest_unreach
    p_icmp.payload = dest_unreach

  ip_packet = ipv4()
  ip_packet.protocol = ip_packet.ICMP_PROTOCOL
  ip_packet.srcip = packet.next.dstip  
  ip_packet.dstip = packet.next.srcip

  eth_packet = ethernet()

  eth_packet.dst = packet.src
  eth_packet.type = eth_packet.IP_TYPE
 
  ip_packet.payload = p_icmp
  eth_packet.payload = ip_packet
 
  msg = of.ofp_packet_out()
  msg.actions.append(of.ofp_action_output(port = packet_in.in_port))
  msg.data = eth_packet.pack()
  #msg.in_port = rt_object.mainRouter.ip_to_port[str(packet.next.srcip)]
  core.openflow.sendToDPID(sw_object.mainSwitch.DPID, msg)

def check_imcp(sw_object, srcip, dstip):
  #print(srcip + " " + dstip)
  if len(sw_object.firewall_rule) == 0:
    return True
  for icmp_allow in sw_object.firewall_rule["ICMP_allow"]:
    for src in icmp_allow:
      if (src == srcip and icmp_allow[src] == dstip) or (src == dstip and icmp_allow[src] == srcip):
        return True
  for dst in sw_object.firewall_rule["ICMP_ban"]:
    if dst == dstip or dst == srcip:
      return False
  return True

def check_tcp(sw_object, srcip, dstip):
  if len(sw_object.firewall_rule) == 0:
    return True
  for tcp_allow in sw_object.firewall_rule["TCP_allow"]:
    for src in tcp_allow:
      if (src == srcip and tcp_allow[src] == dstip) or (src == dstip and tcp_allow[src] == srcip):
        return True
  for dst in sw_object.firewall_rule["TCP_ban"]:
    if dst == dstip or dst == srcip:
      return False
  return True

def switch_handler(sw_object, packet, packet_in):
  if isinstance(packet.next.next, icmp):
    if check_imcp(sw_object, str(packet.next.srcip), str(packet.next.dstip)) == False:
      generate_icmp_reply(sw_object, packet, TYPE_DEST_UNREACH, packet_in)
      return
    
  if isinstance(packet.next.next, tcp):
    if check_tcp(sw_object, str(packet.next.srcip), str(packet.next.dstip)) == False:
      generate_icmp_reply(sw_object, packet, TYPE_DEST_UNREACH, packet_in)
      return
  # format MACs
  src_mac = packet.src
  dst_mac = packet.dst
  # print(sw_object.mainSwitch.DPID)
  # print(packet.src)
  # print(packet.dst)
  # print(packet_in.in_port)
  # print(sw_object.mainSwitch.macToPort)
  # learn mac to port mapping
  if src_mac not in sw_object.mainSwitch.macToPort:
    sw_object.mainSwitch.macToPort[src_mac] = packet_in.in_port
    #print(sw_object.mainSwitch.macToPort)

  # if the port associated with the destination MAC of the packet is known:
  if dst_mac in sw_object.mainSwitch.macToPort:
    # Send packet out the associated port
    sw_object.resend_packet(packet_in, sw_object.mainSwitch.macToPort[dst_mac])
    # flow mod
    msg = of.ofp_flow_mod()
    msg.match = of.ofp_match.from_packet(packet)
    msg.match = of.ofp_match(dl_src = src_mac, dl_dst = dst_mac)
    #msg.match = of.ofp_match(dl_dst = dst_mac)
    msg.idle_timeout = 3600
    msg.hard_timeout = 7200
    msg.priority = 0x8000 # A0
    msg.actions.append(of.ofp_action_output(port = sw_object.mainSwitch.macToPort[dst_mac]))
    if not isinstance(packet.next, arp):
      core.openflow.sendToDPID(sw_object.mainSwitch.DPID, msg)
  else:
    # broadcase packet out of all ports except in_port
    sw_object.resend_packet(packet_in, of.OFPP_ALL)