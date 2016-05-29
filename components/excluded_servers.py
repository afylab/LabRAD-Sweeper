"""
Holds the list of servers to be ignored by the sweeper program.
"""

global excluded_servers

def labrad_format(string):
	"""Converts to all lower case, and converts '-' to '_'"""
	return (string.lower()).replace('-','_')
"""
Changed labrad.format(node())+'_gpib_bus' to labrad_format(node())+'_gpib_bus'
-Zach
"""
from platform import node
serial_server_name = labrad_format(node())+'_serial_server'
gpib_bus_name      = labrad_format(node())+'_gpib_bus'

excluded_servers = [
            'gpib_device_manager',
            gpib_bus_name,
            serial_server_name,
            'manager',
            'registry',
            'data_vault',
            ]
