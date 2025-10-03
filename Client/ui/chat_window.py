"""
Chat window module for chat client.
"""
import tkinter as tk
from tkinter import scrolledtext, messagebox
from Chat.Client.network import ChatNetwork


class ChatWindow:
    
    def __init__(self, master: tk.Tk, host: str, port: int, id_token: str):
        self.master = master
        self.master.title('Chat Client')
        self.master.protocol('WM_DELETE_WINDOW', self.on_close)
        
        # Network
        self.network = ChatNetwork(host, port)
        self.network.set_receive_callback(self._on_message_received)
        
        self._setup_ui()
        self._connect_to_server(id_token)
        
    def _setup_ui(self):
        # Chat output area
        self.output = scrolledtext.ScrolledText(
            self.master, wrap=tk.WORD, state=tk.DISABLED, 
            width=60, height=20
        )
        self.output.grid(row=0, column=0, columnspan=4, padx=8, pady=8, sticky='nsew')

        # Connection settings row
        tk.Label(self.master, text='Host:').grid(row=1, column=0, padx=(8, 2), pady=8, sticky='w')
        self.entry_host = tk.Entry(self.master, width=15)
        self.entry_host.insert(0, self.network.host)
        self.entry_host.grid(row=1, column=1, padx=2, pady=8, sticky='w')

        tk.Label(self.master, text='Port:').grid(row=1, column=2, padx=(8, 2), pady=8, sticky='w')
        self.entry_port = tk.Entry(self.master, width=8)
        self.entry_port.insert(0, str(self.network.port))
        self.entry_port.grid(row=1, column=3, padx=2, pady=8, sticky='w')

        # Message input row
        self.entry_message = tk.Entry(self.master, width=50)
        self.entry_message.grid(row=2, column=0, padx=8, pady=8, sticky='ew')
        self.entry_message.bind('<Return>', lambda _e: self.send_message())

        self.button_send = tk.Button(self.master, text='Send', command=self.send_message)
        self.button_send.grid(row=2, column=1, padx=4, pady=8)

        self.button_connect = tk.Button(self.master, text='Connect', command=self.connect)
        self.button_connect.grid(row=2, column=2, padx=8, pady=8)

        # Grid weights
        self.master.rowconfigure(0, weight=1)
        self.master.columnconfigure(0, weight=1)
        
    def _connect_to_server(self, id_token: str):
        """Connect to server with authentication."""
        if self.network.connect(id_token):
            self.log(f'Connected to {self.network.host}:{self.network.port} (authenticated)')
        else:
            messagebox.showerror('Connection Error', 
                               f'Could not connect to {self.network.host}:{self.network.port}')
            self.master.destroy()
            
    def _on_message_received(self, message: str):
        self.master.after(0, self.log, message)
        
    def log(self, text: str):
        self.output.configure(state=tk.NORMAL)
        self.output.insert(tk.END, text + '\n')
        self.output.configure(state=tk.DISABLED)
        self.output.see(tk.END)

    def connect(self):
        if self.network.is_connected:
            return
            
        try:
            host = self.entry_host.get().strip()
            port = int(self.entry_port.get().strip())
        except ValueError:
            messagebox.showerror('Input Error', 'Please enter a valid port number')
            return
            
        if not host:
            messagebox.showerror('Input Error', 'Please enter a host address')
            return
            
        # Update network settings
        self.network.host = host
        self.network.port = port
        
        messagebox.showerror('Reconnect Error', 'Please restart the application to reconnect')

    def send_message(self):
        message = self.entry_message.get().strip()
        if not message:
            return
            
        if not self.network.is_connected:
            self.log('Not connected. Click Connect first.')
            return
            
        # Show message locally first
        self.output.configure(state=tk.NORMAL)
        self.output.insert(tk.END, "Me: " + message + "\n", "self")
        self.output.configure(state=tk.DISABLED)
        self.output.see(tk.END)

        # Send to server
        if not self.network.send_message(message):
            self.log('Error sending message')
            self.on_close()
            return
            
        # Clear input
        self.entry_message.delete(0, tk.END)

    def on_close(self):
        try:
            self.network.disconnect()
        finally:
            self.master.destroy()
