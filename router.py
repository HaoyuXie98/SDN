"""
[555 Comments]
Your router code and any other helper functions related to router should be written in this file
"""
from pox.core import core
import pox.openflow.libopenflow_01 as of
from pox.lib.packet.arp import arp
from pox.lib.packet.ethernet import *
from pox.lib.addresses import *
from pox.lib.packet.icmp import *
from pox.lib.packet.ipv4 import *
import math
log = core.getLogger()

"""
[555 Comments]
  Function : router_handler
  Input Parameters:
      rt_object : The router object. This will be initialized in the controller file corresponding to the scenario in __init__
                  function of tutorial class. Any data structures you would like to use for a router should be initialized
                  in the contoller file corresponding to the scenario.
      packet    : The packet that is received from the packet forwarding switch.
      packet_in : The packet_in object that is received from the packet forwarding switch
"""
class myRouter:
    def __init__ (self, dpid):
      self.DPID = dpid
      self.ip_to_port = {}
      self.mac_to_port = {}
      self.ip_to_mac = {}
      self.buffer ={}

def LPM(mask, ip):
    x=0
    ip_bin=0
    while x <= 3:
        temp = ip.split(".")[x]
        temp_int= int(temp)<<(24-x*8)
        ip_bin=temp_int+ip_bin
        x=x+1
    temp_dec= math.pow(2,int(mask))
    temp_dec = int(temp_dec-1)
    temp_bin = temp_dec<<(32-int(mask))
    result_bin = temp_bin & ip_bin
    first = result_bin>>24
    second = result_bin & 16711680
    second = second>>16
    third = result_bin & 65280
    third = third>>8
    fourth = result_bin & 255
    key = str(first)+"."+str(second)+"."+str(third)+"."+str(fourth)
    return key

def get_subnet(rt_object, ip):
  mask = 32
  match = ""
  while match not in rt_object.routing_table[rt_object.mainRouter.DPID] and mask > 0:
    match = LPM(mask, str(ip))
    mask -= 1
  return match

def same_subnet(rt_object, ip1, ip2):
  return (get_subnet(rt_object, ip1) == get_subnet(rt_object, ip2))

def is_interface(rt_object, dstip):
  for subnet in rt_object.routing_table[rt_object.mainRouter.DPID]:
    if(dstip == rt_object.routing_table[rt_object.mainRouter.DPID][subnet]["router_interface"]):
      return True
  return False

def validate_ip(rt_object, ip):
  ip_sub = get_subnet(rt_object, ip)
  for subnet in rt_object.routing_table[rt_object.mainRouter.DPID]:
    if ip_sub == subnet:
      return True
  return False

def check_imcp(rt_object, srcip, dstip):
  #print(srcip + " " + dstip)
  if len(rt_object.firewall_rule) == 0:
    return True
  for icmp_allow in rt_object.firewall_rule["ICMP_allow"]:
    for src in icmp_allow:
      if (src == srcip and icmp_allow[src] == dstip) or (src == dstip and icmp_allow[src] == srcip):
        return True
  for dst in rt_object.firewall_rule["ICMP_ban"]:
    if dst == dstip or dst == srcip:
      return False
  return True

def check_tcp(rt_object, srcip, dstip):
  if len(rt_object.firewall_rule) == 0:
    return True
  for tcp_allow in rt_object.firewall_rule["TCP_allow"]:
    for src in tcp_allow:
      if (src == srcip and tcp_allow[src] == dstip) or (src == dstip and tcp_allow[src] == srcip):
        return True
  for dst in rt_object.firewall_rule["TCP_ban"]:
    if dst == dstip or dst == srcip:
      return False
  return True

def get_subnet_from_interface_ip(rt_object, interface_ip):
  # for subnet, table in rt_object.routing_table[rt_object.mainRouter.DPID].iteritems():
  for subnet, table in rt_object.routing_table[rt_object.mainRouter.DPID].items():
    if(table["router_interface"] == interface_ip):
      return subnet
  return interface_ip

########################################## ARP functions ##########################################
def generate_arp_request(rt_object, endpoint_ip, destination_ip, packet, packet_in):
  arp_req = arp()
  arp_req.hwtype = arp_req.HW_TYPE_ETHERNET
  arp_req.prototype = arp_req.PROTO_TYPE_IP
  arp_req.hwlen = 6
  arp_req.protolen = arp_req.protolen
  arp_req.opcode = arp_req.REQUEST
  arp_req.hwdst = ETHER_BROADCAST
  arp_req.protodst = IPAddr(destination_ip)
  arp_req.hwsrc =  EthAddr(rt_object.routing_table[rt_object.mainRouter.DPID][get_subnet(rt_object, packet.next.dstip)]["mac_interface"])
  # make source the interface for this route
  arp_req.protosrc = IPAddr(rt_object.routing_table[rt_object.mainRouter.DPID][get_subnet(rt_object, endpoint_ip)]["router_interface"])
  eth = ethernet(type=ethernet.ARP_TYPE, src=packet.src, dst=ETHER_BROADCAST)
  eth.set_payload(arp_req)
  msg = of.ofp_packet_out()
  msg.data = eth.pack()
  msg.actions.append(of.ofp_action_output(port = rt_object.routing_table[rt_object.mainRouter.DPID][get_subnet(rt_object, packet.next.dstip)]["port"]))
  msg.in_port = packet_in.in_port
  core.openflow.sendToDPID(rt_object.mainRouter.DPID, msg)

