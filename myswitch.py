#!/usr/bin/env python3

'''
Note that this file currently has the code to implement a "hub"
in it, not a learning switch.  (I.e., it's currently a switch
that doesn't learn.)

Algorithm:
1) Start with empty table.
2) When frame arrive with destination & its not in table, broadcast frame to all ports.
3) Store src address from where the packet arrived.
4) Remove stale address.
'''
from switchyard.lib.address import *
from switchyard.lib.packet import *
from switchyard.lib.common import *
import time

# Global Mac Address Table
class macTableClass(object):
	def __init__(self, mac, port, arrival_time):
		self.mac = mac
		self.port = port
		self.arrival_time = arrival_time 
		self.expiryTime = self.arrival_time + 30 	# 30 sec expiry time

macTable = []

# Expiry Timer Handler: It is called after 10sec and iterate over the list of
# Mac Address and remove the entry, if entry's expiry timer is move than current time.
def expiryTimerHandler():
	now = int(time.time())
	lenMacTable = len(macTable)
	log_info("Print the len of macTable {}".format(lenMacTable))

	for macObj in macTable:
		if macObj.expiryTime <= now:
			log_info("#RG# Deleting the MAC Address {} on port".format(macObj.mac, macObj.port))
			macTable.remove(macObj)

	print (macTable)

def switchy_main(net):
	AddMacEntryFlag = True								## If True: add this entry to Global Mac Address Table else: No
	FoundDestFlag = False								## If True: found the dest. addess and port else: No
	my_interfaces = net.interfaces() 
	mymacs = [intf.ethaddr for intf in my_interfaces]
	
	while True:
		try:
			iport,timestamp,packet = net.recv_packet(5, True)
		except NoPackets:
			expiryTimerHandler()  						## Call ExpiryTimer Handler and delete stale Mac Address.
			continue
		except Shutdown:
			return

		log_debug ("In {} received packet {} on {}".format(net.name, packet, iport))
		if packet[0].dst in mymacs:
			log_debug ("Packet intended for me.")
		else:
			for macObj in macTable:
				if packet[0].dst == macObj.mac:
					FoundDestFlag = True
					log_debug("Forward the packet to MAC: {} on port {}".format(macObj.mac, macObj.port))
					net.send_packet(macObj.port, packet)

			if FoundDestFlag == False:
				for intf in my_interfaces:
					if iport != intf.name:
						log_debug ("Flooding packet {} to {}".format(packet, intf.name))
						net.send_packet(intf.name, packet)


		# Store the src address of the rev'ed packet.
		# If MAC Already present, Update the expiry timer in Global Mac Address for this MAC 
		# Add the MAC Entry only if its unique.
		if packet[0].src != "ff:ff:ff:ff:ff:ff":
			for macObj in macTable:
				if packet[0].src == macObj.mac:
					macObj.expiryTime = int(time.time()) + 30
					AddMacEntryFlag = False
					log_info("Mac {} is already present in Global Mac Table. Increment Expiration Time to {}".format(macObj.mac, macObj.expiryTime))
					if macObj.port != iport:
						macObj.port = iport
						log_warn("Port Address Changed for this MAC {}".format(macObj.mac))

			if AddMacEntryFlag == True:
				currentTime = int(time.time())
				AddEntry = macTableClass(packet[0].src, iport, currentTime)
				macTable.append(AddEntry)
				log_info("#RG# Learning the MAC {} on port {} on time {}".format(packet[0].src, iport, currentTime))

		#Re initialize the flags
		FoundDestFlag = False
		AddMacEntryFlag = True

	net.shutdown()
