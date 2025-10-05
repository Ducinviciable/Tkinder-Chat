"""
Chat window module for chat client.
"""
import tkinter as tk
from tkinter import scrolledtext, messagebox
from tkinter import ttk
from Chat.Client.network import ChatNetwork
from Chat.Client.ui.user_profile import UserProfileFrame


class ChatWindow:
    
    def __init__(self, master: tk.Tk, host: str, port: int, id_token: str, current_email: str | None = None):
        self.master = master
        self.master.title('Chat Client')
        self.master.protocol('WM_DELETE_WINDOW', self.on_close)
        
        # Network
        self.network = ChatNetwork(host, port)
        self.network.set_receive_callback(self._on_message_received)
        # Keep the id_token so reconnects can reuse it
        self.id_token = id_token
        # Current user's email for friend features
        self.current_user_email = (current_email or '').strip().lower() or None
        
        self._setup_ui()
        self._connect_to_server(id_token)
        
    def _setup_ui(self):
        # Root grid configuration
        self.master.rowconfigure(0, weight=1)
        self.master.columnconfigure(0, weight=1)

        # Main notebook for tabs
        self.notebook = ttk.Notebook(self.master)
        self.notebook.grid(row=0, column=0, padx=8, pady=8, sticky='nsew')

        # --- Chat tab ---
        self.tab_chat = tk.Frame(self.notebook)
        self.notebook.add(self.tab_chat, text='Chat')

        # Chat output area
        self.output = scrolledtext.ScrolledText(
            self.tab_chat, wrap=tk.WORD, state=tk.DISABLED,
            width=60, height=18
        )
        self.output.grid(row=0, column=0, columnspan=4, padx=8, pady=8, sticky='nsew')

        # Connection settings row
        tk.Label(self.tab_chat, text='Host:').grid(row=1, column=0, padx=(8, 2), pady=8, sticky='w')
        self.entry_host = tk.Entry(self.tab_chat, width=15)
        self.entry_host.insert(0, self.network.host)
        self.entry_host.grid(row=1, column=1, padx=2, pady=8, sticky='w')

        tk.Label(self.tab_chat, text='Port:').grid(row=1, column=2, padx=(8, 2), pady=8, sticky='w')
        self.entry_port = tk.Entry(self.tab_chat, width=8)
        self.entry_port.insert(0, str(self.network.port))
        self.entry_port.grid(row=1, column=3, padx=2, pady=8, sticky='w')

        # Message input row
        self.entry_message = tk.Entry(self.tab_chat, width=50)
        self.entry_message.grid(row=2, column=0, padx=8, pady=8, sticky='ew')
        self.entry_message.bind('<Return>', lambda _e: self.send_message())

        self.button_send = tk.Button(self.tab_chat, text='Send', command=self.send_message)
        self.button_send.grid(row=2, column=1, padx=4, pady=8)

        self.button_connect = tk.Button(self.tab_chat, text='Connect', command=self.connect)
        self.button_connect.grid(row=2, column=2, padx=8, pady=8)

        # Grid weights for chat tab
        self.tab_chat.rowconfigure(0, weight=1)
        self.tab_chat.columnconfigure(0, weight=1)

        # --- Tìm bạn tab ---
        self.tab_find = tk.Frame(self.notebook)
        self.notebook.add(self.tab_find, text='Tìm bạn')

        # Search instruction
        tk.Label(self.tab_find, text='Nhập email Gmail:').grid(row=0, column=0, padx=8, pady=(12, 4), sticky='w')
        self.entry_search_email = tk.Entry(self.tab_find, width=40)
        self.entry_search_email.grid(row=1, column=0, padx=8, pady=4, sticky='w')
        self.entry_search_email.bind('<Return>', lambda _e: self.search_friend())

        self.btn_search = tk.Button(self.tab_find, text='Tìm', command=self.search_friend)
        self.btn_search.grid(row=1, column=1, padx=8, pady=4, sticky='w')

        # Result card (hidden initially)
        self.result_card = tk.Frame(self.tab_find, relief=tk.GROOVE, borderwidth=1)
        self.result_card.grid(row=2, column=0, columnspan=2, padx=8, pady=(8, 12), sticky='ew')
        self.result_card.columnconfigure(0, weight=1)
        self.label_found_name = tk.Label(self.result_card, text='', font=('TkDefaultFont', 10, 'bold'))
        self.label_found_name.grid(row=0, column=0, padx=8, pady=(8, 2), sticky='w')
        self.label_found_email = tk.Label(self.result_card, text='', fg='gray')
        self.label_found_email.grid(row=1, column=0, padx=8, pady=(0, 8), sticky='w')
        self.btn_send_request = tk.Button(self.result_card, text='Gửi yêu cầu kết bạn', command=self.send_friend_request, state=tk.DISABLED)
        self.btn_send_request.grid(row=0, column=1, rowspan=2, padx=8, pady=8, sticky='e')
        # Hide card initially
        self.result_card.grid_remove()

        # Placeholder to keep found user email
        self._found_user_email = None

        # --- Profile tab ---
        self.tab_profile = UserProfileFrame(self.notebook, on_accept=self.accept_friend_request, on_reject=self.reject_friend_request)
        self.notebook.add(self.tab_profile, text='Profile')
        # Initialize friend requests list empty; can be set via set_friend_requests later
        self.tab_profile.set_friend_requests([])
        
    def _connect_to_server(self, id_token: str):
        """Connect to server with authentication."""
        success, err = self.network.connect(id_token)
        if success:
            self.log(f'Connected to {self.network.host}:{self.network.port} (authenticated)')
        else:
            # Show the detailed error and keep window open so user can edit host/port
            messagebox.showerror('Connection Error', err or f'Could not connect to {self.network.host}:{self.network.port}')
            
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
            
        # Update network settings and attempt to connect
        self.network.host = host
        self.network.port = port

        # Try to reconnect using the stored auth token
        success, err = self.network.connect(self.id_token or '')
        if success:
            self.log(f'Reconnected to {host}:{port}')
        else:
            messagebox.showerror('Reconnect Error', err or f'Could not reconnect to {host}:{port}')

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

    # -------------------- Friend features (stubs) --------------------
    def search_friend(self):
        email = (self.entry_search_email.get() or '').strip()
        if not email:
            messagebox.showwarning('Thiếu thông tin', 'Vui lòng nhập email Gmail.')
            return
        # TODO: integrate with Firebase to check user existence by email
        # For now, simulate: treat any email containing '@' as existing
        if '@' in email:
            self._found_user_email = email
            # Derive a display name from email prefix as placeholder
            display_name = email.split('@', 1)[0]
            self.label_found_name.configure(text=display_name)
            self.label_found_email.configure(text=email)
            # Disable sending to self
            if self.current_user_email and email.strip().lower() == self.current_user_email:
                self.btn_send_request.configure(state=tk.DISABLED)
            else:
                self.btn_send_request.configure(state=tk.NORMAL)
            self.result_card.grid()  # show card
            messagebox.showinfo('Tìm bạn', f'Đã tìm thấy người dùng: {email}')
        else:
            self._found_user_email = None
            self.btn_send_request.configure(state=tk.DISABLED)
            self.result_card.grid_remove()
            messagebox.showerror('Tìm bạn', 'Người dùng không tồn tại.')

    def send_friend_request(self):
        if not self._found_user_email:
            messagebox.showwarning('Chưa chọn người dùng', 'Hãy tìm và chọn người dùng trước.')
            return
        # TODO: integrate with Firebase to create a friend request
        messagebox.showinfo('Yêu cầu kết bạn', f'Đã gửi yêu cầu kết bạn đến {self._found_user_email}.')
        self.btn_send_request.configure(state=tk.DISABLED)
        self.result_card.grid_remove()

    def accept_friend_request(self):
        selection = self.tab_profile.get_selected_request()
        if not selection:
            return
        requester_email = selection
        # TODO: integrate with Firebase to accept the friend request
        messagebox.showinfo('Kết bạn', f'Đã chấp nhận lời mời từ {requester_email}.')
        self.tab_profile.remove_selected_request()

    def reject_friend_request(self):
        selection = self.tab_profile.get_selected_request()
        if not selection:
            return
        requester_email = selection
        # TODO: integrate with Firebase to reject the friend request
        messagebox.showinfo('Kết bạn', f'Đã từ chối lời mời từ {requester_email}.')
        self.tab_profile.remove_selected_request()

    def set_friend_requests(self, requester_emails):
        """Replace the list of incoming friend requests shown in Profile."""
        self.tab_profile.set_friend_requests(requester_emails)

    def on_close(self):
        try:
            self.network.disconnect()
        finally:
            self.master.destroy()
