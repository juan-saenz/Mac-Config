import tkinter as tk
import sqlite3
from tkinter import filedialog
from tkinter import ttk
#from ttkthemes import ThemedStyle

LARGE_FONT= ("Verdana", 20)
db_name = ""
file = ""
vlan = ""
format_dic = {"Catalyst 4500 L3 Switch Software":1,
                "C3750 Software":2, 
                "C2960 Software":2,
                "C2960X Software":2, 
                "Catalyst L3 Switch Software":2,
                "C3750E Software":2, 
                "C3500XL Software":2, 
                "C3560 Software":2}

# initializes GUI Application
class App(tk.Tk):

    def __init__(self, *args, **kwargs):
        tk.Tk.__init__(self, *args, **kwargs)

        tk.Tk.wm_title(self, "Configuration Script")

        container = ttk.Frame(self)
        container.pack(side="top", fill="both", expand = True)

        container.grid_rowconfigure(0, weight=1)
        container.grid_columnconfigure(0, weight=1)
        self.frames = {}

        # creates "pages"
        for F in (StartPage, PageOne, PageTwo):

            frame = F(container, self)
            self.frames[F] = frame

            frame.grid(row=0, column=0, sticky="nsew")

        self.show_frame(StartPage)

    def show_frame(self, cont):
        frame = self.frames[cont]
        frame.tkraise()
  
class StartPage(tk.Frame):

    # initializes the main page
    def __init__(self, parent, controller):
        ttk.Frame.__init__(self,parent)

        label = ttk.Label(self, text="MAC Configuration Script", font=LARGE_FONT)
        label.pack(pady=10,padx=10)

        button = ttk.Button(self, text="Pre-Deployment", command=lambda: controller.show_frame(PageOne))
        button.place(x=100,y=100)

        button2 = ttk.Button(self, text="Post-Deployment", command=lambda: controller.show_frame(PageTwo))
        button2.place(x=300,y=100)

class PageOne(tk.Frame):

    # initializes the Pre-Deployment page
    def __init__(self, parent, controller):
        ttk.Frame.__init__(self, parent)
        
        label = ttk.Label(self, text="Create Database",font=LARGE_FONT)
        label.pack(pady=10,padx=10)
        
        global canvas
        canvas = tk.Canvas(self, width = 500, height = 300, highlightthickness=0)
        canvas.pack()
        
        button1 = ttk.Button(self, text='Select Pre-Deployment Log', command=lambda: self.getFileName())
        canvas.create_window(250, 20, window=button1)

        output1 = ttk.Label(self, text = "Save Database As:")
        canvas.create_window(250, 100, window=output1)

        global database_input
        database_input = ttk.Entry(self)
        canvas.create_window(250, 130, window=database_input)

        button2 = ttk.Button(self, text='Create Database', command=lambda: self.createDatabase())
        canvas.create_window(250, 180, window=button2)

        button3 = ttk.Button(self, text="Back to Main", command=lambda: controller.show_frame(StartPage))
        canvas.create_window(60, 280, window=button3)

    # returns filename
    def getFileName (self):
        global label2
        self.filename1 = filedialog.askopenfilename(initialdir = "/",title = "Select file",filetypes = (("text files","*.txt"),("all files","*.*")))
        label2 = ttk.Label(self, text=self.filename1)
        canvas.create_window(250, 50, window=label2)

    # database is created with filename selected
    def createDatabase (self):
        file = self.filename1
        db_name = database_input.get()
        con = sqlite3.connect(db_name+".db")
        c = con.cursor()

        mac_data = []
        ports = []
        version = []
        always_print = False
        format_type = 0

        # reads for version of selected log
        with open(file) as infile:
            for line in infile:
                if "#sh ver" in line:
                    always_print = True
                if "Compiled" in line:
                    always_print = False
                if always_print == True:
                    version.append(line)
        
        # parses file depending on the type of cisco log
        for j in format_dic:
            for k in version:
                if j in k:
                    format_type = format_dic[j]
                    ios = j
                    if format_type == 1:
                        i=-5
                    if format_type == 2:
                        i=-6

        # parses sh mac address table into variable mac_data
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

        # creates sqlite db
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

        print("*** Pre Deploy Log ***")   
        print("IOS Image Found: " + ios)
        print("Format Type " + str(format_type))
        print("MAC Addresses Found: "+ str(i))
        true_mac_counter=0
        #print(mac_data)
        for r in mac_data:
            if format_type == 2:
                if r[x] != "CPU":
                    true_mac_counter += 1
                    ports.append(r[x])
                    # appends ports of mac_data one by one into database
                    c.execute("INSERT INTO configs VALUES ('{}', '{}', '{}')".format(r[1], r[x], r[0]))
            else:
                true_mac_counter += 1
                ports.append(r[x])
                c.execute("INSERT INTO configs VALUES ('{}', '{}', '{}')".format(r[1], r[x], r[0]))
        
        print("MAC Addresses added to Database: "+ str(true_mac_counter))
        con.commit()

        found_port = False
        config_list = []
        c.execute("alter table configs add column config 'text'")
        con.commit()
        temp = ""

        # adds configs from ports found in mac address table and adds to database
        for port in ports:
            found_port = False
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
                elif port.startswith('Fi'):
                    port2 = port.replace('Fi', 'FiveGigabitEthernet')
                    temp = "interface " + port2
                elif port.startswith('Te'):
                    port2 = port.replace('Te', 'TenGigabitEthernet')
                    temp = "interface " + port2
                elif port.startswith('Twe'):
                    port2 = port.replace('Twe', 'TwentyFiveGigE')
                    temp = "interface " + port2

            # finds interface from port and appends to database
            with open(file) as infile:
                for line in infile:
                    templine = line.strip()
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

        output = ttk.Label(self, text = "Database Created!")
        canvas.create_window(250, 210, window =output)
        
