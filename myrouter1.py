#!/usr/bin/env python3

'''
Basic IPv4 router (static routing) in Python.
'''

import sys
import os
import time
from switchyard.lib.packet import *
from switchyard.lib.address import *
from switchyard.lib.common import *

class forwardingTableClass(object):
    def __init__ (self, netDest, netMask, gateWay, intf, prefixlen):
        self.netDest = netDest
        self.netMask = netMask
        self.gateWay = gateWay
        self.intf = intf
        self.prefixlen = prefixlen

class WaitQueueClass(object):
    def __init__(self, pkt, count, srcHw, srcIp, Intf):
        self.pkt = pkt
        self.count = count
        self.srcHw = srcHw
        self.srcIp = srcIp
        self.Intf = Intf

forwardingTable = []
WaitQueue = []
arpTable = {}

class Router(object):
    def __init__(self, net):
        self.net = net
        # other initialization stuff here

    def forwardTableLookUp(self, destIP):
        GotEntry = False
        maxPrefixlen = 0
        for fwdTblObj in forwardingTable:
            prefix = IPv4Address(fwdTblObj.netDest)
            if ((int(prefix) & int(destIP)) == int(prefix)):
                print ((int(prefix) & int(destIP)) == int(prefix))
                if fwdTblObj.prefixlen > maxPrefixlen:
                    SendFromIntf = fwdTblObj.intf
                    GotEntry = True
                    print (SendFromIntf, maxPrefixlen)
            else:
                continue

        return (GotEntry, SendFromIntf)

    # Function to create an Arp Packet  
    def CreateArpPacket(self, srchw, srcip, targetip):
        ether = Ethernet()
        ether.src = srchw
        ether.dst = 'ff:ff:ff:ff:ff:ff'
        ether.ethertype = EtherType.ARP
        arp = Arp()
        arp.operation = ArpOperation.Request
        arp.senderhwaddr = srchw
        arp.senderprotoaddr = srcip
        arp.targethwaddr = 'ff:ff:ff:ff:ff:ff'
        arp.targetprotoaddr = targetip
        arppacket = ether + arp 
        return arppacket

    def router_main(self, net): 
        '''
        Main method for router; we stay in a loop in this method, receiving
        packets until the end of time.
        '''
        my_interfaces = net.interfaces()
        #pktDest = False
        my_ips = [intf.ipaddr for intf in my_interfaces]
        #for intf in my_interfaces:
        #    print (intf.name, intf.ipaddr)

        while True:
            gotpkt = True
            try:
                dev,pkt = self.net.recv_packet(timeout=1.0)
            except NoPackets:
                log_debug("No packets available in recv_packet")
                gotpkt = False
            except Shutdown:
                log_debug("Got shutdown signal")
                break

            SendARPReq = True
            if gotpkt:
                log_debug("Got a packet: {}".format(str(pkt)))

                #Handling of ARP Packets
                arp = pkt.get_header(Arp)
                if(arp):
                    # If it is an ARP Packet, save the Src IP: Src MAC in Arp Table
                    arpTable[arp.senderprotoaddr] = arp.senderhwaddr
                    print (arpTable)

                    for intf in my_interfaces:
                        if arp.targetprotoaddr == intf.ipaddr:
                            log_debug("Got ARP packet on interface: {}".format(intf.name))
                            print (arp.operation)
                            if arp.operation == ArpOperation.Request:
                                log_debug("Got ARP Request on interface: {}".format(intf.name))
                                targethwaddr = arp.senderhwaddr
                                targetprotoaddr = arp.senderprotoaddr
                                myprotoaddr = arp.targetprotoaddr
                                packet = create_ip_arp_reply(intf.ethaddr, targethwaddr, myprotoaddr, targetprotoaddr)
                                log_debug("Replying to ARP Request by Packet: {}".format(str(packet)))
                                net.send_packet(intf.name, packet)

                            # This is, if we get ARP Reply or Response
                            # Save the Src MAC and Src IP in arpTable
                            else:
                                #log_info("ARP Reply on intf {}. Update table, Construct new pkt and Send".format(dev))
                                #arpTable[arp.senderprotoaddr] = arp.senderhwaddr
                                # Get the packet from Queue and save.
                                # Also remove this packet from this WaitQueue.

                                for pktinQueue in WaitQueue:
                                    print (pktinQueue.pkt)
                                    if arp.senderprotoaddr == pktinQueue.pkt[1].dst:
                                        SendPkt = pktinQueue.pkt
                                        log_info("sending the Packet out on intf {}".format(dev))
                                        SendPkt[0].src = intf.ethaddr
                                        SendPkt[0].dst = arpTable[SendPkt[1].dst]
                                        SendPkt.get_header(IPv4).ttl = SendPkt.get_header(IPv4).ttl - 1
                                        net.send_packet(dev, SendPkt)
                                        
                                        log_debug("Removing the pkt {} from WaitQueue".format(pktinQueue.pkt))
                                        pktinQueue.count = 10
                                        #WaitQueue.remove(pktinQueue)

                                for pktinQueue in WaitQueue:
                                    if pktinQueue.count == 10:
                                        WaitQueue.remove(pktinQueue)

                        else:
                            continue

                # Get the IPv4 Packtet Headers and decrement the TTL
                ipv4_header = pkt.get_header(IPv4)
                if (ipv4_header):
                    log_debug("#1 Got a IPv4 Header packet: {}".format(str(ipv4_header)))

                    # Handling of packets that comes to me. Just Drop It! TC1
                    if ipv4_header.dst in my_ips:
                        log_warn("Pkt for me. Do not do anything for this packet.")
                        continue

                    # Handling of Normal IP Packets
                    GotEntry, SendFromIntf = self.forwardTableLookUp(ipv4_header.dst)
                    log_info("Packet to be set from intf {} GotEntry: {}".format(SendFromIntf, GotEntry))

                    if GotEntry == True:
                        # Check for this destIP or intf entry in ARP Table, if present forward the IP packet.
                        # If not send an Arp Request and put the packet in Queue.
                        # 1. Check in Arp Table for entry

                        # Get the interface Object for this SendFromIntf interface. It is an Optimization.
                        for intf in my_interfaces:
                            if intf.name == SendFromIntf:
                                interfaceObj = intf

                        print (arpTable)
                        if pkt[1].dst in arpTable:
                            log_info("Pkt ether dest is present in Arp Table, directly sending the packet out on intf {}".format(SendFromIntf))
                            pkt[0].src = interfaceObj.ethaddr
                            pkt[0].dst = arpTable[pkt[1].dst]
                            pkt.get_header(IPv4).ttl = pkt.get_header(IPv4).ttl - 1
                            net.send_packet(SendFromIntf, pkt)
    
                        # If not in arpTable, send an ARP Request and put pkt in Queue.
                        else:
                            # Check if we have already sent the ARP Request for packet: TC2
                            for pktInQ in WaitQueue:
                                if pkt[1].dst == pktInQ.pkt[1].dst:
                                    SendARPReq = False
                                    log_debug("ARP Req already in Queue. Do not send again.")

                            srcHw = interfaceObj.ethaddr
                            srcIp = interfaceObj.ipaddr
                            
                            if SendARPReq == True:
                                log_info("Send an ARP Req from srchw {} srcIP {} destIP {}".format(srcHw, srcIp, ipv4_header.dst))
                                ArpReqPkt = self.CreateArpPacket(srcHw, srcIp, ipv4_header.dst)
                                net.send_packet(SendFromIntf, ArpReqPkt)
                            
                            # Put the packet in Queue and Send when we get arp Reply
                            QEntry = WaitQueueClass(pkt, 0, srcHw, srcIp, SendFromIntf)
                            WaitQueue.append(QEntry)
                        
                    else:
                        # No Matching Entry found in forwarding Table. Send to Default Route.
                        log_info("No Destination found in forwardingLook up table for packet {}.".format(pkt))
    
            # Else if we have not got any packet:
            else:
                QDestIP = {}
                for pktsInQ in WaitQueue:
                    QDestIP[pktsInQ.pkt[1].dst] = False

                for pktsInQ in WaitQueue:
                    if pktsInQ.count > 5:
                        log_info("Arp Packet for IP {} have been sent more than 5 times. Drop it.".format(pktsInQ.pkt[1].dst))
                        WaitQueue.remove(pktsInQ)

                    # Increment the count for this packet
                    pktsInQ.count += 1

                    # Send the ARP Request Again
                    if QDestIP[pktsInQ.pkt[1].dst] == False:
                        log_info("Send an ARP Req from srchw {} srcIP {} destIP {}".format(pktsInQ.srcHw, pktsInQ.srcIp, pktsInQ.pkt[1].dst))
                        ArpReqPkt = self.CreateArpPacket(srcHw, srcIp, pktsInQ.pkt[1].dst)
                        net.send_packet(pktsInQ.Intf, ArpReqPkt)

                    QDestIP[pktsInQ.pkt[1].dst] = True