def generate_arp_reply(rt_object, packet, packet_in):
    arp_reply = arp()
    arp_reply.opcode = arp.REPLY
    ret_subnet = get_subnet_from_interface_ip(rt_object, packet.payload.protodst)

    # Convert MAC addresses to bytes
    hwsrc_bytes = EthAddr(packet.dst).toRaw()
    hwdst_bytes = EthAddr(packet.src).toRaw()

    arp_reply.hwsrc = hwsrc_bytes
    arp_reply.hwdst = hwdst_bytes
    arp_reply.protosrc = packet.payload.protodst
    arp_reply.protodst = packet.payload.protosrc

    eth = ethernet()
    eth.type = ethernet.ARP_TYPE

    # Use the bytes representation of MAC addresses
    eth.dst = EthAddr(rt_object.mainRouter.ip_to_mac[str(packet.payload.protosrc)]).toRaw()
    eth.src = EthAddr(rt_object.routing_table[rt_object.mainRouter.DPID][get_subnet(rt_object, ret_subnet)]["mac_interface"]).toRaw()

    eth.payload = arp_reply
    msg = of.ofp_packet_out()
    msg.data = eth.pack()
    action = of.ofp_action_output(port=packet_in.in_port)
    msg.actions.append(action)
    core.openflow.sendToDPID(rt_object.mainRouter.DPID, msg)


def arp_handler(rt_object, packet, packet_in):
  if(str(packet.payload.protosrc) not in rt_object.mainRouter.ip_to_mac):
    rt_object.mainRouter.ip_to_mac[str(packet.payload.protosrc)] = str(packet.src)
  # same with ip_to_port
  if(str(packet.payload.protosrc) not in rt_object.mainRouter.ip_to_port):
    rt_object.mainRouter.ip_to_port[str(packet.payload.protosrc)] = packet_in.in_port

  # handle arp request
  arp_dst_ip = str(packet.payload.protodst)
  arp_src_ip = str(packet.payload.protosrc)

  if packet.next.opcode == arp.REQUEST:
    #print(get_subnet(rt_object, arp_dst_ip))
    # if destination ip is the router (default gw), generate arp response
    if (arp_dst_ip == rt_object.routing_table[rt_object.mainRouter.DPID][get_subnet(rt_object, get_subnet_from_interface_ip(rt_object, str(packet.payload.protodst)))]["router_interface"] or get_subnet(rt_object, arp_dst_ip) == "192.168.0.0" or get_subnet(rt_object, arp_dst_ip) == "192.168.0.4"):
     generate_arp_reply(rt_object, packet, packet_in)
     

    elif same_subnet(rt_object, arp_dst_ip, arp_src_ip):
      if(packet.dst == rt_object.routing_table[rt_object.mainRouter.DPID][get_subnet(rt_object, arp_dst_ip)]["mac_interface"]):
        generate_arp_reply(rt_object, packet, packet_in)

  # if this is an arp reply    
  elif packet.next.opcode == arp.REPLY:
    # Learn source MAC addr of sender (next hop)
    rt_object.mainRouter.ip_to_mac[str(packet.payload.protosrc)] = str(packet.next.hwsrc)
    # release buffer
    release_buffer(rt_object, packet.payload.protosrc)

########################################## ICMP functions ##########################################
def generate_icmp_reply(rt_object, packet, icmp_type):
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
    ip_packet.protocol = ipv4.ICMP_PROTOCOL
    ip_packet.srcip = packet.next.dstip
    ip_packet.dstip = packet.next.srcip

    eth_packet = ethernet()
    eth_packet.type = ethernet.IP_TYPE

    # Ensure MAC addresses are in bytes format
    eth_src_mac = EthAddr(rt_object.routing_table[rt_object.mainRouter.DPID][get_subnet(rt_object, packet.next.srcip)]["mac_interface"])
    eth_dst_mac = EthAddr(packet.src)

    eth_packet.src = eth_src_mac
    eth_packet.dst = eth_dst_mac

    ip_packet.payload = p_icmp
    eth_packet.payload = ip_packet

    msg = of.ofp_packet_out()
    msg.actions.append(of.ofp_action_output(port=of.OFPP_IN_PORT))
    msg.data = eth_packet.pack()
    msg.in_port = rt_object.mainRouter.ip_to_port[str(packet.next.srcip)]
    core.openflow.sendToDPID(rt_object.mainRouter.DPID, msg)