class PageTwo(tk.Frame):

    # initializes post deployment page
    def __init__(self, parent, controller):
        ttk.Frame.__init__(self, parent)

        label = ttk.Label(self, text="Create Configurations", font=LARGE_FONT)
        label.pack(pady=10,padx=10)

        global canvas2
        canvas2 = tk.Canvas(self, width = 500, height = 300, highlightthickness=0)
        canvas2.pack()

        button1 = ttk.Button(self, text='Select Post-Deployment Log', command=lambda: self.getFileName2())
        canvas2.create_window(250, 20, window=button1)

        button2 = ttk.Button(self, text='Select Database', command=lambda: self.getDatabase())
        canvas2.create_window(250, 100, window=button2)

        output1 = ttk.Label(self, text = "Save Config File As:")
        canvas2.create_window(100, 180, window =output1)

        global config_input
        config_input = ttk.Entry(self)
        canvas2.create_window(100, 210, window=config_input)

        output2 = ttk.Label(self, text = "VLANs")
        canvas2.create_window(300, 180, window =output2)

        global vlan_input
        vlan_input = ttk.Entry(self)
        canvas2.create_window(300, 210, window=vlan_input)

        global checkbox1
        checkbox1 = ttk.Checkbutton(self, text = 'Trunk Ports', takefocus=0)
        canvas2.create_window(450, 210, window =checkbox1)

        button3 = ttk.Button(self, text='Create Configurations', command=lambda: self.createConfig())
        canvas2.create_window(250, 250, window=button3)

        button4 = ttk.Button(self, text='Back to Main', command=lambda: controller.show_frame(StartPage))
        canvas2.create_window(60, 280, window=button4)

    # grabs filename selected within this page
    def getFileName2 (self):
        global label3
        self.filename2 = filedialog.askopenfilename(initialdir = "/",title = "Select file",filetypes = (("text files","*.txt"),("all files","*.*")))
        label3 = ttk.Label(self,text=self.filename2)
        canvas2.create_window(250, 50, window=label3)

    # grabs databse selected within this page
    def getDatabase (self):
        global label4
        self.filename3 = filedialog.askopenfilename(initialdir = "/",title = "Select file",filetypes = (("database files","*.db"),("all files","*.*")))
        label4 = ttk.Label(self,text=self.filename3)
        canvas2.create_window(250, 130, window =label4)

    # creates txt file from selected options
    def createConfig (self):
        file = self.filename2
        db_name = self.filename3
        all_vlan = vlan_input.get().split(',')
        con = sqlite3.connect(db_name)
        c = con.cursor()

        mac_data = []
        version = []
        always_print = False
        format_type = 0
        trunkport = False

        # reads for version of selected log
        with open(file) as infile:
            for line in infile:
                if "sh ver" in line:
                    always_print = True
                if "Compiled" in line:
                    always_print = False
                if always_print == True:
                    version.append(line)

        # parses file depending on the type of cisco log
        for j in format_dic:
            for k in version:
                if j in k:
                    format_type = format_dic[j]
                    ios = j
                    if format_type == 1:
                        i=-5
                    if format_type == 2:
                        i=-6

        print("Format type: " +str(format_type))

        # parses sh mac address table into variable mac_data
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

        if format_type == 1:
            mac_data = mac_data[4:]
            mac_data = mac_data[:-1]
            num=4
        if format_type == 2:
            num=3
            mac_data = mac_data[7:]
     
        print("*** Post Deploy Log ***")   
        print("IOS Image Found: " + ios + ": Format Type " + str(format_type))
        fileout = config_input.get()
        config = []
        duplicate_check = []

        commands_not_wanted = ['switchport trunk encapsulation dot1q', 'macro description cisco-phone', 'tx-queue',
                            'bandwidth percent', 'priority high', 'shape percent']
        counter = 0
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
                            if checkbox1.instate(['selected']) == True:
                                config.append("\r\ndefault interface " + item[num]+"\r\n")
                                config.append("interface " + item[num]+"\r\n")
                                con.text_factory = str
                                config.append(temp1)
                                counter += 1
                                if counter % 10 == 0:
                                    config.append("\n\n\n\n\n")
                            else:
                                if "switchport mode trunk" not in temp1:
                                    config.append("\r\ndefault interface " + item[num]+"\r\n")
                                    config.append("interface " + item[num]+"\r\n")
                                    con.text_factory = str
                                    config.append(temp1)
                                    counter += 1
                                    if counter % 10 == 0:
                                        config.append("\n\n\n\n")
            #print(config)
            for elem in config:
                outfile.write(elem)

        print("\nFound " + str(counter) + " matching ports")
        con.commit()
        con.close()

        output = ttk.Label(self, text = "Configuration Text File Created!")
        canvas2.create_window(250, 285, window =output)

app = App()
app.mainloop()