import socket;
import threading;
import os;
import json;

try:
    # Firebase Admin SDK for verifying ID tokens
    import firebase_admin; from firebase_admin import credentials, auth as fb_auth;
    _FIREBASE_AVAILABLE = True;
except Exception:
    _FIREBASE_AVAILABLE = False;

 # File transfer removed; only text chat remains

clients = [];
clients_lock = threading.Lock();
socket_to_user = {};

_firebase_initialized = False;

def _init_firebase_if_needed():
    global _firebase_initialized;
    if _firebase_initialized or not _FIREBASE_AVAILABLE:
        return;
    try:
        cred_path = os.environ.get('FIREBASE_CREDENTIALS', '').strip();
        if not cred_path:
            cred_path = os.environ.get('GOOGLE_APPLICATION_CREDENTIALS', '').strip();
        if not cred_path or not os.path.isfile(cred_path):
            # Fallback: Chat/lib/firebase-service.json relative to this file
            server_dir = os.path.dirname(__file__);
            chat_root = os.path.abspath(os.path.join(server_dir, '..'));
            fallback_path = os.path.join(chat_root, 'lib', 'firebase-service.json');
            if os.path.isfile(fallback_path):
                cred_path = fallback_path;

        if cred_path and os.path.isfile(cred_path):
            # Read project_id for explicit initialization (avoids "A project ID is required" errors)
            project_id = '';
            try:
                with open(cred_path, 'r', encoding='utf-8') as f:
                    data = json.load(f);
                    project_id = (data.get('project_id') or '').strip();
            except Exception:
                project_id = '';
            cred = credentials.Certificate(cred_path);
            if project_id:
                firebase_admin.initialize_app(cred, { 'projectId': project_id });
            else:
                firebase_admin.initialize_app(cred);
        else:
            # Try default app (ADC). On Windows dev, set env var or place serviceAccountKey.json and point to it.
            firebase_admin.initialize_app();
        _firebase_initialized = True;
        print('[Auth] Firebase initialized');
    except Exception as exc:
        print(f"[Auth] Firebase init failed: {exc}");
        _firebase_initialized = False;

def _verify_id_token(id_token: str) -> tuple[bool, str]:
    if not _FIREBASE_AVAILABLE:
        return (False, 'auth_unavailable');
    _init_firebase_if_needed();
    if not _firebase_initialized:
        return (False, 'auth_not_initialized');
    try:
        decoded = fb_auth.verify_id_token(id_token, check_revoked=True);
        email = decoded.get('email') or '';
        name = decoded.get('name') or '';
        uid = decoded.get('uid') or 'unknown';
        label = email or name or uid;
        return (True, label);
    except Exception as exc:
        reason = f'invalid_token: {exc}';
        print(f"[Auth] Token verify failed: {reason}");
        return (False, reason);

def broadcast(message: str, exclude_socket: socket.socket | None = None):
    with clients_lock:
        dead_clients = [];
        for s in clients:
            if exclude_socket is not None and s is exclude_socket:
                continue;
            try:
                # Quan trọng: thêm "\n" để client tách dòng và hiển thị ngay
                s.sendall((message + "\n").encode('utf-8'));
            except Exception:
                dead_clients.append(s);
        for s in dead_clients:
            try:
                clients.remove(s);
                socket_to_user.pop(s, None);
            except ValueError:
                pass;

 # broadcast_bytes removed

def handle_client(conn: socket.socket, addr):
    try:
        # Handshake: expect first line to be AUTH <idToken>\n
        conn.settimeout(15.0);
        buffer = b'';
        authed = False;
        user_label = '';
        while True:
            chunk = conn.recv(4096);
            if not chunk:
                raise ConnectionAbortedError('No data during auth');
            buffer += chunk;
            nl_index = buffer.find(b"\n");
            if nl_index == -1:
                # keep reading until a full line
                if len(buffer) > 8192:
                    raise ConnectionAbortedError('Auth line too large');
                continue;
            line = buffer[:nl_index];
            buffer = buffer[nl_index + 1:];
            try:
                text = line.decode('utf-8', errors='replace');
            except Exception:
                text = '';
            if not text.startswith('AUTH '):
                conn.sendall(b"AUTH_ERR Invalid handshake\n");
                raise ConnectionAbortedError('Invalid handshake');
            id_token = text[5:].strip();
            ok, label = _verify_id_token(id_token);
            if not ok:
                err_line = f"AUTH_ERR {label}\n".encode('utf-8', errors='replace');
                conn.sendall(err_line);
                raise ConnectionAbortedError('Auth failed');
            authed = True;
            user_label = label;
            conn.sendall(b"AUTH_OK\n");
            break;

        conn.settimeout(None);

        with clients_lock:
            clients.append(conn);
            socket_to_user[conn] = user_label;

        welcome = f"[Server] {user_label} joined";
        print(welcome);
        broadcast(welcome, exclude_socket=None);
        buffer = buffer if isinstance(buffer, (bytes, bytearray)) else b'';
        while True:
            chunk = conn.recv(4096);
            if not chunk:
                break;
            buffer += chunk;

            while True:
                nl_index = buffer.find(b"\n");
                if nl_index != -1:
                    line = buffer[:nl_index];
                    buffer = buffer[nl_index + 1:];
                    # Dòng text thường
                    try:
                        text = line.decode('utf-8', errors='replace');
                    except Exception:
                        text = '[binary data]';
                    if text.lower() == 'exit':
                        raise ConnectionAbortedError('Client requested exit');
                    sender = socket_to_user.get(conn, str(addr));
                    print(f"{sender}: {text}");
                    broadcast(f"{sender}: {text}", exclude_socket=conn);
                    continue;
                else:
                    if len(buffer) >= 1024:
                        try:
                            text = buffer.decode('utf-8', errors='replace');
                        except Exception:
                            text = '';
                        if text:
                            sender = socket_to_user.get(conn, str(addr));
                            print(f"{sender}: {text}");
                            broadcast(f"{sender}: {text}", exclude_socket=conn);
                            buffer = b'';
                            continue;
                    break;
    except ConnectionAbortedError:
        pass;
    except Exception as exc:
        print(f"Error with {addr}: {exc}");
    finally:
        try:
            conn.close();
        finally:
            with clients_lock:
                try:
                    clients.remove(conn);
                except ValueError:
                    pass;
                socket_to_user.pop(conn, None);
            name = socket_to_user.get(conn);
            left = f"[Server] {(name or str(addr))} left";
            print(left);
            broadcast(left, exclude_socket=None);


# Server Configuration
host_Server = socket.socket(socket.AF_INET, socket.SOCK_STREAM); # v4, TCP
host_Server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1);
host_Server.bind(('0.0.0.0', 8080));
host_Server.listen(5);


print("Server is listening on port 8080...");

try:
    while True:
        conn, addr = host_Server.accept();
        with clients_lock:
            clients.append(conn);
        print(f"Connection from {addr} has been established!");
        threading.Thread(target=handle_client, args=(conn, addr), daemon=True).start();
except KeyboardInterrupt:
    print("Shutting down server...");
finally:
    with clients_lock:
        for c in clients:
            try:
                c.close();
            except Exception:
                pass;
        clients.clear();
    host_Server.close();