########################################## IPV4 functions ##########################################
def ip_flow_mod(rt_object, packet, dest_ip):
  msg = of.ofp_flow_mod()
  msg.priority = 1000 # set priority to highest
  msg.match.dl_type = 0x800 # type: ip
  msg.match.nw_src = packet.next.srcip
  msg.match.nw_dst = packet.next.dstip
  msg.actions.append(of.ofp_action_dl_addr.set_dst(EthAddr(rt_object.mainRouter.ip_to_mac[str(dest_ip)])))
  msg.actions.append(of.ofp_action_output(port = rt_object.mainRouter.ip_to_port[str(dest_ip)]))
  core.openflow.sendToDPID(rt_object.mainRouter.DPID, msg)


def send_ip_packet(rt_object, buf_id, inport, dstip):
  msg = of.ofp_packet_out(buffer_id=buf_id, in_port=inport)
  msg.actions.append(of.ofp_action_dl_addr.set_dst(EthAddr(rt_object.mainRouter.ip_to_mac[str(dstip)])))
  msg.actions.append(of.ofp_action_output(port = rt_object.mainRouter.ip_to_port[str(dstip)]))
  core.openflow.sendToDPID(rt_object.mainRouter.DPID, msg)

def release_buffer(rt_object, dstip):
  while (len(rt_object.mainRouter.buffer[str(dstip)]) > 0):
    send_ip_packet(rt_object, rt_object.mainRouter.buffer[str(dstip)][0]["buffer_id"], rt_object.mainRouter.buffer[str(dstip)][0]["port"], dstip)
    del rt_object.mainRouter.buffer[str(dstip)][0]

def ipv4_handler(rt_object, packet, packet_in):
  rt_object.mainRouter.ip_to_port[str(packet.next.srcip)] = packet_in.in_port
  #print(type(packet.next.srcip))
  if isinstance(packet.next.next, icmp):
    if check_imcp(rt_object, str(packet.next.srcip), str(packet.next.dstip)) == False:
      generate_icmp_reply(rt_object, packet, TYPE_DEST_UNREACH)
      return
  
  if isinstance(packet.next.next, tcp):
    if check_tcp(rt_object, str(packet.next.srcip), str(packet.next.dstip)) == False:
      generate_icmp_reply(rt_object, packet, TYPE_DEST_UNREACH)
      return
  # if destination ip is valid (in routing table or one of routers)
  if validate_ip(rt_object, packet.next.dstip) :
    # if packet meant for THIS router
    if(is_interface(rt_object, str(packet.next.dstip))):
      if isinstance(packet.next.next, icmp):
        if(packet.next.next.type == TYPE_ECHO_REQUEST):
          generate_icmp_reply(rt_object, packet, TYPE_ECHO_REPLY)
          
    else:
        destination_ip = None
        # if packet is meant for network connected to another router, forward to next hop
        next_hop = rt_object.routing_table[rt_object.mainRouter.DPID][get_subnet(rt_object, packet.next.dstip)]["next_hop"]
        if(next_hop != "0.0.0.0"):
          destination_ip = next_hop
        else:
          destination_ip = str(packet.next.dstip)

        if destination_ip not in rt_object.mainRouter.ip_to_mac or destination_ip not in rt_object.mainRouter.ip_to_port:
          # add a new buffer for this dstip if it does not already exist
          if destination_ip not in rt_object.mainRouter.buffer:
            rt_object.mainRouter.buffer[destination_ip] = []

          # cache packet
          buffer_entry = {"buffer_id": packet_in.buffer_id, "port": packet_in.in_port}
          rt_object.mainRouter.buffer[destination_ip].append(buffer_entry)

          # generate arp request to learn next hop
          generate_arp_request(rt_object, packet.next.dstip, destination_ip, packet, packet_in)
  
        # we've already received the arp reply, so forward to known destination
        else:
          send_ip_packet(rt_object, packet_in.buffer_id, packet_in.in_port, destination_ip)

          # flow mod
          ip_flow_mod(rt_object, packet, destination_ip)

  # ip invalid, generate icmp reply dest unreachable
  else:
    generate_icmp_reply(rt_object, packet, TYPE_DEST_UNREACH)

########################################## MAIN CODE ##########################################
def router_handler(rt_object, packet, packet_in):
  if isinstance(packet.next, arp):
    arp_handler(rt_object, packet, packet_in)
  elif isinstance(packet.next, ipv4):
    ipv4_handler(rt_object, packet, packet_in)

