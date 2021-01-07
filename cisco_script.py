#
#
#   parses a log file for port configs attached to each mac address
#
#

import sqlite3
import os
from os import name
import tkinter as tk
from tkinter import filedialog

db_name = ""
file = ""
vlan = ""
format_dic = {"Catalyst 4500 L3 Switch Software":1,
                "C3750 Software":2, 
                "C2960 Software":2, 
                "Catalyst L3 Switch Software":2,
                "C3750E Software":2, 
                "C3500XL Software":2, 
                "C3560 Software":2}

def createDatabase ():
    file = root.filename1
    db_name = database_input.get()
    con = sqlite3.connect(db_name+".db")
    c = con.cursor()

    mac_data = []
    ports = []
    version = []
    always_print = False
    format_type = 0

    with open(file) as infile:
        for line in infile:
            if "sh ver" in line:
                always_print = True
            if "Compiled" in line:
                always_print = False
            if always_print == True:
                version.append(line)
    
    for j in format_dic:
        for k in version:
            if j in k:
                format_type = format_dic[j]
                if format_type == 1:
                    i=-5
                if format_type == 2:
                    i=-6

    print("Format type: " +str(format_type))

    with open(file) as infile:
        for line in infile:
            if format_type == 1:
                if "sh mac address" in line:
                    always_print = True
                if "Multicast Entries" in line:
                    always_print = False
                if always_print == True:
                    mac_data.append(line.split())
                    i += 1
                    #print(str(i) + " -- " +line)
            if format_type == 2:
                if "sh mac address" in line:
                    always_print = True
                if "Total Mac Addresses" in line:
                    always_print = False
                if always_print == True:
                    mac_data.append(line.split())
                    i += 1
    
    c.execute("""CREATE TABLE configs (
                mac_address text,
                port text,
                vlan integer
                )""")
    con.commit()

    if format_type == 1:
        mac_data = mac_data[4:]
        mac_data = mac_data[:-1]
        x=4
    if format_type == 2:
        x=3
        mac_data = mac_data[7:]

    print("MAC Addresses Found: "+ str(i))
    ii=0
    for r in mac_data:
        if r[x] != "CPU":
            ii += 1
            ports.append(r[x])
            c.execute("INSERT INTO configs VALUES ('{}', '{}', '{}')".format(r[1], r[x], r[0]))
    
    print("MAC Addresses added to Database: "+ str(ii))
    con.commit()

    found_port = False
    config_list = []
    c.execute("alter table configs add column config 'text'")
    con.commit()

    for port in ports:
        if format_type == 1:
            temp = "interface " + port
        if format_type == 2:
            if port.startswith('Gi'):
                port2 = port.replace('Gi', 'GigabitEthernet')
                temp = "interface " + port2
            elif port.startswith('Fa'):
                port2 = port.replace('Fa', 'FastEthernet')
                temp = "interface " + port2
            elif port.startswith('Po'):
                port2 = port.replace('Po', 'Port-channel')
                temp = "interface " + port2

        with open(file) as infile:
            for line in infile:
                templine = line.strip()
                #print(templine + " == " + temp)
                if temp == templine:
                    found_port = True
                if line.startswith("!"):
                    found_port = False
                if found_port == True:
                    if line == "":
                        continue
                    else:
                        if(line.startswith(temp)):
                            continue
                        config_list.append(line)
            port_config = "".join(config_list)
        
            c.execute("UPDATE configs SET config = ? WHERE port = ?", (port_config , port)) 
            config_list = []   
    
    con.commit()
    con.close()

    output = tk.Label(root, text = "Database Created!")
    canvas.create_window(250, 230, window =output)

