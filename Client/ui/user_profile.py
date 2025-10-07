import tkinter as tk


class UserProfileFrame(tk.Frame):
    def __init__(self, master, on_accept, on_reject, on_refresh=None):
        super().__init__(master)
        self.on_accept = on_accept
        self.on_reject = on_reject
        self.on_refresh = on_refresh

        header = tk.Frame(self)
        header.grid(row=0, column=0, columnspan=2, sticky='ew')
        tk.Label(header, text='Yêu cầu kết bạn đến:').pack(side='left', padx=8, pady=(12, 4))
        self.btn_refresh = tk.Button(header, text='Làm mới', command=self._handle_refresh)
        self.btn_refresh.pack(side='right', padx=8, pady=(12, 4))

        self.friend_requests_list = tk.Listbox(self, height=10, width=40, exportselection=False)
        self.friend_requests_list.grid(row=1, column=0, columnspan=2, padx=8, pady=4, sticky='nsew')

        self.btn_accept = tk.Button(self, text='Chấp nhận', command=self._handle_accept, state=tk.DISABLED)
        self.btn_accept.grid(row=2, column=0, padx=(8, 4), pady=8, sticky='w')
        self.btn_reject = tk.Button(self, text='Từ chối', command=self._handle_reject, state=tk.DISABLED)
        self.btn_reject.grid(row=2, column=1, padx=(4, 8), pady=8, sticky='w')

        self.friend_requests_list.bind('<<ListboxSelect>>', self._on_request_select)

        self.rowconfigure(1, weight=1)
        self.columnconfigure(0, weight=1)

    def _on_request_select(self, _event=None):
        has_selection = bool(self.get_selected_request())
        self.btn_accept.configure(state=tk.NORMAL if has_selection else tk.DISABLED)
        self.btn_reject.configure(state=tk.NORMAL if has_selection else tk.DISABLED)

    def _handle_accept(self):
        email = self.get_selected_request()
        if email:
            self.on_accept(email)

    def _handle_reject(self):
        email = self.get_selected_request()
        if email:
            self.on_reject(email)

    def _handle_refresh(self):
        if callable(self.on_refresh):
            try:
                self.on_refresh()
            except Exception:
                pass

    def set_friend_requests(self, requester_emails):
        self.friend_requests_list.delete(0, tk.END)
        for email in requester_emails or []:
            self.friend_requests_list.insert(tk.END, email)
        self._on_request_select()

    def get_selected_request(self):
        if not self.friend_requests_list.curselection():
            return None
        idx = self.friend_requests_list.curselection()[0]
        return self.friend_requests_list.get(idx)

    def remove_selected_request(self):
        if not self.friend_requests_list.curselection():
            return
        idx = self.friend_requests_list.curselection()[0]
        self.friend_requests_list.delete(idx)


