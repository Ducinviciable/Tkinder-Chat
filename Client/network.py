import socket
import threading
from typing import Optional


class ChatNetwork: 
    def __init__(self, host: str = 'localhost', port: int = 8080):
        self.host = host
        self.port = port
        self.client_socket: Optional[socket.socket] = None
        self.is_connected = False
        self.receive_callback = None
        
    def set_receive_callback(self, callback):
        self.receive_callback = callback
        
    def connect(self, id_token: str) -> tuple[bool, Optional[str]]:
        if self.is_connected:
            return True, None

        try:
            self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            # Short timeout for establishing connection
            self.client_socket.settimeout(5.0)
            self.client_socket.connect((self.host, self.port))
        except Exception as e:
            # Provide a helpful error string
            try:
                if self.client_socket is not None:
                    self.client_socket.close()
            except Exception:
                pass
            self.client_socket = None
            return False, f'Could not connect to {self.host}:{self.port} ({e})'
        finally:
            # Clear timeout for normal operation
            try:
                if self.client_socket is not None:
                    self.client_socket.settimeout(None)
            except Exception:
                pass

        # Send AUTH handshake and wait for server response
        try:
            auth_line = f'AUTH {id_token}\n'.encode('utf-8')
            self.client_socket.sendall(auth_line)
            # Wait for single-line response
            auth_resp = self._recv_line(self.client_socket, timeout_s=15.0)
            if auth_resp != 'AUTH_OK':
                # Close socket on auth failure
                try:
                    self.client_socket.close()
                except Exception:
                    pass
                self.client_socket = None
                return False, f'Auth failed: {auth_resp}'
        except Exception as e:
            try:
                self.client_socket.close()
            except Exception:
                pass
            self.client_socket = None
            return False, f'Error during auth: {e}'

        self.is_connected = True

        # Start receiver thread
        threading.Thread(target=self._receive_loop, daemon=True).start()
        return True, None

    def send_message(self, message: str) -> bool:
        if not self.is_connected or self.client_socket is None:
            return False
            
        try:
            data_to_send = (message + '\n').encode('utf-8')
            self.client_socket.sendall(data_to_send)
            return True
        except Exception:
            self.disconnect()
            return False

    def send_command(self, obj: dict) -> bool:
        if not self.is_connected or self.client_socket is None:
            return False
        try:
            payload = 'CMD ' + __import__('json').dumps(obj)
            data_to_send = (payload + '\n').encode('utf-8')
            self.client_socket.sendall(data_to_send)
            return True
        except Exception:
            self.disconnect()
            return False

    def disconnect(self):
        try:
            if self.client_socket is not None:
                try:
                    self.client_socket.sendall('exit'.encode('utf-8'))
                except Exception:
                    pass
                self.client_socket.close()
        finally:
            self.client_socket = None
            self.is_connected = False

    def _receive_loop(self):
        assert self.client_socket is not None
        buffer = b''
        try:
            while True:
                data = self.client_socket.recv(1024)
                if not data:
                    break
                buffer += data
                
                # Parse lines
                while b'\n' in buffer:
                    line, buffer = buffer.split(b'\n', 1)
                    if line:
                        try:
                            message = line.decode('utf-8', errors='replace')
                            if self.receive_callback:
                                self.receive_callback(message)
                        except Exception:
                            pass
        except OSError:
            pass
        finally:
            self.is_connected = False
            if self.receive_callback:
                self.receive_callback('Disconnected from server')

    def _recv_line(self, s: socket.socket, timeout_s: float = 15.0) -> str:
        s.settimeout(timeout_s)
        buf = b''
        try:
            while True:
                chunk = s.recv(1024)
                if not chunk:
                    break
                buf += chunk
                nl = buf.find(b'\n')
                if nl != -1:
                    line = buf[:nl]
                    try:
                        return line.decode('utf-8', errors='replace')
                    except Exception:
                        return ''
        finally:
            s.settimeout(None)
        return ''
