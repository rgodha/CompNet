
#!/usr/bin/env python

import sys
from switchyard.lib.address import *
from switchyard.lib.packet import *
from switchyard.lib.common import *
from switchyard.lib.testing import *

def mk_pkt(hwsrc, hwdst, ipsrc, ipdst, reply=False):
    ether = Ethernet()
    ether.src = EthAddr(hwsrc)
    ether.dst = EthAddr(hwdst)
    ether.ethertype = EtherType.IP

    ippkt = IPv4()
    ippkt.srcip = IPAddr(ipsrc)
    ippkt.dstip = IPAddr(ipdst)
    ippkt.protocol = IPProtocol.ICMP
    ippkt.ttl = 32

    icmppkt = ICMP()
    if reply:
        icmppkt.icmptype = ICMPType.EchoReply
    else:
        icmppkt.icmptype = ICMPType.EchoRequest

    return ether + ippkt + icmppkt

def switch_tests():
    s = Scenario("switch tests")
    s.add_interface('eth0', '10:00:00:00:00:01')
    s.add_interface('eth1', '10:00:00:00:00:02')
    s.add_interface('eth2', '10:00:00:00:00:03')

    # test case 1: a frame with broadcast destination should get sent out
    # all ports except ingress
    testpkt = mk_pkt("30:00:00:00:00:02", "ff:ff:ff:ff:ff:ff", "172.16.42.2", "255.255.255.255")
    s.expect(PacketInputEvent("eth1", testpkt, display=Ethernet), "An Ethernet frame with a broadcast destination address should arrive on eth1")
    s.expect(PacketOutputEvent("eth0", testpkt, "eth2", testpkt, display=Ethernet), "The Ethernet frame with a broadcast destination address should be forwarded out ports eth0 and eth2")

    # test case 2: a frame with any unicast address except one assigned to learning switch
    # interface should be sent out all ports except ingress
    reqpkt = mk_pkt("20:00:00:00:00:01", "30:00:00:00:00:02", '192.168.1.100','172.16.42.2')
    s.expect(PacketInputEvent("eth0", reqpkt, display=Ethernet), "An Ethernet frame from 20:00:00:00:00:01 to 30:00:00:00:00:02 should arrive on eth0")
    s.expect(PacketOutputEvent("eth1", reqpkt, display=Ethernet), "Ethernet frame destined for 30:00:00:00:00:02 should be sent out on eth1") 

    resppkt = mk_pkt("30:00:00:00:00:02", "20:00:00:00:00:01", '172.16.42.2', '192.168.1.100', reply=True)
    s.expect(PacketInputEvent("eth1", resppkt, display=Ethernet), "An Ethernet frame from 30:00:00:00:00:02 to 20:00:00:00:00:01 should arrive on eth1")
    s.expect(PacketOutputEvent("eth0", resppkt, display=Ethernet), "Ethernet frame destined to 20:00:00:00:00:01 should be sent out on eth0")

    # test case 3: a frame with dest address of one of the interfaces should
    # result in nothing happening
    reqpkt = mk_pkt("20:00:00:00:00:02", "10:00:00:00:00:03", '192.168.1.100','172.16.42.2')
    s.expect(PacketInputEvent("eth2", reqpkt, display=Ethernet), "An Ethernet frame should arrive on eth2 with destination address the same as eth2's MAC address")

    s.expect(PacketInputTimeoutEvent(1.0), "The hub should not do anything in response to a frame arriving with a destination address referring to the hub itself.")


    s.expect(PacketInputTimeoutEvent(10), "Silence")

    testpkt = mk_pkt("30:00:00:00:00:02", "ff:ff:ff:ff:ff:ff", "172.16.42.2", "255.255.255.255")
    s.expect(PacketInputEvent("eth1", testpkt, display=Ethernet), "An Ethernet frame with a broadcast destination address should arrive on eth1")
    s.expect(PacketOutputEvent("eth0", testpkt, "eth2", testpkt, display=Ethernet), "The Ethernet frame with a broadcast destination address should be forwarded out ports eth0 and eth2")


    resppkt = mk_pkt("20:00:00:00:00:01", "ff:ff:ff:ff:ff:ff", '172.16.42.2', '255.255.255.255')
    s.expect(PacketInputEvent("eth0", testpkt, display=Ethernet), "An Ethernet frame with a broadcast destination address should arrive on eth0")
    s.expect(PacketOutputEvent("eth1", testpkt, "eth2", testpkt, display=Ethernet), "The Ethernet frame with a broadcast destination address should be forwarded out ports eth1 and eth2")

    s.expect(PacketInputTimeoutEvent(10), "Silence")

    testpkt = mk_pkt("30:00:00:00:00:02", "ff:ff:ff:ff:ff:ff", "172.16.42.2", "255.255.255.255")
    s.expect(PacketInputEvent("eth1", testpkt, display=Ethernet), "An Ethernet frame with a broadcast destination address should arrive on eth1")
    s.expect(PacketOutputEvent("eth0", testpkt, "eth2", testpkt, display=Ethernet), "The Ethernet frame with a broadcast destination address should be forwarded out ports eth0 and eth2")


    resppkt = mk_pkt("20:00:00:00:00:01", "ff:ff:ff:ff:ff:ff", '172.16.42.2', '255.255.255.255')
    s.expect(PacketInputEvent("eth0", testpkt, display=Ethernet), "An Ethernet frame with a broadcast destination address should arrive on eth0")
    s.expect(PacketOutputEvent("eth1", testpkt, "eth2", testpkt, display=Ethernet), "The Ethernet frame with a broadcast destination address should be forwarded out ports eth1 and eth2")

    s.expect(PacketInputTimeoutEvent(10), "Silence")

    testpkt = mk_pkt("30:00:00:00:00:02", "ff:ff:ff:ff:ff:ff", "172.16.42.2", "255.255.255.255")
    s.expect(PacketInputEvent("eth1", testpkt, display=Ethernet), "An Ethernet frame with a broadcast destination address should arrive on eth1")
    s.expect(PacketOutputEvent("eth0", testpkt, "eth2", testpkt, display=Ethernet), "The Ethernet frame with a broadcast destination address should be forwarded out ports eth0 and eth2")


    resppkt = mk_pkt("20:00:00:00:00:01", "ff:ff:ff:ff:ff:ff", '172.16.42.2', '255.255.255.255')
    s.expect(PacketInputEvent("eth0", testpkt, display=Ethernet), "An Ethernet frame with a broadcast destination address should arrive on eth0")
    s.expect(PacketOutputEvent("eth1", testpkt, "eth2", testpkt, display=Ethernet), "The Ethernet frame with a broadcast destination address should be forwarded out ports eth1 and eth2")

    s.expect(PacketInputTimeoutEvent(10), "Silence")

    testpkt = mk_pkt("30:00:00:00:00:02", "ff:ff:ff:ff:ff:ff", "172.16.42.2", "255.255.255.255")
    s.expect(PacketInputEvent("eth1", testpkt, display=Ethernet), "An Ethernet frame with a broadcast destination address should arrive on eth1")
    s.expect(PacketOutputEvent("eth0", testpkt, "eth2", testpkt, display=Ethernet), "The Ethernet frame with a broadcast destination address should be forwarded out ports eth0 and eth2")


    resppkt = mk_pkt("20:00:00:00:00:01", "ff:ff:ff:ff:ff:ff", '172.16.42.2', '255.255.255.255')
    s.expect(PacketInputEvent("eth0", testpkt, display=Ethernet), "An Ethernet frame with a broadcast destination address should arrive on eth0")
    s.expect(PacketOutputEvent("eth1", testpkt, "eth2", testpkt, display=Ethernet), "The Ethernet frame with a broadcast destination address should be forwarded out ports eth1 and eth2")

    s.expect(PacketInputTimeoutEvent(10), "Silence")

    testpkt = mk_pkt("30:00:00:00:00:02", "ff:ff:ff:ff:ff:ff", "172.16.42.2", "255.255.255.255")
    s.expect(PacketInputEvent("eth1", testpkt, display=Ethernet), "An Ethernet frame with a broadcast destination address should arrive on eth1")
    s.expect(PacketOutputEvent("eth0", testpkt, "eth2", testpkt, display=Ethernet), "The Ethernet frame with a broadcast destination address should be forwarded out ports eth0 and eth2")


    testpkt = mk_pkt("20:00:00:00:00:01", "ff:ff:ff:ff:ff:ff", '172.16.42.2', '255.255.255.255')
    s.expect(PacketInputEvent("eth0", testpkt, display=Ethernet), "An Ethernet frame with a broadcast destination address should arrive on eth0")
    s.expect(PacketOutputEvent("eth1", testpkt, "eth2", testpkt, display=Ethernet), "The Ethernet frame with a broadcast destination address should be forwarded out ports eth1 and eth2")

    s.expect(PacketInputTimeoutEvent(10), "Silence")

    testpkt = mk_pkt("30:00:00:00:00:02", "ff:ff:ff:ff:ff:ff", "172.16.42.2", "255.255.255.255")
    s.expect(PacketInputEvent("eth1", testpkt, display=Ethernet), "An Ethernet frame with a broadcast destination address should arrive on eth1")
    s.expect(PacketOutputEvent("eth0", testpkt, "eth2", testpkt, display=Ethernet), "The Ethernet frame with a broadcast destination address should be forwarded out ports eth0 and eth2")


    testpkt = mk_pkt("20:00:00:00:00:01", "ff:ff:ff:ff:ff:ff", '172.16.42.2', '255.255.255.255')
    s.expect(PacketInputEvent("eth0", testpkt, display=Ethernet), "An Ethernet frame with a broadcast destination address should arrive on eth0")
    s.expect(PacketOutputEvent("eth1", testpkt, "eth2", testpkt, display=Ethernet), "The Ethernet frame with a broadcast destination address should be forwarded out ports eth1 and eth2")

    s.expect(PacketInputTimeoutEvent(10), "Silence")


    reqpkt = mk_pkt("20:00:00:00:00:01", "20:00:00:00:00:02", '192.168.100.1','192.168.1.100')
    s.expect(PacketInputEvent("eth0", reqpkt, display=Ethernet), "An Ethernet frame should arrive on eth0 with destination address for eth2")
    s.expect(PacketOutputEvent("eth1", reqpkt, "eth2", reqpkt, display=Ethernet), "The ethernet frame should be flooded in eth1 and eth2")

    reqpkt = mk_pkt("20:00:00:00:00:02", "20:00:00:00:00:01", '192.168.1.100','192.168.100.1', reply=True)
    s.expect(PacketInputEvent("eth2", reqpkt, display=Ethernet), "An Ethernet frame should arrive on eth2 destined for eth0")
    s.expect(PacketOutputEvent("eth0", reqpkt, display=Ethernet), "The reply ethernet frame should be sent on eth0")


    testpkt = mk_pkt("20:00:00:00:00:03", "ff:ff:ff:ff:ff:ff", '192.168.1.101', '255.255.255.255')
    s.expect(PacketInputEvent("eth2", testpkt, display=Ethernet), "An Ethernet frame with a broadcast destination address should arrive on eth2")
    s.expect(PacketOutputEvent("eth0", testpkt, "eth1", testpkt, display=Ethernet), "The reply ethernet frame should be flooded on eth0 and eth1")

    reqpkt = mk_pkt("20:00:00:00:00:01", "20:00:00:00:00:03", '192.168.100.1','192.168.1.101')
    s.expect(PacketInputEvent("eth0", reqpkt, display=Ethernet), "An Ethernet frame should arrive on eth0 with destination address for eth2")
    s.expect(PacketOutputEvent("eth2", reqpkt, display=Ethernet), "The ethernet frame should be sent on eth2")


    testpkt = mk_pkt("20:00:00:00:00:03", "ff:ff:ff:ff:ff:ff", '192.168.1.101', '255.255.255.255')
    s.expect(PacketInputEvent("eth0", testpkt, display=Ethernet), "An Ethernet frame with a broadcast destination  address should arrive on eth0")
    s.expect(PacketOutputEvent("eth1", testpkt, "eth2", testpkt, display=Ethernet), "An Ethernet frame should be flooded  on eth1 and eth1 & eth2")

    testpkt = mk_pkt("30:00:00:00:00:02", "20:00:00:00:00:03", "172.16.42.2", "192.168.1.101")
    s.expect(PacketInputEvent("eth1", testpkt, display=Ethernet), "An Ethernet frame with 20:00:00:00:00:03 destination address should arrive on eth1")
    s.expect(PacketOutputEvent("eth0", testpkt, display=Ethernet), "An Ethernet frame should arrive on eth0")
    return s

scenario = switch_tests()