def createConfig ():
    file = root.filename2
    db_name = root.filename3
    all_vlan = vlan_input.get().split(',')
    con = sqlite3.connect(db_name)
    c = con.cursor()

    mac_data = []
    always_print = False
    format_type = 0

    with open(file) as infile:
        for line in infile:
            for item in format_dic:
                if item in line:
                    format_type = format_dic[item]
                    if format_type == 1:
                        i=-5
                    if format_type == 2:
                        i=-6
                    continue
            if format_type == 1:
                if "sh mac address" in line:
                    always_print = True
                if "Multicast Entries" in line:
                    always_print = False
                if always_print == True:
                    mac_data.append(line.split())
                    i += 1
                    #print(str(i) + " -- " +line)
            if format_type == 2:
                if "sh mac address" in line:
                    always_print = True
                if "Total Mac Addresses" in line:
                    always_print = False
                if always_print == True:
                    mac_data.append(line.split())
                    i += 1

    if format_type == 1:
        mac_data = mac_data[4:]
        mac_data = mac_data[:-1]
        num=4
    if format_type == 2:
        num=3
        mac_data = mac_data[7:]

    fileout = config_input.get()
    config = []
    duplicate_check = []

    commands_not_wanted = ['switchport trunk encapsulation dot1q', 'macro description cisco-phone', 'tx-queue',
                        'bandwidth percent', 'priority high', 'shape percent']

    with open(fileout,'w') as outfile:
        for item in mac_data:
            if item[num] in duplicate_check:
                continue
            else:
                duplicate_check.append(item[num])
                for x in all_vlan:
                    vlan = x
                    if vlan == "all":
                        c.execute("SELECT config FROM configs WHERE mac_address=?", (item[1],))
                    else:
                        vlan = int(x)
                        c.execute("SELECT config FROM configs WHERE mac_address=? AND vlan=? ", (item[1],vlan))
                    temp = c.fetchone()
                    if temp != None:
                        temp1 = temp[0]
                        print(temp1)
                        
                        if "switchport mode trunk" not in temp1:
                            config.append("\r\ndefault interface " + item[num]+"\r\n")
                            config.append("interface " + item[num]+"\r\n")
                            con.text_factory = str
                            config.append(temp1)
                        

        for elem in config:
            outfile.write(elem)

    con.commit()
    con.close()

    output = tk.Label(root, text = "Configuration Text File Created!")
    canvas.create_window(750, 285, window =output)

def getFileName ():
    global label2
    root.filename1 = filedialog.askopenfilename(initialdir = "/",title = "Select file",filetypes = (("text files","*.txt"),("all files","*.*")))
    label2 = tk.Label(root,text=root.filename1)
    canvas.create_window(250, 50, window =label2)

def getFileName2 ():
    global label3
    root.filename2 = filedialog.askopenfilename(initialdir = "/",title = "Select file",filetypes = (("text files","*.txt"),("all files","*.*")))
    label3 = tk.Label(root,text=root.filename2)
    canvas.create_window(750, 50, window =label3)

def getDatabase ():
    global label4
    root.filename3 = filedialog.askopenfilename(initialdir = "/",title = "Select file",filetypes = (("database files","*.db"),("all files","*.*")))
    label4 = tk.Label(root,text=root.filename3)
    canvas.create_window(750, 130, window =label4)

root = tk.Tk()

canvas = tk.Canvas(root, width = 1000, height = 300)
canvas.pack()
canvas.winfo_toplevel().title("MAC Configuration Script")

canvas.create_line(499,0,499,300)
canvas.create_line(500,0,500,300)
canvas.create_line(501,0,501,300)
canvas.pack()

button1 = tk.Button(text='Select Pre-Deployment Log', command=getFileName)
canvas.create_window(250, 20, window=button1)

output1 = tk.Label(root, text = "Save Database As:")
canvas.create_window(250, 100, window =output1)

database_input = tk.Entry()
canvas.create_window(250, 130, window=database_input)

button2 = tk.Button(text='Create Database', command=createDatabase)
canvas.create_window(250, 200, window=button2)



button3 = tk.Button(text='Select Post-Deployment Log', command=getFileName2)
canvas.create_window(750, 20, window=button3)

button4 = tk.Button(text='Select Database', command=getDatabase)
canvas.create_window(750, 100, window=button4)

output2 = tk.Label(root, text = "Save Config File As:")
canvas.create_window(650, 180, window =output2)

config_input = tk.Entry()
canvas.create_window(650, 210, window=config_input)

output3 = tk.Label(root, text = "VLANs")
canvas.create_window(850, 180, window =output3)

vlan_input = tk.Entry()
canvas.create_window(850, 210, window=vlan_input)

button5 = tk.Button(text='Create Configurations', command=createConfig)
canvas.create_window(750, 260, window=button5)

canvas.pack()

root.mainloop()