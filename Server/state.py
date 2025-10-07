import threading

clients = []
clients_lock = threading.Lock()
socket_to_user = {}
socket_to_uid = {}


