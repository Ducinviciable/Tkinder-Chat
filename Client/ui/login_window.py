"""
Login window module for chat client.
"""
import tkinter as tk
from tkinter import messagebox
from Chat.Client.auth import firebase_sign_in


class LoginWindow:
    """Login window with Firebase authentication."""
    
    def __init__(self, master: tk.Tk, on_login_success):
        self.master = master
        self.on_login_success = on_login_success
        self.master.title('Chat Login')
        self.master.protocol('WM_DELETE_WINDOW', self.on_close)
        
        self._setup_ui()
        
    def _setup_ui(self):
        """Setup the login window UI."""
        # Set window size and center it
        self.master.geometry('500x500')
        self.master.resizable(False, False)
        self.master.configure(bg='#f0f0f0')
        
        # Center window on screen
        self.master.update_idletasks()
        x = (self.master.winfo_screenwidth() // 2) - (500 // 2)
        y = (self.master.winfo_screenheight() // 2) - (500 // 2)
        self.master.geometry(f'500x500+{x}+{y}')
        
        # Main container with padding
        main_frame = tk.Frame(self.master, bg='#f0f0f0', padx=40, pady=30)
        main_frame.pack(fill='both', expand=True)
        
        # Title
        title_label = tk.Label(main_frame, text='Chat Application', 
                              font=('Arial', 24, 'bold'), 
                              fg='#2c3e50', bg='#f0f0f0')
        title_label.pack(pady=(0, 30))
        
        # Login form container
        form_frame = tk.Frame(main_frame, bg='white', relief='solid', bd=1)
        form_frame.pack(fill='x', pady=(0, 20))
        
        # Form padding
        form_padding = tk.Frame(form_frame, bg='white', padx=30, pady=25)
        form_padding.pack(fill='both', expand=True)
        
        self._setup_server_settings(form_padding)
        self._setup_credentials(form_padding)
        self._setup_login_button(main_frame)
        
    def _setup_server_settings(self, parent):
        """Setup server settings section."""
        server_frame = tk.Frame(parent, bg='white')
        server_frame.pack(fill='x', pady=(0, 20))
        
        tk.Label(server_frame, text='Server Settings', 
                font=('Arial', 10, 'bold'), 
                fg='#34495e', bg='white').pack(anchor='w', pady=(0, 10))
        
        # Host and Port row
        host_port_frame = tk.Frame(server_frame, bg='white')
        host_port_frame.pack(fill='x', pady=(0, 15))
        
        tk.Label(host_port_frame, text='Host:', 
                font=('Arial', 10), fg='#2c3e50', bg='white').pack(side='left', padx=(0, 10))
        self.entry_host = tk.Entry(host_port_frame, width=20, font=('Arial', 10), 
                                  relief='solid', bd=1)
        self.entry_host.insert(0, 'localhost')
        self.entry_host.pack(side='left', padx=(0, 20))
        
        tk.Label(host_port_frame, text='Port:', 
                font=('Arial', 10), fg='#2c3e50', bg='white').pack(side='left', padx=(0, 10))
        self.entry_port = tk.Entry(host_port_frame, width=8, font=('Arial', 10), 
                                  relief='solid', bd=1)
        self.entry_port.insert(0, '8080')
        self.entry_port.pack(side='left')
        
    def _setup_credentials(self, parent):
        """Setup login credentials section."""
        cred_frame = tk.Frame(parent, bg='white')
        cred_frame.pack(fill='x', pady=(0, 20))
        
        tk.Label(cred_frame, text='Login Credentials', 
                font=('Arial', 10, 'bold'), 
                fg='#34495e', bg='white').pack(anchor='w', pady=(0, 10))
        
        # Email
        email_frame = tk.Frame(cred_frame, bg='white')
        email_frame.pack(fill='x', pady=(0, 15))
        
        tk.Label(email_frame, text='Email:', 
                font=('Arial', 10), fg='#2c3e50', bg='white').pack(anchor='w')
        self.entry_email = tk.Entry(email_frame, width=35, font=('Arial', 10), 
                                   relief='solid', bd=1)
        self.entry_email.pack(fill='x', pady=(5, 0))
        
        # Password
        password_frame = tk.Frame(cred_frame, bg='white')
        password_frame.pack(fill='x', pady=(0, 20))
        
        tk.Label(password_frame, text='Password:', 
                font=('Arial', 10), fg='#2c3e50', bg='white').pack(anchor='w')
        self.entry_password = tk.Entry(password_frame, font=('Arial', 10), 
                                      show='*', relief='solid', bd=1)
        self.entry_password.pack(fill='x', pady=(5, 0))
        
    def _setup_login_button(self, parent):
        """Setup login button with hover effects."""
        button_frame = tk.Frame(parent, bg='#f0f0f0')
        button_frame.pack(fill='x')
        
        self.button_login = tk.Button(button_frame, text='LOGIN', 
                                     command=self.do_login,
                                     font=('Arial', 12, 'bold'),
                                     bg='#000000', fg='white',
                                     relief='flat', bd=0,
                                     padx=30, pady=30,
                                     cursor='hand2')
        self.button_login.pack(pady=(0, 10))
        
        # Hover effects
        def on_enter(e):
            self.button_login.config(bg='#2980b9')
        def on_leave(e):
            self.button_login.config(bg='#000000')
        
        self.button_login.bind('<Enter>', on_enter)
        self.button_login.bind('<Leave>', on_leave)
        
        # Bind Enter key to login
        self.master.bind('<Return>', lambda e: self.do_login())

    def do_login(self):
        """Handle login button click."""
        host = self.entry_host.get().strip() or 'localhost'
        try:
            port = int(self.entry_port.get().strip() or '8080')
        except ValueError:
            messagebox.showerror('Input Error', 'Port must be a number')
            return
            
        email = self.entry_email.get().strip()
        password = self.entry_password.get().strip()
        
        if not email or not password:
            messagebox.showerror('Auth Error', 'Please enter Email and Password')
            return
            
        try:
            id_token = firebase_sign_in(email, password)
            if not id_token:
                messagebox.showerror('Auth Error', 'Login failed. Check your credentials')
                return
                
            # Close login window and call success callback
            self.master.destroy()
            self.on_login_success(host, port, id_token)
            
        except ValueError as e:
            messagebox.showerror('Auth Error', str(e))
        except Exception as e:
            messagebox.showerror('Auth Error', f'Login failed: {e}')

    def on_close(self):
        """Handle window close."""
        try:
            self.master.destroy()
        except Exception:
            pass