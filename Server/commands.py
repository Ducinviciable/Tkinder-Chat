import json

try:
    from Chat.Server.firebase_admin_utils import get_user_by_email, list_friends, get_email_for_uid, ensure_user_profile
    from Chat.Server.firebase_admin_utils import init_firebase_if_needed
    from Chat.Server.firebase_admin_utils import db
    from Chat.Server.state import socket_to_user
except Exception:
    from firebase_admin_utils import get_user_by_email, list_friends, get_email_for_uid, ensure_user_profile
    from firebase_admin_utils import init_firebase_if_needed
    from firebase_admin_utils import db
    from state import socket_to_user


def handle_command_line(conn, obj: dict):
    cmd_type = (obj.get('type') or '').upper()
    try:
        print(f"[CMD] received type={cmd_type} obj_keys={list(obj.keys())}")
    except Exception:
        pass
    if cmd_type == 'FIND_USER':
        _cmd_find_user(conn, obj)
    elif cmd_type == 'LIST_FRIENDS':
        _cmd_list_friends(conn)
    elif cmd_type == 'SEND_FRIEND_REQUEST':
        _cmd_send_friend_request(conn, obj)
    elif cmd_type == 'ACCEPT_REQUEST':
        _cmd_accept_request(conn, obj)
    elif cmd_type == 'REJECT_REQUEST':
        _cmd_reject_request(conn, obj)
    elif cmd_type == 'FRIEND_REQUESTS':
        _cmd_friend_requests(conn)
    else:
        _send_cmd(conn, { 'type': 'ERROR', 'message': 'unknown_command' })


def _cmd_find_user(conn, obj: dict):
    email = (obj.get('email') or '').strip()
    if not email:
        _send_cmd(conn, { 'type': 'FIND_USER_RESULT', 'found': False, 'error': 'missing_email' })
        return
    record = get_user_by_email(email)
    if not record:
        _send_cmd(conn, { 'type': 'FIND_USER_RESULT', 'found': False, 'error': 'not_found' })
        return
    _send_cmd(conn, {
        'type': 'FIND_USER_RESULT',
        'found': True,
        'email': record.get('email') or email,
        'displayName': record.get('displayName') or '',
        'uid': record.get('uid') or ''
    })


def _send_cmd(conn, obj: dict):
    try:
        conn.sendall(("CMD " + json.dumps(obj) + "\n").encode('utf-8'))
    except Exception:
        pass


def _cmd_list_friends(conn):
    # Pull uid from connection attribute set during AUTH
    uid = getattr(conn, '_chat_uid', '')
    if not uid:
        # Fallback resolve from socket_to_uid map
        try:
            from Chat.Server.state import socket_to_uid as _s2u  # type: ignore
        except Exception:
            from state import socket_to_uid as _s2u  # type: ignore
        try:
            uid = _s2u.get(conn, '')
        except Exception:
            uid = ''
        if not uid:
            _send_cmd(conn, { 'type': 'FRIENDS', 'friends': [], 'error': 'unauthorized' })
            return
    friends = list_friends(uid)
    try:
        print(f"[FRIEND] LIST_FRIENDS uid={uid}: {len(friends)} item(s)")
    except Exception:
        pass
    _send_cmd(conn, { 'type': 'FRIENDS', 'friends': friends })


def _resolve_uid_from_obj(obj: dict) -> str:
    to_uid = (obj.get('toUid') or '').strip()
    if to_uid:
        return to_uid
    to_email = (obj.get('toEmail') or '').strip()
    if to_email:
        record = get_user_by_email(to_email)
        return (record or {}).get('uid') or ''
    return ''


def _cmd_send_friend_request(conn, obj: dict):
    uid = getattr(conn, '_chat_uid', '')
    if not uid:
        # Fallback resolve uid by the label (email) stored at handshake
        try:
            label = socket_to_user.get(conn) or ''
            if label:
                rec = get_user_by_email(label)
                if rec and rec.get('uid'):
                    uid = rec['uid']
                    try:
                        conn._chat_uid = uid  
                    except Exception:
                        pass
        except Exception:
            pass
    if not uid:
        try:
            print(f"[FRIEND] SEND_FRIEND_REQUEST unauthorized: conn has no uid. obj={obj}")
        except Exception:
            pass
        _send_cmd(conn, { 'type': 'FRIEND_REQUEST_SENT', 'ok': False, 'error': 'unauthorized' })
        return
    to_uid = _resolve_uid_from_obj(obj)
    if not to_uid or to_uid == uid:
        try:
            print(f"[FRIEND] SEND_FRIEND_REQUEST invalid_target: from={uid}, to_uid={to_uid}, obj={obj}")
        except Exception:
            pass
        _send_cmd(conn, { 'type': 'FRIEND_REQUEST_SENT', 'ok': False, 'error': 'invalid_target' })
        return
    try:
        init_firebase_if_needed()
        try:
            print(f"[FRIEND] SEND_FRIEND_REQUEST from={uid} to={to_uid}")
        except Exception:
            pass
        # Guard 1: already friends (either direction)
        already_a = bool(db.reference(f'/users/{uid}/friends/{to_uid}').get())
        already_b = bool(db.reference(f'/users/{to_uid}/friends/{uid}').get())
        if already_a or already_b:
            _send_cmd(conn, { 'type': 'FRIEND_REQUEST_SENT', 'ok': False, 'error': 'already_friends' })
            return

        # Guard 2: already has pending request
        req_ref = db.reference(f'/users/{to_uid}/incoming_requests/{uid}')
        if bool(req_ref.get()):
            _send_cmd(conn, { 'type': 'FRIEND_REQUEST_SENT', 'ok': False, 'error': 'already_requested' })
            return

        # Create request
        req_ref = db.reference(f'/users/{to_uid}/incoming_requests/{uid}')
        req_ref.set({ 'createdAt': {'.sv': 'timestamp'} })
        key = uid
        _send_cmd(conn, { 'type': 'FRIEND_REQUEST_SENT', 'ok': True, 'toUid': to_uid, 'requestId': key })
    except Exception as e:
        _send_cmd(conn, { 'type': 'FRIEND_REQUEST_SENT', 'ok': False, 'error': f'{e}' })


