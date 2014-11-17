#!/usr/bin/env python

import sys, os, re
if sys.version_info[0]<3:
    from _winreg import *
else:
    from winreg import *


# ================================= Extras ======================================


# Decorator for observing a function's output
def debug(fn):

	MAX_STR_LEN=60
	INDENT=2

	def wrapper(*args, **kw):
		if not DEBUG:
			return fn(*args, **kw)

		def indent(depth, string):
			return (INDENT*depth*' ')+string

		def print_item(item, depth=3):
			if isinstance(item, list):
				print(indent(depth, '['))
				for i in item:
					print_item(i, depth+1)
				print(indent(depth, ']'))
				return
			if isinstance(item, tuple):
				print(indent(depth, '('))
				for i in item:
					print_item(i, depth+1)
				print(indent(depth, ')'))
				return
			if isinstance(item, str):
				string=item
				if len(string)>MAX_STR_LEN:
					string=string[:MAX_STR_LEN]+'..'
				print(indent(depth, "'"+string+"'"))
				return
				
			print('DEBUG: Can\'t pretty print item of type %s' % type(item))
		
		ret=fn(*args, **kw)
		log("%s()   --->   (function's output below)" % (fn.__name__))
		print_item(ret)
		return ret

	return wrapper

# Acts as print()
def log(*args):
	str=args[0]
	if len(args)>1:
		for arg in args[1:]:
			str+=', '+arg
	print(str)

# ================================= Mbed ======================================


# Print all info for the currently connected mbed boards
def print_discovered_mbeds(defs):
    rows=[]
    col1, col2, col3, col4 = 6, 37, 4, 12 
    for mbed in discover_connected_mbeds(defs):
        if len(mbed)==4:
            rows+=["%s %s %s %s" % (mbed[0].ljust(col1), mbed[1].ljust(col2), \
                                    mbed[2].rjust(col3), mbed[3].rjust(col4))]
        elif len(mbed)==3:
            rows+=["%s %s %s"    % (mbed[0].ljust(col1), mbed[1].ljust(col2), \
                                    mbed[2].rjust(col3))]
        elif len(mbed)==2:
            rows+=["%s %s"       % (mbed[0].ljust(col1), mbed[1].ljust(col2))]
        else:
            print("ERROR: Mbed board is missing ID or is in unknown format")
            exit(1)
    print("%s %s %s %s"          % ("Mount".ljust(col1), "Serial".ljust(col2), \
                                    "Port".ljust(col3), "Mbed board".rjust(col4)))
    print("%s" % "".ljust(col1+col2+col3+col4+3,'-'))
    for row in rows:
        print(row)


# Returns [(<mbed_mount_point>, <mbed_id>, <com port>, <board model>), ..]
# (notice that this function is permissive: adds new elements in-placesk when and if found)
def discover_connected_mbeds(defs):
    mbeds=[(m[0], m[1], '', '') for m in get_connected_mbeds()]
    for i in range(len(mbeds)):
        mbed=mbeds[i]
        mnt, id = mbed[0], mbed[1]
        id_prefix=id[0:4]
        if id_prefix in defs:
            board=defs[id_prefix]
            mbeds[i]=(mnt, id, mbeds[i][2], board)
        port=get_mbed_com_port(id)
        if port:
            mbeds[i]=(mnt, id, port, mbeds[i][3])
    return mbeds


# (This goes through a whole new loop, but this assures that even if
#  com is not detected, we still get the rest of info like mount point etc.)
def get_mbed_com_port(id):
    enum=OpenKey(HKEY_LOCAL_MACHINE, 'SYSTEM\CurrentControlSet\Enum')
    usb_devs=OpenKey(enum, 'USB')

    # first try to find all devs keys (by id)
    dev_keys=[]
    for VID in iter_keys(usb_devs):
        try:
            dev_keys+=[OpenKey(VID, id)]
        except:
            pass

    # then try to get port directly from "Device Parameters"
    for key in dev_keys:
        try:
            param=OpenKey(key, "Device Parameters")
            port=QueryValueEx(param, 'PortName')[0]
            return port
        except:
            pass

    # else follow symbolic dev links in registry
    for key in dev_keys:
        try:
            ports=[]
            parent_id=QueryValueEx(key, 'ParentIdPrefix')[0]
            for VID in iter_keys(usb_devs):
                for dev in iter_keys_as_str(VID):
                    if parent_id in dev:
                        ports+=[get_mbed_com_port(dev)]
            for port in ports:
                if port:
                    return port
        except:
            pass


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


# Iterate over subkeys of a key returning subkey as string
def iter_keys_as_str(key):
    for i in range(QueryInfoKey(key)[0]):
        yield EnumKey(key, i)


# Iterate over subkeys of a key
def iter_keys(key):
    for i in range(QueryInfoKey(key)[0]):
        yield OpenKey(key, EnumKey(key, i))

        
# Iterate over values of a key
def iter_vals(key):
    for i in range(QueryInfoKey(key)[1]):
        yield EnumValue(key, i)


# Get MBED devices (connected or not)
@debug
def get_mbed_devices():
    return [d for d in get_dos_devices() if 'VEN_MBED' in d[1].upper()]


# Get DOS devices (connected or not)
@debug
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
    string=''
    for i in range(0, len(bin), 2):
        # bin[i] is str in Python2 and int in Python3
        if isinstance(bin[i], int):
            if bin[i]<128:
                string+=chr(bin[i])
        elif isinstance(bin[i], str):
            string+=bin[i]
        else:
            print('ERROR: Can\'t decode REG_BIN from registry')
            exit(1)
    return string




# ================================= Main ======================================


defs={
    "0700": "NUCLEO_F103RB",
    "0705": "NUCLEO_F302R8",
    "0710": "NUCLEO_L152RE",
    "0715": "NUCLEO_L053R8",
    "0720": "NUCLEO_F401RE",
    "0725": "NUCLEO_F030R8",
    "0730": "NUCLEO_F072RB",
    "0735": "NUCLEO_F334R8",
    "0740": "NUCLEO_F411RE",
    "1010": "LPC1768",
    "1040": "LPC11U24",
    "1050": "LPC812",
    "1168": "LPC11U68",
    "1549": "LPC1549",
    "1070": "NRF51822",
    "0200": "KL25Z",
    "0220": "KL46Z",
    "0230": "K20D50M",
    "0240": "K64F"
}

if __name__ == '__main__':
    import sys
    DEBUG=False
    if len(sys.argv) == 2 and sys.argv[1] == '--debug':
        DEBUG=True
    print_discovered_mbeds(defs)