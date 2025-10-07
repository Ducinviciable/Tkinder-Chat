import tkinter as tk
from Chat.Client.ui.login_window import LoginWindow
from Chat.Client.ui.chat_window import ChatWindow


def on_login_success(host: str, port: int, id_token: str, email: str):
    chat_root = tk.Tk()
    ChatWindow(chat_root, host, port, id_token, email)
    chat_root.mainloop()


def main():
    root = tk.Tk()
    LoginWindow(root, on_login_success)
    root.mainloop()


if __name__ == '__main__':
    main()
