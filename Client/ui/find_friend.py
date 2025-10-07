import tkinter as tk


class FindFriendFrame(tk.Frame):
    def __init__(self, master, on_search, on_send_request):
        super().__init__(master)
        self.on_search = on_search
        self.on_send_request = on_send_request

        tk.Label(self, text='Nhập Gmail:').grid(row=0, column=0, padx=8, pady=(12, 4), sticky='w')
        self.entry_search_email = tk.Entry(self, width=40)
        self.entry_search_email.grid(row=1, column=0, padx=8, pady=4, sticky='w')
        self.entry_search_email.bind('<Return>', lambda _e: self._do_search())

        self.btn_search = tk.Button(self, text='Tìm', command=self._do_search)
        self.btn_search.grid(row=1, column=1, padx=8, pady=4, sticky='w')

        # Result card
        self.result_card = tk.Frame(self, relief=tk.GROOVE, borderwidth=1)
        self.result_card.grid(row=2, column=0, columnspan=2, padx=8, pady=(8, 12), sticky='ew')
        self.result_card.columnconfigure(0, weight=1)
        self.label_found_name = tk.Label(self.result_card, text='', font=('TkDefaultFont', 10, 'bold'))
        self.label_found_name.grid(row=0, column=0, padx=8, pady=(8, 2), sticky='w')
        self.label_found_email = tk.Label(self.result_card, text='', fg='gray')
        self.label_found_email.grid(row=1, column=0, padx=8, pady=(0, 8), sticky='w')
        self.btn_send_request = tk.Button(self.result_card, text='Gửi yêu cầu kết bạn', state=tk.DISABLED, command=self._do_send)
        self.btn_send_request.grid(row=0, column=1, rowspan=2, padx=8, pady=8, sticky='e')
        self.result_card.grid_remove()

    def _do_search(self):
        email = (self.entry_search_email.get() or '').strip()
        if callable(self.on_search):
            self.on_search(email)

    def _do_send(self):
        if callable(self.on_send_request):
            self.on_send_request()

    # External control helpers
    def show_result(self, email: str, display_name: str, can_send: bool):
        self.label_found_name.configure(text=display_name or '')
        self.label_found_email.configure(text=email or '')
        self.btn_send_request.configure(state=(tk.NORMAL if can_send else tk.DISABLED))
        self.result_card.grid()

    def hide_result(self):
        self.result_card.grid_remove()

    def disable_send(self):
        self.btn_send_request.configure(state=tk.DISABLED)


