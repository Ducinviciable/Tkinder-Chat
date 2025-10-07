import tkinter as tk
from tkinter import scrolledtext


class PrivateChatTab:
    """Encapsulates a DM tab UI for 1-1 chat."""

    def __init__(self, notebook: tk.Misc, friend: dict, on_send, on_load_history=None):
        self.notebook = notebook
        self.friend = friend or {}
        self.on_send = on_send
        self.on_load_history = on_load_history
        self.frame = tk.Frame(self.notebook)

        title = self.friend.get('displayName') or self.friend.get('email') or self.friend.get('uid') or 'DM'
        self.notebook.add(self.frame, text=f"Chat: {title}")
        self.notebook.select(self.frame)

        header = tk.Frame(self.frame)
        header.grid(row=0, column=0, columnspan=3, sticky='ew', padx=8, pady=(8, 0))
        header.columnconfigure(0, weight=1)
        tk.Label(header, text=title, font=('TkDefaultFont', 10, 'bold')).pack(side='left')
        tk.Label(header, text=self.friend.get('email') or '', fg='gray').pack(side='right')

        self.transcript = scrolledtext.ScrolledText(self.frame, wrap=tk.WORD, state=tk.DISABLED, width=60, height=18)
        self.transcript.grid(row=1, column=0, columnspan=3, padx=8, pady=8, sticky='nsew')

        self.entry = tk.Entry(self.frame, width=50)
        self.entry.grid(row=2, column=0, padx=8, pady=(0, 8), sticky='ew')
        self.send_btn = tk.Button(self.frame, text='Gửi', command=self._on_send)
        self.send_btn.grid(row=2, column=1, padx=4, pady=(0, 8))
        self.entry.bind('<Return>', lambda _e: self._on_send())

        self.frame.rowconfigure(1, weight=1)
        self.frame.columnconfigure(0, weight=1)

        # Load history if callback provided
        if callable(self.on_load_history):
            try:
                self.on_load_history(self.friend)
            except Exception:
                pass

    def focus(self):
        try:
            self.notebook.select(self.frame)
        except Exception:
            pass

    def append_self(self, text: str):
        try:
            self.transcript.configure(state=tk.NORMAL)
            self.transcript.insert(tk.END, f"Me: {text}\n")
            self.transcript.configure(state=tk.DISABLED)
            self.transcript.see(tk.END)
        except Exception:
            pass

    def append_peer(self, text: str):
        try:
            self.transcript.configure(state=tk.NORMAL)
            self.transcript.insert(tk.END, f"Friend: {text}\n")
            self.transcript.configure(state=tk.DISABLED)
            self.transcript.see(tk.END)
        except Exception:
            pass

    def append_history(self, messages, me_uid: str):
        try:
            self.transcript.configure(state=tk.NORMAL)
            for m in messages or []:
                who = 'Me' if (m.get('senderUid') == me_uid) else 'Friend'
                self.transcript.insert(tk.END, f"{who}: {m.get('text') or ''}\n")
            self.transcript.configure(state=tk.DISABLED)
            self.transcript.see(tk.END)
        except Exception:
            pass

    def _on_send(self):
        text = (self.entry.get() or '').strip()
        if not text:
            return
        if callable(self.on_send):
            self.on_send(self.friend, text, self.transcript)
        self.append_self(text)
        try:
            self.entry.delete(0, tk.END)
        except Exception:
            pass


