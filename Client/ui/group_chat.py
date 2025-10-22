import tkinter as tk
from tkinter import scrolledtext, messagebox
from tkinter import ttk


class GroupChatTab(tk.Frame):
    def __init__(self, master, group_data, on_send_message, on_load_history):
        super().__init__(master)
        self.group_data = group_data
        self.on_send_message = on_send_message
        self.on_load_history = on_load_history
        
        # Group info
        group_name = group_data.get('name', 'Unknown Group')
        group_id = group_data.get('id', '')
        
        # Header with group name
        header_frame = tk.Frame(self)
        header_frame.grid(row=0, column=0, columnspan=3, padx=8, pady=8, sticky='ew')
        
        tk.Label(header_frame, text=f'Nhóm: {group_name}', font=('Arial', 12, 'bold')).pack(side='left')
        
        # Members info
        members = group_data.get('members', [])
        members_text = ', '.join([m.get('displayName', m.get('email', 'Unknown')) for m in members])
        tk.Label(header_frame, text=f'Thành viên: {members_text}', font=('Arial', 9)).pack(side='left', padx=(20, 0))
        
        # Chat display
        self.chat_display = scrolledtext.ScrolledText(
            self, wrap=tk.WORD, state=tk.DISABLED,
            width=60, height=20, font=('Arial', 10)
        )
        self.chat_display.grid(row=1, column=0, columnspan=3, padx=8, pady=8, sticky='nsew')
        
        # Message input
        self.message_entry = tk.Entry(self, width=50, font=('Arial', 10))
        self.message_entry.grid(row=2, column=0, padx=8, pady=8, sticky='ew')
        self.message_entry.bind('<Return>', lambda e: self._send_message())
        
        # Send button
        self.send_button = tk.Button(self, text='Gửi', command=self._send_message)
        self.send_button.grid(row=2, column=1, padx=4, pady=8)
        
        # Load history button
        self.history_button = tk.Button(self, text='Tải lịch sử', command=self._load_history)
        self.history_button.grid(row=2, column=2, padx=8, pady=8)
        
        # Configure grid weights
        self.rowconfigure(1, weight=1)
        self.columnconfigure(0, weight=1)
        
        # Load initial history
        self._load_history()

    def _send_message(self):
        """Send a message to the group"""
        message = self.message_entry.get().strip()
        if not message:
            return
        
        # Add message to display immediately
        self._add_message_to_display("Bạn", message, is_own=True)
        
        # Send to server
        try:
            self.on_send_message(self.group_data.get('id', ''), message)
        except Exception as e:
            messagebox.showerror('Lỗi', f'Không thể gửi tin nhắn: {e}')
            return
        
        # Clear input
        self.message_entry.delete(0, tk.END)

    def _load_history(self):
        """Load chat history"""
        try:
            self.on_load_history(self.group_data.get('id', ''))
        except Exception as e:
            messagebox.showerror('Lỗi', f'Không thể tải lịch sử: {e}')

    def _add_message_to_display(self, sender, message, is_own=False):
        """Add a message to the chat display"""
        self.chat_display.configure(state=tk.NORMAL)
        
        # Format message
        if is_own:
            formatted_msg = f"[Bạn]: {message}\n"
            self.chat_display.insert(tk.END, formatted_msg, "own_message")
        else:
            formatted_msg = f"[{sender}]: {message}\n"
            self.chat_display.insert(tk.END, formatted_msg, "other_message")
        
        self.chat_display.configure(state=tk.DISABLED)
        self.chat_display.see(tk.END)

    def add_message(self, sender, message, sender_uid=None):
        """Add a received message to the display"""
        # Get sender name from group members or use UID
        sender_name = sender
        if sender_uid and self.group_data.get('members'):
            for member in self.group_data.get('members', []):
                if member.get('uid') == sender_uid:
                    sender_name = member.get('displayName', member.get('email', sender))
                    break
        
        self._add_message_to_display(sender_name, message)

    def load_messages(self, messages):
        """Load multiple messages into the display"""
        self.chat_display.configure(state=tk.NORMAL)
        self.chat_display.delete(1.0, tk.END)
        
        for msg in messages:
            sender_uid = msg.get('senderUid', '')
            text = msg.get('text', '')
            timestamp = msg.get('ts', 0)
            
            # Get sender name
            sender_name = sender_uid
            if self.group_data.get('members'):
                for member in self.group_data.get('members', []):
                    if member.get('uid') == sender_uid:
                        sender_name = member.get('displayName', member.get('email', sender_uid))
                        break
            
            # Format timestamp if available
            time_str = ""
            if timestamp:
                try:
                    import datetime
                    dt = datetime.datetime.fromtimestamp(timestamp / 1000)
                    time_str = f" [{dt.strftime('%H:%M')}]"
                except:
                    pass
            
            formatted_msg = f"[{sender_name}]{time_str}: {text}\n"
            self.chat_display.insert(tk.END, formatted_msg)
        
        self.chat_display.configure(state=tk.DISABLED)
        self.chat_display.see(tk.END)

    def focus(self):
        """Focus on the message input"""
        self.message_entry.focus()


