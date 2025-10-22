import tkinter as tk
from tkinter import scrolledtext, messagebox
from tkinter import ttk
from Chat.Client.network import ChatNetwork
from Chat.Client.ui.user_profile import UserProfileFrame
from Chat.Client.ui.find_friend import FindFriendFrame
from Chat.Client.ui.friends_tab import FriendsTabFrame
from Chat.Client.ui.private_chat import PrivateChatTab
from Chat.Client.ui.create_group import CreateGroupFrame
from Chat.Client.ui.group_chat import GroupsListFrame, GroupChatTab
from Chat.Client.ui import cmd_handlers as CMD


class ChatWindow:
    
    def __init__(self, master: tk.Tk, host: str, port: int, id_token: str, current_email: str | None = None):
        self.master = master
        self.master.title('Chat Client')
        self.master.protocol('WM_DELETE_WINDOW', self.on_close)
        
        # Network Information
        self.network = ChatNetwork(host, port)
        self.network.set_receive_callback(self._on_message_received)
        self.id_token = id_token
        self.current_user_email = (current_email or '').strip().lower() or None
        
        self._setup_ui()
        self._connect_to_server(id_token)

    # -------------------- UI setup --------------------
    def _setup_ui(self):
        # Root grid configuration
        self.master.rowconfigure(0, weight=1)
        self.master.columnconfigure(0, weight=1)

        top_frame = tk.Frame(self.master)
        top_frame.grid(row=0, column=0, padx=8, pady=8, sticky='nsew')
        top_frame.columnconfigure(0, weight=1)
        top_frame.rowconfigure(1, weight=1)

        user_box = tk.Frame(top_frame)
        user_box.grid(row=0, column=0, sticky='w', pady=(0, 4))
        tk.Label(user_box, text='User:').pack(side='left', padx=(0, 4))
        self.entry_username = tk.Entry(user_box, width=25)
        self.entry_username.insert(0, self.current_user_email or "Unknown")
        self.entry_username.configure(state='readonly')
        self.entry_username.pack(side='left')

        self.notebook = ttk.Notebook(top_frame)
        self.notebook.grid(row=1, column=0, sticky='nsew')
        self._demo_profile_loaded = False
        self._friends_loaded = False
        self._friends = []  # list of dicts {uid,email,displayName}
        self._incoming_requests = []  # list of dicts {requestId, fromUid, fromEmail, createdAt}
        self._refresh_req_job = None

        self.tab_chat = tk.Frame(self.notebook)
        self.notebook.add(self.tab_chat, text='Chat')

        self.output = scrolledtext.ScrolledText(
            self.tab_chat, wrap=tk.WORD, state=tk.DISABLED,
            width=60, height=18
        )
        self.output.grid(row=0, column=0, columnspan=4, padx=8, pady=8, sticky='nsew')

        # Connection settings row
        tk.Label(self.tab_chat, text='Host:').grid(row=1, column=0, padx=(8, 2), pady=8, sticky='w')
        self.entry_host = tk.Entry(self.tab_chat, width=15)
        self.entry_host.insert(0, self.network.host)
        self.entry_host.configure(state='readonly')
        self.entry_host.grid(row=1, column=1, padx=2, pady=8, sticky='w')

        tk.Label(self.tab_chat, text='Port:').grid(row=1, column=2, padx=(8, 2), pady=8, sticky='w')
        self.entry_port = tk.Entry(self.tab_chat, width=8,)
        self.entry_port.insert(0, str(self.network.port),)
        self.entry_port.configure(state='readonly')
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

        # --- Find friend tab ---
        self.tab_find = FindFriendFrame(self.notebook, on_search=self._search_friend_ui, on_send_request=self.send_friend_request)
        self.notebook.add(self.tab_find, text='Tìm bạn')

        self._found_user_email = None

        # --- Profile tab ---
        self.tab_profile = UserProfileFrame(self.notebook, on_accept=self.accept_friend_request, on_reject=self.reject_friend_request, on_refresh=self._refresh_requests)
        self.notebook.add(self.tab_profile, text='Profile')
        # Initialize friend requests list empty; can be set via set_friend_requests later
        self.tab_profile.set_friend_requests([])
        
        # Bind to load demo data on first open of Profile tab
        self.notebook.bind('<<NotebookTabChanged>>', self._on_tab_changed)

        # --- Friends tab ---
        self.tab_friends = FriendsTabFrame(self.notebook, on_open_dm=self._open_dm_from_friend, on_refresh=lambda: self.network.send_command({ 'type': 'LIST_FRIENDS' }))
        self.notebook.add(self.tab_friends, text='Bạn bè')
        
        # --- Create Group tab ---
        self.tab_create_group = CreateGroupFrame(self.notebook, on_create_group=self._create_group, on_refresh_friends=lambda: self.network.send_command({ 'type': 'LIST_FRIENDS' }))
        self.notebook.add(self.tab_create_group, text='Tạo nhóm')
        
        # --- Groups tab ---
        self.tab_groups = GroupsListFrame(self.notebook, on_open_group=self._open_group_chat, on_create_group=self._show_create_group_tab)
        self.notebook.add(self.tab_groups, text='Nhóm chat')
        
        # Group chat tabs storage
        self._group_tabs = {}
        self._groups = []
        
    def _connect_to_server(self, id_token: str):
        """Connect to server with authentication."""
        success, err = self.network.connect(id_token)
        if success:
            self.log(f'Connected to {self.network.host}:{self.network.port} (authenticated)')
            try:
                self.network.send_command({ 'type': 'LIST_FRIENDS' })
            except Exception:
                pass
        else:
            messagebox.showerror('Connection Error', err or f'Could not connect to {self.network.host}:{self.network.port}')
            
    def _on_message_received(self, message: str):
        if message.startswith('CMD '):
            try:
                import json as _json
                obj = _json.loads(message[4:])
            except Exception:
                return
            msg_type = (obj.get('type') or '').upper()
            if msg_type == 'FIND_USER_RESULT':
                CMD.handle_find_user_result(self, obj)
                return
            if msg_type == 'FRIENDS':
                CMD.handle_friends(self, obj)
                return
            if msg_type == 'FRIEND_REQUEST_SENT':
                CMD.handle_friend_request_sent(self, obj)
                return
            if msg_type == 'FRIEND_REQUEST_ACCEPTED':
                CMD.handle_friend_request_accepted(self, obj)
                return
            if msg_type == 'FRIEND_REQUEST_REJECTED':
                CMD.handle_friend_request_rejected(self, obj)
                return
            if msg_type == 'FRIEND_REQUESTS':
                CMD.handle_friend_requests(self, obj)
                return
            if msg_type == 'DM':
                CMD.handle_dm(self, obj)
                return
            if msg_type == 'DM_DELIVERED':
                CMD.handle_dm_delivered(self, obj)
                return
            if msg_type == 'DM_HISTORY':
                CMD.handle_dm_history(self, obj)
                return
            if msg_type == 'GROUPS':
                CMD.handle_groups(self, obj)
                return
            if msg_type == 'GROUP_CREATED':
                CMD.handle_group_created(self, obj)
                return
            if msg_type == 'GROUP_MESSAGE':
                CMD.handle_group_message(self, obj)
                return
            if msg_type == 'GROUP_HISTORY':
                CMD.handle_group_history(self, obj)
                return
            self.master.after(0, self.log, message)
            return
        self.master.after(0, self.log, message)
    
    def _on_tab_changed(self, _event=None):
        current = self.notebook.select()
        if current == str(self.tab_profile):
            self._refresh_requests()
        if current == str(self.tab_friends):
            try:
                self.network.send_command({ 'type': 'LIST_FRIENDS' })
            except Exception:
                pass
        if current == str(self.tab_groups):
            try:
                self.network.send_command({ 'type': 'LIST_GROUPS' })
            except Exception:
                pass

    def _refresh_requests(self):
        try:
            self.network.send_command({ 'type': 'FRIEND_REQUESTS' })
        except Exception:
            pass
        # Schedule next refresh in 5 seconds
        try:
            self._refresh_req_job = self.master.after(5000, self._refresh_requests)
        except Exception:
            self._refresh_req_job = None
        
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

    # -------------------- Friend features --------------------
    def _search_friend_ui(self, email_input: str):
        email = (email_input or '').strip()
        if not email:
            messagebox.showwarning('Thiếu thông tin', 'Vui lòng nhập email Gmail.')
            return
        # Send command to server to find user by email via Firebase Admin
        sent = self.network.send_command({ 'type': 'FIND_USER', 'email': email })
        if not sent:
            messagebox.showerror('Lỗi mạng', 'Không thể gửi yêu cầu tìm kiếm đến server.')

    def send_friend_request(self):
        if not self._found_user_email:
            messagebox.showwarning('Chưa chọn người dùng', 'Hãy tìm và chọn người dùng trước.')
            return
        # Send to server
        sent = self.network.send_command({ 'type': 'SEND_FRIEND_REQUEST', 'toEmail': self._found_user_email })
        if not sent:
            messagebox.showerror('Lỗi mạng', 'Không thể gửi yêu cầu kết bạn đến server.')
            return

    
    def _open_dm_from_friend(self, friend):
        if not hasattr(self, '_dm_tabs'):
            self._dm_tabs = {}
        key = friend.get('uid') or friend.get('email') or str(friend)
        if key in self._dm_tabs:
            try:
                self._dm_tabs[key].focus()
            except Exception:
                pass
            return
        tab = PrivateChatTab(self.notebook, friend, on_send=lambda f, text, _t: self._send_dm_raw(f, text), on_load_history=self._load_thread_for_friend)
        self._dm_tabs[key] = tab

    def _send_dm_raw(self, friend, text: str):
        to_uid = friend.get('uid') or ''
        client_msg_id = f"{self.master.winfo_id()}-{to_uid}-{len(text)}"
        sent = self.network.send_command({ 'type': 'SEND_DM', 'toUid': to_uid, 'text': text, 'clientMsgId': client_msg_id })
        if not sent:
            self.log('Không thể gửi tin nhắn (network)')
            return

    def _find_dm_tab_by_thread_or_uid(self, thread_id: str | None, from_uid: str | None):
        if not hasattr(self, '_dm_tabs'):
            self._dm_tabs = {}
        if thread_id:
            for key, tab in self._dm_tabs.items():
                friend = getattr(tab, 'friend', None) or {}
                if friend.get('threadId') == thread_id:
                    return tab
        if from_uid:
            for key, tab in self._dm_tabs.items():
                friend = getattr(tab, 'friend', None) or {}
                if friend.get('uid') == from_uid:
                    return tab
        return None

    
        
    def _load_thread_for_friend(self, friend):
        peer_uid = friend.get('uid') or ''
        if not peer_uid:
            return
        try:
            self.network.send_command({ 'type': 'LOAD_THREAD', 'peerUid': peer_uid, 'limit': 50 })
        except Exception:
            pass


    def accept_friend_request(self, requester_email=None):
        if requester_email is None:
            selection = self.tab_profile.get_selected_request()
            if not selection:
                return
            requester_email = selection
        # include requestId/fromUid if available for efficient server handling
        req = next((r for r in (self._incoming_requests or []) if (r.get('fromEmail') == requester_email) or (r.get('fromUid') and r.get('fromUid') == requester_email)), None)
        payload = { 'type': 'ACCEPT_REQUEST' }
        if req:
            if req.get('fromUid'):
                payload['fromUid'] = req['fromUid']
            if req.get('requestId'):
                payload['requestId'] = req['requestId']
            if req.get('fromEmail'):
                payload['fromEmail'] = req['fromEmail']
        else:
            payload['fromEmail'] = requester_email
        sent = self.network.send_command(payload)
        if not sent:
            messagebox.showerror('Lỗi mạng', 'Không thể gửi yêu cầu chấp nhận đến server.')
            return

    def reject_friend_request(self, requester_email=None):
        if requester_email is None:
            selection = self.tab_profile.get_selected_request()
            if not selection:
                return
            requester_email = selection
        req = next((r for r in (self._incoming_requests or []) if (r.get('fromEmail') == requester_email) or (r.get('fromUid') and r.get('fromUid') == requester_email)), None)
        payload = { 'type': 'REJECT_REQUEST' }
        if req:
            if req.get('fromUid'):
                payload['fromUid'] = req['fromUid']
            if req.get('requestId'):
                payload['requestId'] = req['requestId']
            if req.get('fromEmail'):
                payload['fromEmail'] = req['fromEmail']
        else:
            payload['fromEmail'] = requester_email
        sent = self.network.send_command(payload)
        if not sent:
            messagebox.showerror('Lỗi mạng', 'Không thể gửi yêu cầu từ chối đến server.')
            return

    

    def set_friend_requests(self, requester_emails):
        self.tab_profile.set_friend_requests(requester_emails)

    # -------------------- Group chat features --------------------
    def _create_group(self, group_name: str, selected_friends: list):
        """Create a new group"""
        if not group_name or not selected_friends:
            messagebox.showwarning('Thiếu thông tin', 'Vui lòng nhập tên nhóm và chọn bạn bè.')
            return
        
        # Prepare member UIDs
        member_uids = [friend.get('uid', '') for friend in selected_friends if friend.get('uid')]
        
        if not member_uids:
            messagebox.showwarning('Lỗi', 'Không có thành viên hợp lệ được chọn.')
            return
        
        # Send create group command
        sent = self.network.send_command({
            'type': 'CREATE_GROUP',
            'name': group_name,
            'memberUids': member_uids
        })
        
        if not sent:
            messagebox.showerror('Lỗi mạng', 'Không thể gửi yêu cầu tạo nhóm đến server.')
            return
        
        messagebox.showinfo('Thành công', f'Nhóm "{group_name}" đã được tạo thành công!')
        
        # Switch to groups tab and refresh
        self.notebook.select(self.tab_groups)
        try:
            self.network.send_command({ 'type': 'LIST_GROUPS' })
        except Exception:
            pass

    def _show_create_group_tab(self):
        """Switch to create group tab"""
        self.notebook.select(self.tab_create_group)

    def _open_group_chat(self, group_data):
        """Open a group chat"""
        group_id = group_data.get('id', '')
        if not group_id:
            return
        
        # Check if group chat tab already exists
        if group_id in self._group_tabs:
            try:
                self._group_tabs[group_id].focus()
            except Exception:
                pass
            return
        
        # Create new group chat tab
        tab = GroupChatTab(
            self.notebook,
            group_data,
            on_send_message=lambda gid, text: self._send_group_message(gid, text),
            on_load_history=lambda gid: self._load_group_history(gid)
        )
        
        # Add tab to notebook
        tab_name = f"Nhóm: {group_data.get('name', 'Unknown')}"
        self.notebook.add(tab, text=tab_name)
        self._group_tabs[group_id] = tab
        
        # Switch to the new tab
        self.notebook.select(tab)

    def _send_group_message(self, group_id: str, text: str):
        """Send a message to a group"""
        if not group_id or not text:
            return
        
        sent = self.network.send_command({
            'type': 'SEND_GROUP_MESSAGE',
            'groupId': group_id,
            'text': text
        })
        
        if not sent:
            self.log('Không thể gửi tin nhắn nhóm (network)')

    def _load_group_history(self, group_id: str):
        """Load group chat history"""
        if not group_id:
            return
        
        try:
            self.network.send_command({
                'type': 'LOAD_GROUP_HISTORY',
                'groupId': group_id,
                'limit': 50
            })
        except Exception:
            pass

    def set_groups(self, groups):
        """Set the list of groups"""
        self._groups = groups or []
        self.tab_groups.set_groups(groups)

    def add_group_message(self, group_id: str, sender: str, message: str, sender_uid: str = None):
        """Add a received group message to the appropriate tab"""
        if group_id in self._group_tabs:
            self._group_tabs[group_id].add_message(sender, message, sender_uid)

    def load_group_messages(self, group_id: str, messages: list):
        """Load group messages into the appropriate tab"""
        if group_id in self._group_tabs:
            self._group_tabs[group_id].load_messages(messages)

    def on_close(self):
        try:
            self.network.disconnect()
        finally:
            self.master.destroy()
