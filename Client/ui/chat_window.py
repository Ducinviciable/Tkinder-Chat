import tkinter as tk
from tkinter import scrolledtext, messagebox
from tkinter import ttk
from Chat.Client.network import ChatNetwork
from Chat.Client.ui.user_profile import UserProfileFrame
from Chat.Client.ui.find_friend import FindFriendFrame
from Chat.Client.ui.friends_tab import FriendsTabFrame


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
                self._handle_find_user_result(obj)
                return
            if msg_type == 'FRIENDS':
                self._handle_friends(obj)
                return
            if msg_type == 'FRIEND_REQUEST_SENT':
                self._handle_friend_request_sent(obj)
                return
            if msg_type == 'FRIEND_REQUEST_ACCEPTED':
                self._handle_friend_request_accepted(obj)
                return
            if msg_type == 'FRIEND_REQUEST_REJECTED':
                self._handle_friend_request_rejected(obj)
                return
            if msg_type == 'FRIEND_REQUESTS':
                self._handle_friend_requests(obj)
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

    def _handle_find_user_result(self, obj):
        found = bool(obj.get('found'))
        if not found:
            self._found_user_email = None
            self.btn_send_request.configure(state=tk.DISABLED)
            self.result_card.grid_remove()
            error = obj.get('error') or 'Người dùng không tồn tại.'
            try:
                # If server returned a prefixed error, simplify message
                if 'not_found' in error:
                    error = 'Người dùng không tồn tại.'
            except Exception:
                pass
            messagebox.showerror('Tìm bạn', error)
            return
        email = obj.get('email') or ''
        display_name = obj.get('displayName') or (email.split('@', 1)[0] if '@' in email else email)
        self._found_user_email = email
        self.tab_find.show_result(email, display_name, can_send=False)
        # Disable sending to self or existing friend
        if self.current_user_email and email.strip().lower() == self.current_user_email:
            self.tab_find.disable_send()
        elif any((email.strip().lower() == (f.get('email') or '').strip().lower()) for f in (self._friends or [])):
            self.tab_find.disable_send()
            try:
                messagebox.showinfo('Kết bạn', 'Người dùng này đã là bạn của bạn.')
            except Exception:
                pass
        else:
            self.tab_find.show_result(email, display_name, can_send=True)
        messagebox.showinfo('Tìm bạn', f'Đã tìm thấy người dùng: {email}')

    def _handle_friends(self, obj):
        friends = obj.get('friends') or []
        self._friends = friends
        self._friends_loaded = True
        self.tab_friends.set_friends(friends)

    def _on_friend_select(self):
        has = bool(self.friends_list.curselection())
        self.btn_dm.configure(state=tk.NORMAL if has else tk.DISABLED)

    def _open_dm_from_friend(self, friend):
        title = friend.get('displayName') or friend.get('email') or friend.get('uid') or 'DM'
        if not hasattr(self, '_dm_tabs'):
            self._dm_tabs = {}
        key = friend.get('uid') or friend.get('email') or str(idx)
        if key in self._dm_tabs:
            self.notebook.select(self._dm_tabs[key]['frame'])
            return
        frame = tk.Frame(self.notebook)
        self.notebook.add(frame, text=f"Chat: {title}")
        self.notebook.select(frame)
        # Header with peer info
        header = tk.Frame(frame)
        header.grid(row=0, column=0, columnspan=3, sticky='ew', padx=8, pady=(8, 0))
        header.columnconfigure(0, weight=1)
        tk.Label(header, text=title, font=('TkDefaultFont', 10, 'bold')).pack(side='left')
        tk.Label(header, text=friend.get('email') or '', fg='gray').pack(side='right')

        transcript = scrolledtext.ScrolledText(frame, wrap=tk.WORD, state=tk.DISABLED, width=60, height=18)
        transcript.grid(row=1, column=0, columnspan=3, padx=8, pady=8, sticky='nsew')
        entry = tk.Entry(frame, width=50)
        entry.grid(row=2, column=0, padx=8, pady=(0,8), sticky='ew')
        send_btn = tk.Button(frame, text='Gửi', command=lambda: self._send_dm(friend, entry, transcript))
        send_btn.grid(row=2, column=1, padx=4, pady=(0,8))
        entry.bind('<Return>', lambda _e: self._send_dm(friend, entry, transcript))
        frame.rowconfigure(1, weight=1)
        frame.columnconfigure(0, weight=1)
        self._dm_tabs[key] = { 'frame': frame, 'transcript': transcript, 'entry': entry, 'friend': friend }

    def _send_dm(self, friend, entry_widget, transcript_widget):
        text = (entry_widget.get() or '').strip()
        if not text:
            return
        try:
            transcript_widget.configure(state=tk.NORMAL)
            transcript_widget.insert(tk.END, f"Me → {friend.get('displayName') or friend.get('email')}: {text}\n")
            transcript_widget.configure(state=tk.DISABLED)
            transcript_widget.see(tk.END)
        except Exception:
            pass
        entry_widget.delete(0, tk.END)

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

    def _handle_friend_request_sent(self, obj):
        ok = bool(obj.get('ok'))
        if ok:
            messagebox.showinfo('Yêu cầu kết bạn', f'Đã gửi yêu cầu kết bạn đến {self._found_user_email}.')
            self.btn_send_request.configure(state=tk.DISABLED)
            self.result_card.grid_remove()
        else:
            err = obj.get('error') or 'Không gửi được yêu cầu.'
            messagebox.showerror('Yêu cầu kết bạn', err)

    def _handle_friend_request_accepted(self, obj):
        ok = bool(obj.get('ok'))
        if ok:
            # Remove from UI list
            self.tab_profile.remove_selected_request()
            messagebox.showinfo('Kết bạn', 'Đã chấp nhận lời mời kết bạn.')
            # Refresh friends list
            try:
                self.network.send_command({ 'type': 'LIST_FRIENDS' })
            except Exception:
                pass
            # Refresh incoming requests as well
            try:
                self.network.send_command({ 'type': 'FRIEND_REQUESTS' })
            except Exception:
                pass
            # Switch to Bạn bè tab to show the new friend
            try:
                self.notebook.select(self.tab_friends)
            except Exception:
                pass
        else:
            err = obj.get('error') or 'Không chấp nhận được lời mời.'
            messagebox.showerror('Kết bạn', err)

    def _handle_friend_request_rejected(self, obj):
        ok = bool(obj.get('ok'))
        if ok:
            # Remove from UI list
            self.tab_profile.remove_selected_request()
            messagebox.showinfo('Kết bạn', 'Đã từ chối lời mời kết bạn.')
            try:
                self.network.send_command({ 'type': 'FRIEND_REQUESTS' })
            except Exception:
                pass
        else:
            err = obj.get('error') or 'Không từ chối được lời mời.'
            messagebox.showerror('Kết bạn', err)

    def _handle_friend_requests(self, obj):
        requests = obj.get('requests') or []
        # Save raw for later accept/reject payloads
        self._incoming_requests = requests
        # Populate listbox with email fallback to fromUid
        emails = []
        for r in requests:
            email = r.get('fromEmail') or r.get('fromUid') or ''
            if email:
                emails.append(email)
        self.tab_profile.set_friend_requests(emails)

        # try:
        #     self.log(f"[FriendRequests] Loaded {len(emails)} request(s)")
        # except Exception:
        #     pass

    def set_friend_requests(self, requester_emails):
        """Replace the list of incoming friend requests shown in Profile."""
        self.tab_profile.set_friend_requests(requester_emails)

    def on_close(self):
        try:
            self.network.disconnect()
        finally:
            self.master.destroy()