class GroupsListFrame(tk.Frame):
    def __init__(self, master, on_open_group, on_create_group):
        super().__init__(master)
        self.on_open_group = on_open_group
        self.on_create_group = on_create_group
        
        # Title
        tk.Label(self, text='Danh sách nhóm:', font=('Arial', 12, 'bold')).grid(row=0, column=0, padx=8, pady=(12, 4), sticky='w')
        
        # Groups list
        self.groups_list = tk.Listbox(self, height=15, width=40, exportselection=False)
        self.groups_list.grid(row=1, column=0, columnspan=2, padx=8, pady=4, sticky='nsew')
        self.groups_list.bind('<<ListboxSelect>>', self._on_select)
        self.groups_list.bind('<Double-Button-1>', self._open_selected)
        
        # Buttons
        self.btn_open = tk.Button(self, text='Mở nhóm', state=tk.DISABLED, command=self._open_selected)
        self.btn_open.grid(row=2, column=0, padx=8, pady=8, sticky='w')
        
        self.btn_create = tk.Button(self, text='Tạo nhóm mới', command=self._create_new_group)
        self.btn_create.grid(row=2, column=1, padx=8, pady=8, sticky='e')
        
        # Configure grid
        self.rowconfigure(1, weight=1)
        self.columnconfigure(0, weight=1)
        
        self._groups = []

    def set_groups(self, groups):
        """Set the list of groups"""
        self._groups = groups or []
        self.groups_list.delete(0, tk.END)
        
        for group in self._groups:
            name = group.get('name', 'Unknown Group')
            member_count = len(group.get('members', []))
            display_text = f"{name} ({member_count} thành viên)"
            self.groups_list.insert(tk.END, display_text)
        
        self._on_select()

    def _on_select(self, event=None):
        """Handle group selection"""
        has_selection = bool(self.groups_list.curselection())
        self.btn_open.configure(state=(tk.NORMAL if has_selection else tk.DISABLED))

    def _open_selected(self, event=None):
        """Open selected group"""
        if not self.groups_list.curselection():
            return
        
        idx = self.groups_list.curselection()[0]
        try:
            group = self._groups[idx]
        except (IndexError, KeyError):
            return
        
        self._safe_call(self.on_open_group, group)

    def _create_new_group(self):
        """Create new group"""
        self._safe_call(self.on_create_group)

    def _safe_call(self, fn, *args, **kwargs):
        """Safely call a function with error handling"""
        if callable(fn):
            try:
                fn(*args, **kwargs)
            except Exception as e:
                messagebox.showerror('Lỗi', f'Có lỗi xảy ra: {e}')
