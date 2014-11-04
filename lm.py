#!/usr/bin/env python
import sys, os, re
if sys.version_info[0]<3:
	from _winreg import *
else:
	from winreg import *




# ================================= Mbed ======================================


# Print all info for the currently connected mbed boards
def print_discovered_mbeds(defs):
	rows=[]
	col1, col2, col3 = 14, 27, 10 
	for mbed in discover_connected_mbeds(defs):
		if len(mbed)==3:
			rows+=["%s %s %s" % (mbed[0].ljust(col1), mbed[1].ljust(col2), \
							     mbed[2].rjust(col3))]
		elif len(mbed)==2:
			rows+=["%s %s"    % (mbed[0].ljust(col1), mbed[1].ljust(col2))]
		else:
			print("ERROR: Mbed board is missing ID or is in unknown format")
			exit(1)
	print("%s %s %s" % ("Mount point".ljust(col1), "Mbed ID".ljust(col2), \
						"Mbed board".rjust(col3)))
	print("%s" % "".ljust(col1+col2+col3+2,'-'))
	for row in rows:
		print(row)


# Returns [(<mbed_mount_point>, <mbed_id>), ..]
def discover_connected_mbeds(defs):
	mbeds=get_connected_mbeds()
	for i in range(len(mbeds)):
		mbed=mbeds[i]
		for board in defs:
			for id in defs[board]:
				if mbed[1] in id:
					mbeds[i]=(mbed[0], mbed[1], board)
	return mbeds


# Returns [(<mbed_mount_point>, <mbed_id>), ..]
def get_connected_mbeds():
	return [m for m in get_mbeds() if os.path.exists(m[0])]


# Returns [(<mbed_mount_point>, <mbed_id>), ..]
def get_mbeds():
	mbeds=[]
	for mbed in get_mbed_devices():
		mountpoint=re.match('.*\\\\(.:)$', mbed[0]).group(1)
		id=re.search('[0-9A-Fa-f]{10,36}', mbed[1]).group(0)
		mbeds+=[(mountpoint, id)]
	return mbeds




# =============================== Registry ====================================


# Get MBED devices (connected or not)
def get_mbed_devices():
	return [d for d in get_dos_devices() if 'VEN_MBED' in d[1].upper()]


# Get DOS devices (connected or not)
def get_dos_devices():
	ddevs=[dev for dev in get_mounted_devices() if 'DosDevices' in dev[0]]
	return [(d[0], regbin2str(d[1])) for d in ddevs]


# Get all mounted devices (connected or not)
def get_mounted_devices():
	devs=[]
	mounts=OpenKey(HKEY_LOCAL_MACHINE, 'SYSTEM\MountedDevices')
	for i in range(QueryInfoKey(mounts)[1]):
		devs+=[EnumValue(mounts, i)]
	return devs


# Decode registry binary to readable string
def regbin2str(bin):
	str=''
	for i in range(0, len(bin), 2):
		if bin[i]<128:
			str+=chr(bin[i])
	return str




# ================================= Main ======================================


defs={  
   "KL46Z":[  
      "usb-MBED_microcontroller_02200201E6761E7B1B88E3A3-0:0"
   ],
   "KL25Z":[  
      "usb-MBED_microcontroller_0200020113F4A2A569556DD7-0:0"
   ],
   "NUCLEO_L152RE":[  
      "usb-MBED_microcontroller_066EFF534951775087215736-0:0"
   ],
   "NUCLEO_F302R8":[  
      "usb-MBED_microcontroller_066EFF525257775087141721-0:0"
   ],
   "NUCLEO_F401RE":[  
      "usb-MBED_microcontroller_066EFF534951775087061841-0:0"
   ],
   "NUCLEO_F030R8":[  
      "usb-MBED_microcontroller_066CFF534951775087112139-0:0"
   ],
   "NUCLEO_F103RB":[  
      "usb-MBED_microcontroller_066EFF534951775087124315-0:0"
   ],
   "NUCLEO_L053R8":[  
      "usb-MBED_microcontroller_066FFF525257775087155144-0:0"
   ],
   "LPC11U24":[  
      "usb-MBED_MBED_CMSIS-DAP_A000000001-0:0"
   ],
   "LPC1768":[  
      "usb-MBED_microcontrolleur_10105a42e87da33c103dccfb6bc235360a97-0:0"
   ],
   "LPC2368":[  
      "usb-mbed_Microcontroller_100000000000000000000002F7F092F4-0:0"
   ],
   "LPC11U68":[  
      "usb-MBED_microcontroller_116802021D4C8D9A222B0DCF-0:0"
   ],
   "LPC1549":[  
      "usb-MBED_microcontroller_154902021F5F41C12038C5B5-0:0",
      "usb-MBED_microcontroller_154902021A4D7483252AF0F7-0:0"
   ],
   "LPC812":[  
      "usb-MBED_microcontroller_10500200E72F934C9D8F4E6E-0:0",
      "usb-MBED_microcontrolleur_10500200FE37FA0C8497272E-0:0"
   ]
}

if __name__ == '__main__':
	print_discovered_mbeds(defs)
