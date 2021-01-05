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

def createDatabase ():
    file = root.filename1
    db_name = database_input.get()
    con = sqlite3.connect(db_name+".db")
    c = con.cursor()

    mac_data = []
    ports = []
    always_print = False
    i=-5

    with open(file) as infile:
        for line in infile:
            if "sh mac address" in line:
                always_print = True
            if "Multicast Entries" in line:
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

    mac_data = mac_data[4:]
    print(i)
    for r in mac_data[:-1]:
        ports.append(r[4])
        c.execute("INSERT INTO configs VALUES ('{}', '{}', '{}')".format(r[1], r[4], r[0]))
        
    con.commit()

    found_port = False
    config_list = []
    c.execute("alter table configs add column config 'text'")
    con.commit()

    for port in ports:
        temp = "interface " + port
        with open(file) as infile:
            for line in infile:
                #print line
                #temp_line.append(line)
                #print temp_line
                templine = line.strip()
                if temp == templine:
                    found_port = True
                if line.startswith("!"):
                    found_port = False
                if found_port == True:
                    if line == "":
                        continue
                    else:
                        if(line.startswith("interface " + port)):
                            continue
                        config_list.append(line)
            port_config = "".join(config_list)
        
            c.execute("UPDATE configs SET config = ? WHERE port = ?", (port_config , port)) 
            config_list = []   
    
    con.commit()
    con.close()

    output = tk.Label(root, text = "Database Created!")
    canvas.create_window(200, 230, window =output)

def createConfig ():
    file = root.filename2
    db_name = root.filename3
    all_vlan = vlan_input.get().split(',')
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
    fileout = config_input.get()
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
                for x in all_vlan:
                    vlan = x
                    if vlan == "all":
                        c.execute("SELECT config FROM configs WHERE mac_address=?", (item[1],))
                    else:
                        vlan = int(x)
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

    con.commit()
    con.close()

    output = tk.Label(root, text = "Configuration Text File Created!")
    canvas.create_window(600, 285, window =output)

def getFileName ():
    root.filename1 = filedialog.askopenfilename(initialdir = "/",title = "Select file",filetypes = (("text files","*.txt"),("all files","*.*")))
    label2 = tk.Label(root,text=root.filename1)
    canvas.create_window(200, 50, window =label2)

def getFileName2 ():
    root.filename2 = filedialog.askopenfilename(initialdir = "/",title = "Select file",filetypes = (("text files","*.txt"),("all files","*.*")))
    label3 = tk.Label(root,text=root.filename2)
    canvas.create_window(600, 50, window =label3)

def getDatabase ():
    root.filename3 = filedialog.askopenfilename(initialdir = "/",title = "Select file",filetypes = (("database files","*.db"),("all files","*.*")))
    label4 = tk.Label(root,text=root.filename3)
    canvas.create_window(600, 130, window =label4)

root = tk.Tk()

canvas = tk.Canvas(root, width = 800, height = 300)
canvas.pack()
canvas.winfo_toplevel().title("MAC Configuration Script")

canvas.create_line(400,0,400,300)
canvas.pack()

button1 = tk.Button(text='Select Pre-Deployment Log', command=getFileName)
canvas.create_window(200, 20, window=button1)

output1 = tk.Label(root, text = "Save Database As:")
canvas.create_window(200, 100, window =output1)

database_input = tk.Entry()
canvas.create_window(200, 130, window=database_input)

button2 = tk.Button(text='Create Database', command=createDatabase)
canvas.create_window(200, 200, window=button2)



button3 = tk.Button(text='Select Post-Deployment Log', command=getFileName2)
canvas.create_window(600, 20, window=button3)

button4 = tk.Button(text='Select Database', command=getDatabase)
canvas.create_window(600, 100, window=button4)

output2 = tk.Label(root, text = "Save Config File As:")
canvas.create_window(500, 180, window =output2)

config_input = tk.Entry()
canvas.create_window(500, 210, window=config_input)

listbox = tk.Listbox()
listbox.insert(1,"America")

output3 = tk.Label(root, text = "VLANs")
canvas.create_window(700, 180, window =output3)

vlan_input = tk.Entry()
canvas.create_window(700, 210, window=vlan_input)

button5 = tk.Button(text='Create Configurations', command=createConfig)
canvas.create_window(600, 260, window=button5)



root.mainloop()