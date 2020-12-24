#
#
#   prepares a cisco config for mac addresses found in the new switch using a database with stored old configs=
#
#

import sqlite3
import os
from os import name

def clearScreen():
    if name == "nt":
        os.system("cls")
    else:
        os.system("clear")

db_name = ""
file = ""
vlan = ""
while True:
    clearScreen()
    db_name = raw_input("Please input database name to open: ")
    file = raw_input("Please input name of switch log: ")
    print("Enter the VLANs for which you want configs for.")
    vlan = int(raw_input("Type 1 for all VLANs: "))
    break

con = sqlite3.connect(db_name)
c = con.cursor()

mac_data = []
always_print = False
i = -5
with open(file) as infile:
    for line in infile:
        if "sh mac address" in line:
            always_print = True
        if "Multicast Entries" in line:
            always_print = False
        if always_print == True:
            mac_data.append(line.split())
            i += 1

mac_data = mac_data[4:]
fileout = "NEW_CONFIGS.txt"
config = []
duplicate_check = []

commands_not_wanted = ['switchport trunk encapsulation dot1q', 'macro description cisco-phone', 'tx-queue',
                    'bandwidth percent', 'priority high', 'shape percent']

with open(fileout,'w') as outfile:
    for item in mac_data[:-1]:
        if item[4] in duplicate_check:
            continue
        else:
            duplicate_check.append(item[4])
            
            if vlan == 1:
                c.execute("SELECT config FROM configs WHERE mac_address=?", (item[1],))
            else:
                c.execute("SELECT config FROM configs WHERE mac_address=? AND vlan=? ", (item[1],vlan))
            temp = c.fetchone()
            if temp != None:
                config.append("\r\ndefault " + item[4]+"\r\n")
                config.append("interface " + item[4]+"\r\n")
                con.text_factory = str
                temp1 = temp[0]
                config.append(temp1)
    for elem in config:
        outfile.write(elem)