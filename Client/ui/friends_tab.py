import tkinter as tk
from tkinter import scrolledtext


class FriendsTabFrame(tk.Frame):
    def __init__(self, master, on_open_dm, on_refresh):
        super().__init__(master)
        self.on_open_dm = on_open_dm
        self.on_refresh = on_refresh

        tk.Label(self, text='Danh sách bạn bè:').grid(row=0, column=0, padx=8, pady=(12, 4), sticky='w')
        self.friends_list = tk.Listbox(self, height=12, width=40, exportselection=False)
        self.friends_list.grid(row=1, column=0, columnspan=2, padx=8, pady=4, sticky='nsew')
        self.btn_dm = tk.Button(self, text='Nhắn tin', state=tk.DISABLED, command=self._open_selected)
        self.btn_dm.grid(row=2, column=0, padx=8, pady=8, sticky='w')
        self.btn_refresh = tk.Button(self, text='Làm mới', command=lambda: self._safe_call(self.on_refresh))
        self.btn_refresh.grid(row=2, column=1, padx=8, pady=8, sticky='e')
        self.friends_list.bind('<<ListboxSelect>>', lambda _e: self._on_select())
        self.rowconfigure(1, weight=1)
        self.columnconfigure(0, weight=1)

        self._friends = []

    def set_friends(self, friends):
        self._friends = friends or []
        self.friends_list.delete(0, tk.END)
        for f in self._friends:
            label = f.get('displayName') or f.get('email') or f.get('uid') or 'Unknown'
            self.friends_list.insert(tk.END, label)
        self._on_select()

    def _on_select(self):
        has = bool(self.friends_list.curselection())
        self.btn_dm.configure(state=(tk.NORMAL if has else tk.DISABLED))

    def _open_selected(self):
        if not self.friends_list.curselection():
            return
        idx = self.friends_list.curselection()[0]
        try:
            friend = self._friends[idx]
        except Exception:
            friend = {}
        self._safe_call(self.on_open_dm, friend)

    def _safe_call(self, fn, *args, **kwargs):
        if callable(fn):
            try:
                fn(*args, **kwargs)
            except Exception:
                pass


