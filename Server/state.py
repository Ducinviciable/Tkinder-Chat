import threading

clients = []
clients_lock = threading.Lock()
socket_to_user = {} # email/uid/displayName
socket_to_uid = {} # socket/uid
uid_to_socket = {} # uid/socket