def switchy_main(net):
    '''
    Main entry point for router.  Just create Router
    object and get it going.
    '''
    #Build a Forwarding Table
    # 1) Read from forwarding_table.txt and build Routing Table:
    # 2) Through a call to net.interfaces()
    #cmd = os.getcwd()
    #log_debug("Current cmd: {}".format(cmd))
    my_interfaces = net.interfaces()

    forwardingTableFile = open("/home/rahul/switchyard/examples/exercises/router/forwarding_table.txt",'r')
    for line in forwardingTableFile:
        line = line.replace('\n','')
        NetDest, NetMask, GateWay, Intf = line.split()
        NetConcat = NetDest + '/' + NetMask
        netaddr = IPv4Network(NetConcat)
        AddEntry = forwardingTableClass(NetDest, NetMask, GateWay, Intf, netaddr.prefixlen)
        forwardingTable.append(AddEntry)
        log_info("Added the entry as NetDest {} NetMask {} Gateway {} on Interface {} Prefixlen {}".format(NetDest, NetMask, GateWay, Intf, netaddr.prefixlen))

    # Get the Router Interfaces IP and add in forwarding table.
    for intf in my_interfaces:
        NetDest = intf.ipaddr
        mask = IPv4Address('255.255.255.0')
        NetDest = str(IPv4Address(int(NetDest) & int(mask)))
        NetMask = str(intf.netmask)
        # Putting Gateway as self IP as of now. Use Router Interface to forward packets.
        NetConcat = NetDest + '/' + NetMask
        netaddr = IPv4Network(NetConcat)
        AddEntry = forwardingTableClass(NetDest, NetMask, NetDest, intf.name, netaddr.prefixlen)
        forwardingTable.append(AddEntry)
        log_info("Added the entry as NetDest {} NetMask {} Gateway {} on Interface {} Prefixlen {}".format(NetDest, NetMask, NetDest, intf.name, netaddr.prefixlen))

    r = Router(net)
    r.router_main(net)
    net.shutdown()
