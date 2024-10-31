import os
import platform
import subprocess
import time
import tkinter as tk
from tkinter import ttk, filedialog
from datetime import datetime

def ping(host):
    param = '-n' if platform.system().lower() == 'windows' else '-c'
    command = ['ping', param, '1', host]
    start_time = time.time()
    result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    end_time = time.time()
    response_time = (end_time - start_time) * 1000  # Convert to milliseconds
    return result.returncode == 0, response_time

class PingApp:
    def __init__(self, root):
        self.root = root
        self.root.title("PingInfoView")
        
        self.hosts = ['google.com', 'yahoo.com', 'bing.com']
        self.interval = 5
        self.pinging = False
        self.file_path = None
        
        self.tree = ttk.Treeview(root, columns=('Host', 'Status', 'Response Time', 'Last Action Time'), show='headings')
        self.tree.heading('Host', text='Host')
        self.tree.heading('Status', text='Status')
        self.tree.heading('Response Time', text='Response Time (ms)')
        self.tree.heading('Last Action Time', text='Last Action Time')
        self.tree.pack(fill=tk.BOTH, expand=True)
        
        self.toggle_button = tk.Button(root, text="Start", command=self.toggle_pinging)
        self.toggle_button.pack(side=tk.LEFT, padx=10, pady=10)
        
        self.file_button = tk.Button(root, text="Select File", command=self.select_file)
        self.file_button.pack(side=tk.LEFT, padx=10, pady=10)
        
        self.interval_label = tk.Label(root, text="Ping Interval (seconds):")
        self.interval_label.pack(side=tk.LEFT, padx=10, pady=10)
        
        self.interval_entry = tk.Entry(root)
        self.interval_entry.insert(0, str(self.interval))
        self.interval_entry.pack(side=tk.LEFT, padx=10, pady=10)
        
        self.status_label = tk.Label(root, text="Current pinging subject: default ping setting")
        self.status_label.pack(side=tk.BOTTOM, padx=10, pady=10)
        
    def toggle_pinging(self):
        self.pinging = not self.pinging
        self.toggle_button.config(text="Stop" if self.pinging else "Start")
        if self.pinging:
            self.update_pings()
        
    def select_file(self):
        file_path = filedialog.askopenfilename(filetypes=[("Text files", "*.txt")])
        if file_path:
            self.file_path = file_path
            with open(file_path, 'r') as file:
                self.hosts = [line.strip() for line in file if line.strip()]
            self.status_label.config(text=f"Current pinging subject: {file_path}")
        else:
            self.file_path = None
            self.status_label.config(text="Current pinging subject: default ping setting")
        
    def update_pings(self):
        try:
            self.interval = int(self.interval_entry.get())
        except ValueError:
            self.interval = 5
            self.interval_entry.delete(0, tk.END)
            self.interval_entry.insert(0, str(self.interval))
        
        if self.pinging:
            for i in self.tree.get_children():
                self.tree.delete(i)
                
            for index, host in enumerate(self.hosts):
                success, response_time = ping(host)
                status = 'Success' if success else 'Failed'
                last_action_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                color = 'green' if success else 'red'
                font = ('', 10, 'bold')
                
                self.tree.insert('', 'end', values=(host, status, f"{response_time:.2f}", last_action_time),
                                 tags=(color,))
                
                self.tree.tag_configure('green', foreground='green', font=font)
                self.tree.tag_configure('red', foreground='red', font=font)
                
                if index % 2 == 0:
                    self.tree.tag_configure('even', background='#f0f0ff')
                    self.tree.item(self.tree.get_children()[-1], tags=('even', color))
                else:
                    self.tree.tag_configure('odd', background='#ffffff')
                    self.tree.item(self.tree.get_children()[-1], tags=('odd', color))
                
            self.root.after(self.interval * 1000, self.update_pings)

if __name__ == "__main__":
    root = tk.Tk()
    app = PingApp(root)
    root.mainloop()