def _cmd_accept_request(conn, obj: dict):
    uid = getattr(conn, '_chat_uid', '') 
    if not uid:
        try:
            from Chat.Server.state import socket_to_uid as _s2u  
        except Exception:
            from state import socket_to_uid as _s2u  
        try:
            uid = _s2u.get(conn, '')
        except Exception:
            uid = ''
    from_uid = (obj.get('fromUid') or '').strip()
    if not from_uid:
        from_email = (obj.get('fromEmail') or '').strip()
        if from_email:
            rec = get_user_by_email(from_email)
            from_uid = (rec or {}).get('uid') or ''
    request_id = (obj.get('requestId') or '').strip()
    if not uid or not from_uid:
        try:
            print(f"[FRIEND] ACCEPT_REQUEST missing_params: uid={uid}, from_uid={from_uid}, obj={obj}")
        except Exception:
            pass
        _send_cmd(conn, { 'type': 'FRIEND_REQUEST_ACCEPTED', 'ok': False, 'error': 'missing_params' })
        return
    try:
        init_firebase_if_needed()
        try:
            print(f"[FRIEND] ACCEPT_REQUEST uid={uid} from_uid={from_uid} request_id={request_id}")
        except Exception:
            pass
        # Create friendships both directions under /users
        db.reference(f'/users/{uid}/friends/{from_uid}').set(True)
        db.reference(f'/users/{from_uid}/friends/{uid}').set(True)
        # Remove request
        db.reference(f'/users/{uid}/incoming_requests/{from_uid}').delete()
        _send_cmd(conn, { 'type': 'FRIEND_REQUEST_ACCEPTED', 'ok': True, 'fromUid': from_uid })
    except Exception as e:
        _send_cmd(conn, { 'type': 'FRIEND_REQUEST_ACCEPTED', 'ok': False, 'error': f'{e}' })


def _cmd_reject_request(conn, obj: dict):
    uid = getattr(conn, '_chat_uid', '')
    if not uid:
        try:
            from Chat.Server.state import socket_to_uid as _s2u  
        except Exception:
            from state import socket_to_uid as _s2u  
        try:
            uid = _s2u.get(conn, '')
        except Exception:
            uid = ''
    from_uid = (obj.get('fromUid') or '').strip()
    if not from_uid:
        from_email = (obj.get('fromEmail') or '').strip()
        if from_email:
            rec = get_user_by_email(from_email)
            from_uid = (rec or {}).get('uid') or ''
    request_id = (obj.get('requestId') or '').strip()
    if not uid or not from_uid:
        try:
            print(f"[FRIEND] REJECT_REQUEST missing_params: uid={uid}, from_uid={from_uid}, obj={obj}")
        except Exception:
            pass
        _send_cmd(conn, { 'type': 'FRIEND_REQUEST_REJECTED', 'ok': False, 'error': 'missing_params' })
        return
    try:
        init_firebase_if_needed()
        try:
            print(f"[FRIEND] REJECT_REQUEST uid={uid} from_uid={from_uid} request_id={request_id}")
        except Exception:
            pass
        # Remove request under /users
        db.reference(f'/users/{uid}/incoming_requests/{from_uid}').delete()
        _send_cmd(conn, { 'type': 'FRIEND_REQUEST_REJECTED', 'ok': True, 'fromUid': from_uid })
    except Exception as e:
        _send_cmd(conn, { 'type': 'FRIEND_REQUEST_REJECTED', 'ok': False, 'error': f'{e}' })


def _cmd_friend_requests(conn):
    uid = getattr(conn, '_chat_uid', '')
    if not uid:
        # Fallback: attempt to fetch uid from state map by socket
        try:
            from Chat.Server.state import socket_to_uid as _s2u  # type: ignore
        except Exception:
            from state import socket_to_uid as _s2u 
        try:
            uid = _s2u.get(conn, '')
        except Exception:
            uid = ''
        if not uid:
            try:
                print("[FRIEND] REQUESTS unauthorized: connection has no uid")
            except Exception:
                pass
            _send_cmd(conn, { 'type': 'FRIEND_REQUESTS', 'requests': [], 'error': 'unauthorized' })
            return
    try:
        init_firebase_if_needed()
        path = f'/users/{uid}/incoming_requests'
        data = db.reference(path).get() or {}
        requests = []
        if isinstance(data, dict):
            for from_uid, r in data.items():
                created_at = r.get('createdAt') if isinstance(r, dict) else None
                # Resolve email for display
                try:
                    email = get_email_for_uid(from_uid) or ''
                except Exception:
                    email = ''
                requests.append({ 'requestId': from_uid, 'fromUid': from_uid, 'fromEmail': email, 'createdAt': created_at })
        try:
            print(f"[FRIEND] REQUESTS for uid={uid} path={path}: {len(requests)} item(s)")
        except Exception:
            pass
        _send_cmd(conn, { 'type': 'FRIEND_REQUESTS', 'requests': requests })
    except Exception as e:
        _send_cmd(conn, { 'type': 'FRIEND_REQUESTS', 'requests': [], 'error': f'{e}' })


