import tkinter as tk
from tkinter import messagebox
from tkinter import ttk


class CreateGroupFrame(tk.Frame):
    def __init__(self, master, on_create_group, on_refresh_friends):
        super().__init__(master)
        self.on_create_group = on_create_group
        self.on_refresh_friends = on_refresh_friends
        
        # Group name input
        tk.Label(self, text='Tên nhóm:').grid(row=0, column=0, padx=8, pady=(12, 4), sticky='w')
        self.entry_group_name = tk.Entry(self, width=30)
        self.entry_group_name.grid(row=0, column=1, padx=8, pady=(12, 4), sticky='ew')
        
        # Friends selection
        tk.Label(self, text='Chọn bạn bè:').grid(row=1, column=0, padx=8, pady=(8, 4), sticky='w')
        
        # Frame for friends list and buttons
        friends_frame = tk.Frame(self)
        friends_frame.grid(row=2, column=0, columnspan=2, padx=8, pady=4, sticky='nsew')
        friends_frame.columnconfigure(0, weight=1)
        friends_frame.rowconfigure(0, weight=1)
        
        # Friends list with checkboxes
        self.friends_list = tk.Frame(friends_frame)
        self.friends_list.grid(row=0, column=0, sticky='nsew')
        
        # Scrollbar for friends list
        scrollbar = tk.Scrollbar(friends_frame, orient="vertical")
        scrollbar.grid(row=0, column=1, sticky='ns')
        
        # Canvas for scrollable friends list
        self.canvas = tk.Canvas(friends_frame, yscrollcommand=scrollbar.set)
        self.canvas.grid(row=0, column=0, sticky='nsew')
        scrollbar.config(command=self.canvas.yview)
        
        # Frame inside canvas for friends checkboxes
        self.friends_inner_frame = tk.Frame(self.canvas)
        self.canvas_window = self.canvas.create_window((0, 0), window=self.friends_inner_frame, anchor="nw")
        
        # Buttons
        button_frame = tk.Frame(self)
        button_frame.grid(row=3, column=0, columnspan=2, padx=8, pady=8, sticky='ew')
        
        self.btn_refresh = tk.Button(button_frame, text='Làm mới danh sách', command=self._refresh_friends)
        self.btn_refresh.pack(side='left', padx=(0, 8))
        
        self.btn_create = tk.Button(button_frame, text='Tạo nhóm', command=self._create_group, state=tk.DISABLED)
        self.btn_create.pack(side='right')
        
        # Configure grid weights
        self.rowconfigure(2, weight=1)
        self.columnconfigure(1, weight=1)
        friends_frame.rowconfigure(0, weight=1)
        friends_frame.columnconfigure(0, weight=1)
        
        # Bind events
        self.entry_group_name.bind('<KeyRelease>', self._on_input_change)
        
        # Initialize
        self._friends = []
        self._friend_vars = {}
        self._selected_friends = set()
        
        # Load friends on initialization
        self._refresh_friends()

    def set_friends(self, friends):
        """Set the list of friends and update the UI"""
        self._friends = friends or []
        self._friend_vars = {}
        self._selected_friends = set()
        
        # Clear existing checkboxes
        for widget in self.friends_inner_frame.winfo_children():
            widget.destroy()
        
        if not self._friends:
            # Show message when no friends
            no_friends_label = tk.Label(
                self.friends_inner_frame,
                text="Chưa có bạn bè nào. Hãy kết bạn trước khi tạo nhóm.",
                fg="gray",
                font=('Arial', 10, 'italic')
            )
            no_friends_label.grid(row=0, column=0, sticky='w', padx=4, pady=8)
        else:
            # Create checkboxes for each friend
            for i, friend in enumerate(self._friends):
                var = tk.BooleanVar()
                self._friend_vars[friend.get('uid', '')] = var
                
                cb = tk.Checkbutton(
                    self.friends_inner_frame,
                    text=friend.get('displayName') or friend.get('email') or 'Unknown',
                    variable=var,
                    command=lambda uid=friend.get('uid', ''): self._on_friend_select(uid)
                )
                cb.grid(row=i, column=0, sticky='w', padx=4, pady=2)
        
        # Update canvas scroll region
        self.friends_inner_frame.update_idletasks()
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        
        self._update_create_button()

    def _on_friend_select(self, uid):
        """Handle friend selection"""
        if uid in self._friend_vars:
            if self._friend_vars[uid].get():
                self._selected_friends.add(uid)
            else:
                self._selected_friends.discard(uid)
        self._update_create_button()

    def _on_input_change(self, event=None):
        """Handle input field changes"""
        self._update_create_button()

    def _update_create_button(self):
        """Update create button state"""
        has_name = bool(self.entry_group_name.get().strip())
        has_friends = len(self._selected_friends) > 0
        
        self.btn_create.configure(state=(tk.NORMAL if (has_name and has_friends) else tk.DISABLED))

    def _refresh_friends(self):
        """Refresh friends list"""
        self._safe_call(self.on_refresh_friends)

    def _create_group(self):
        """Create the group"""
        group_name = self.entry_group_name.get().strip()
        if not group_name:
            messagebox.showwarning('Thiếu thông tin', 'Vui lòng nhập tên nhóm.')
            return
        
        if not self._selected_friends:
            messagebox.showwarning('Thiếu thông tin', 'Vui lòng chọn ít nhất một bạn bè.')
            return
        
        # Get selected friends data
        selected_friends_data = []
        for friend in self._friends:
            if friend.get('uid', '') in self._selected_friends:
                selected_friends_data.append(friend)
        
        self._safe_call(self.on_create_group, group_name, selected_friends_data)
        
        # Clear form after successful creation
        self.entry_group_name.delete(0, tk.END)
        for var in self._friend_vars.values():
            var.set(False)
        self._selected_friends.clear()
        self._update_create_button()

    def _safe_call(self, fn, *args, **kwargs):
        """Safely call a function with error handling"""
        if callable(fn):
            try:
                fn(*args, **kwargs)
            except Exception as e:
                messagebox.showerror('Lỗi', f'Có lỗi xảy ra: {e}')
