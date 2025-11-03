import json

try:
    from Chat.Server.firebase_admin_utils import get_user_by_email, list_friends, get_email_for_uid, ensure_user_profile
    from Chat.Server.firebase_admin_utils import init_firebase_if_needed
    from Chat.Server.firebase_admin_utils import db
    from Chat.Server.state import socket_to_user
    from Chat.Server.state import uid_to_socket
except Exception:
    from firebase_admin_utils import get_user_by_email, list_friends, get_email_for_uid, ensure_user_profile
    from firebase_admin_utils import init_firebase_if_needed
    from firebase_admin_utils import db
    from state import socket_to_user
    from state import uid_to_socket


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
    elif cmd_type == 'SEND_DM':
        _cmd_send_dm(conn, obj)
    elif cmd_type == 'LOAD_THREAD':
        _cmd_load_thread(conn, obj)
    elif cmd_type == 'CREATE_GROUP':
        _cmd_create_group(conn, obj)
    elif cmd_type == 'LIST_GROUPS':
        _cmd_list_groups(conn)
    elif cmd_type == 'SEND_GROUP_MESSAGE':
        _cmd_send_group_message(conn, obj)
    elif cmd_type == 'LOAD_GROUP_HISTORY':
        _cmd_load_group_history(conn, obj)
    elif cmd_type == 'LEAVE_GROUP':
        _cmd_leave_group(conn, obj)
    elif cmd_type == 'LIST_GROUP_MEMBERS':
        _cmd_list_group_members(conn, obj)
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

# Send command to client
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


def _make_thread_id(uid_a: str, uid_b: str) -> str:
    if uid_a <= uid_b:
        return f"{uid_a}__{uid_b}"
    return f"{uid_b}__{uid_a}"


def _cmd_send_dm(conn, obj: dict):
    uid = getattr(conn, '_chat_uid', '')
    if not uid:
        # try fallback
        try:
            from Chat.Server.state import socket_to_uid as _s2u  
        except Exception:
            from state import socket_to_uid as _s2u  
        uid = _s2u.get(conn, '') if _s2u else ''
    to_uid = (obj.get('toUid') or '').strip()
    text = (obj.get('text') or '').strip()
    client_msg_id = (obj.get('clientMsgId') or '').strip()
    if not uid or not to_uid or not text:
        _send_cmd(conn, { 'type': 'DM_DELIVERED', 'ok': False, 'clientMsgId': client_msg_id, 'error': 'missing_params' })
        return
    try:
        init_firebase_if_needed()
        thread_id = _make_thread_id(uid, to_uid)
        # Write message to database
        msg_ref = db.reference(f'/chats/{thread_id}/messages').push({
            'senderUid': uid,
            'text': text,
            'ts': {'.sv': 'timestamp'},
        })
        # Deliver to recipient if user online
        try:
            peer_socket = uid_to_socket.get(to_uid)
            if peer_socket is not None:
                _send_cmd(peer_socket, { 'type': 'DM', 'fromUid': uid, 'text': text, 'threadId': thread_id })
        except Exception:
            pass
        _send_cmd(conn, { 'type': 'DM_DELIVERED', 'ok': True, 'clientMsgId': client_msg_id, 'threadId': thread_id })
    except Exception as e:
        _send_cmd(conn, { 'type': 'DM_DELIVERED', 'ok': False, 'clientMsgId': client_msg_id, 'error': f'{e}' })


def _cmd_load_thread(conn, obj: dict):
    uid = getattr(conn, '_chat_uid', '')
    if not uid:
        try:
            from Chat.Server.state import socket_to_uid as _s2u  # type: ignore
        except Exception:
            from state import socket_to_uid as _s2u  # type: ignore
        uid = _s2u.get(conn, '') if _s2u else ''
    peer_uid = (obj.get('peerUid') or '').strip()
    limit = obj.get('limit')
    if not uid or not peer_uid:
        _send_cmd(conn, { 'type': 'DM_HISTORY', 'ok': False, 'error': 'missing_params' })
        return
    try:
        init_firebase_if_needed()
        thread_id = _make_thread_id(uid, peer_uid)
        ref = db.reference(f'/chats/{thread_id}/messages')
        data = ref.get() or {}
        messages = []
        if isinstance(data, dict):
            for mid, m in data.items():
                if not isinstance(m, dict):
                    continue
                messages.append({
                    'id': mid,
                    'senderUid': m.get('senderUid') or '',
                    'text': m.get('text') or '',
                    'ts': m.get('ts') or 0,
                })
        # Sort by ts asc
        messages.sort(key=lambda x: x.get('ts') or 0)
        if isinstance(limit, int) and limit > 0:
            messages = messages[-limit:]
        _send_cmd(conn, { 'type': 'DM_HISTORY', 'ok': True, 'threadId': thread_id, 'peerUid': peer_uid, 'meUid': uid, 'messages': messages })
    except Exception as e:
        _send_cmd(conn, { 'type': 'DM_HISTORY', 'ok': False, 'error': f'{e}' })


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


# Group chat commands
def _cmd_create_group(conn, obj: dict):
    uid = getattr(conn, '_chat_uid', '')
    if not uid:
        try:
            from Chat.Server.state import socket_to_uid as _s2u
        except Exception:
            from state import socket_to_uid as _s2u
        uid = _s2u.get(conn, '') if _s2u else ''
    
    if not uid:
        _send_cmd(conn, { 'type': 'GROUP_CREATED', 'ok': False, 'error': 'unauthorized' })
        return
    
    group_name = (obj.get('name') or '').strip()
    member_uids = obj.get('memberUids') or []
    
    if not group_name or not member_uids:
        _send_cmd(conn, { 'type': 'GROUP_CREATED', 'ok': False, 'error': 'missing_params' })
        return
    
    try:
        init_firebase_if_needed()
        
        # Create group ID
        import uuid
        group_id = str(uuid.uuid4())
        
        # Get member details
        members = []
        for member_uid in member_uids:
            try:
                member_email = get_email_for_uid(member_uid) or ''
                member_name = ''
                # Try to get display name from user profile
                try:
                    user_ref = db.reference(f'/users/{member_uid}')
                    user_data = user_ref.get()
                    if isinstance(user_data, dict):
                        member_name = user_data.get('displayName', '')
                except Exception:
                    pass
                
                members.append({
                    'uid': member_uid,
                    'email': member_email,
                    'displayName': member_name or member_email.split('@')[0] if member_email else 'Unknown'
                })
            except Exception:
                members.append({
                    'uid': member_uid,
                    'email': '',
                    'displayName': 'Unknown'
                })
        
        # Add creator to members
        creator_email = get_email_for_uid(uid) or ''
        creator_name = ''
        try:
            user_ref = db.reference(f'/users/{uid}')
            user_data = user_ref.get()
            if isinstance(user_data, dict):
                creator_name = user_data.get('displayName', '')
        except Exception:
            pass
        
        members.append({
            'uid': uid,
            'email': creator_email,
            'displayName': creator_name or creator_email.split('@')[0] if creator_email else 'Unknown'
        })
        
        # Create group in database
        group_data = {
            'id': group_id,
            'name': group_name,
            'createdBy': uid,
            'createdAt': {'.sv': 'timestamp'},
            'members': {member['uid']: True for member in members}
        }
        
        # Store group data
        db.reference(f'/groups/{group_id}').set(group_data)
        
        # Add group to each member's groups list
        for member in members:
            db.reference(f'/users/{member["uid"]}/groups/{group_id}').set(True)
        
        # Send success response
        _send_cmd(conn, {
            'type': 'GROUP_CREATED',
            'ok': True,
            'groupId': group_id,
            'name': group_name,
            'members': members
        })
        
        try:
            print(f"[GROUP] Created group {group_name} (id={group_id}) with {len(members)} members")
        except Exception:
            pass
            
    except Exception as e:
        _send_cmd(conn, { 'type': 'GROUP_CREATED', 'ok': False, 'error': f'{e}' })


def _cmd_list_groups(conn):
    uid = getattr(conn, '_chat_uid', '')
    if not uid:
        try:
            from Chat.Server.state import socket_to_uid as _s2u
        except Exception:
            from state import socket_to_uid as _s2u
        uid = _s2u.get(conn, '') if _s2u else ''
    
    if not uid:
        _send_cmd(conn, { 'type': 'GROUPS', 'groups': [], 'error': 'unauthorized' })
        return
    
    try:
        init_firebase_if_needed()
        
        # Get user's groups
        user_groups_ref = db.reference(f'/users/{uid}/groups')
        user_groups = user_groups_ref.get() or {}
        
        groups = []
        for group_id in user_groups.keys():
            try:
                # Get group data
                group_ref = db.reference(f'/groups/{group_id}')
                group_data = group_ref.get()
                
                if not isinstance(group_data, dict):
                    continue
                
                # Get member details
                members = []
                group_members = group_data.get('members', {})
                for member_uid in group_members.keys():
                    try:
                        member_email = get_email_for_uid(member_uid) or ''
                        member_name = ''
                        try:
                            user_ref = db.reference(f'/users/{member_uid}')
                            user_data = user_ref.get()
                            if isinstance(user_data, dict):
                                member_name = user_data.get('displayName', '')
                        except Exception:
                            pass
                        
                        members.append({
                            'uid': member_uid,
                            'email': member_email,
                            'displayName': member_name or member_email.split('@')[0] if member_email else 'Unknown'
                        })
                    except Exception:
                        members.append({
                            'uid': member_uid,
                            'email': '',
                            'displayName': 'Unknown'
                        })
                
                groups.append({
                    'id': group_id,
                    'name': group_data.get('name', 'Unknown Group'),
                    'createdBy': group_data.get('createdBy', ''),
                    'createdAt': group_data.get('createdAt', 0),
                    'members': members
                })
                
            except Exception:
                continue
        
        _send_cmd(conn, { 'type': 'GROUPS', 'groups': groups })
        
        try:
            print(f"[GROUP] LIST_GROUPS for uid={uid}: {len(groups)} groups")
        except Exception:
            pass
            
    except Exception as e:
        _send_cmd(conn, { 'type': 'GROUPS', 'groups': [], 'error': f'{e}' })


def _cmd_send_group_message(conn, obj: dict):
    uid = getattr(conn, '_chat_uid', '')
    if not uid:
        try:
            from Chat.Server.state import socket_to_uid as _s2u
        except Exception:
            from state import socket_to_uid as _s2u
        uid = _s2u.get(conn, '') if _s2u else ''
    
    group_id = (obj.get('groupId') or '').strip()
    text = (obj.get('text') or '').strip()
    
    if not uid or not group_id or not text:
        _send_cmd(conn, { 'type': 'GROUP_MESSAGE_DELIVERED', 'ok': False, 'error': 'missing_params' })
        return
    
    try:
        init_firebase_if_needed()
        
        # Check if user is member of group
        user_in_group = bool(db.reference(f'/users/{uid}/groups/{group_id}').get())
        if not user_in_group:
            _send_cmd(conn, { 'type': 'GROUP_MESSAGE_DELIVERED', 'ok': False, 'error': 'not_member' })
            return
        
        # Store message in database
        msg_ref = db.reference(f'/groups/{group_id}/messages').push({
            'senderUid': uid,
            'text': text,
            'ts': {'.sv': 'timestamp'},
        })
        
        # Get group members and deliver to online members
        group_data = db.reference(f'/groups/{group_id}').get() or {}
        group_members = group_data.get('members', {})
        
        for member_uid in group_members.keys():
            if member_uid == uid:  # Skip sender
                continue
            try:
                member_socket = uid_to_socket.get(member_uid)
                if member_socket is not None:
                    _send_cmd(member_socket, {
                        'type': 'GROUP_MESSAGE',
                        'groupId': group_id,
                        'senderUid': uid,
                        'text': text
                    })
            except Exception:
                pass
        
        _send_cmd(conn, { 'type': 'GROUP_MESSAGE_DELIVERED', 'ok': True, 'groupId': group_id })
        
    except Exception as e:
        _send_cmd(conn, { 'type': 'GROUP_MESSAGE_DELIVERED', 'ok': False, 'error': f'{e}' })


def _cmd_load_group_history(conn, obj: dict):
    uid = getattr(conn, '_chat_uid', '')
    if not uid:
        try:
            from Chat.Server.state import socket_to_uid as _s2u
        except Exception:
            from state import socket_to_uid as _s2u
        uid = _s2u.get(conn, '') if _s2u else ''
    
    group_id = (obj.get('groupId') or '').strip()
    limit = obj.get('limit', 50)
    
    if not uid or not group_id:
        _send_cmd(conn, { 'type': 'GROUP_HISTORY', 'ok': False, 'error': 'missing_params' })
        return
    
    try:
        init_firebase_if_needed()
        # Allow loading history even if user left the group (read-only view)
        
        # Get group messages
        messages_ref = db.reference(f'/groups/{group_id}/messages')
        data = messages_ref.get() or {}
        messages = []
        
        if isinstance(data, dict):
            for mid, m in data.items():
                if not isinstance(m, dict):
                    continue
                messages.append({
                    'id': mid,
                    'senderUid': m.get('senderUid') or '',
                    'text': m.get('text') or '',
                    'ts': m.get('ts') or 0,
                })
        
        # Sort by timestamp ascending
        messages.sort(key=lambda x: x.get('ts') or 0)
        
        # Apply limit
        if isinstance(limit, int) and limit > 0:
            messages = messages[-limit:]
        
        _send_cmd(conn, {
            'type': 'GROUP_HISTORY',
            'ok': True,
            'groupId': group_id,
            'messages': messages
        })
        
    except Exception as e:
        _send_cmd(conn, { 'type': 'GROUP_HISTORY', 'ok': False, 'error': f'{e}' })


# --- Additional group commands: leave and list members ---
def _require_uid(conn) -> str:
    uid = getattr(conn, '_chat_uid', '')
    if uid:
        return uid
    try:
        from Chat.Server.state import socket_to_uid as _s2u  # type: ignore
    except Exception:
        from state import socket_to_uid as _s2u  # type: ignore
    try:
        return _s2u.get(conn, '')
    except Exception:
        return ''


def _cmd_leave_group(conn, obj: dict):
    uid = _require_uid(conn)
    group_id = (obj.get('groupId') or '').strip()
    if not uid or not group_id:
        _send_cmd(conn, { 'type': 'LEAVE_GROUP_OK', 'ok': False, 'error': 'missing_params' })
        return
    try:
        init_firebase_if_needed()
        # Remove from group members and user's group list
        db.reference(f'/groups/{group_id}/members/{uid}').delete()
        db.reference(f'/users/{uid}/groups/{group_id}').delete()
        # Compose system text and persist as a system message
        try:
            leaver_email = get_email_for_uid(uid) or ''
        except Exception:
            leaver_email = uid
        sys_text = f"{leaver_email} đã rời nhóm"
        try:
            db.reference(f'/groups/{group_id}/messages').push({
                'senderUid': '',
                'system': True,
                'text': sys_text,
                'ts': {'.sv': 'timestamp'},
            })
        except Exception:
            pass
        # Notify remaining online members in realtime
        try:
            mems = db.reference(f'/groups/{group_id}/members').get() or {}
            if isinstance(mems, dict):
                for m_uid, linked in mems.items():
                    if not linked:
                        continue
                    try:
                        peer_socket = uid_to_socket.get(m_uid)
                        if peer_socket is not None:
                            _send_cmd(peer_socket, { 'type': 'GROUP_SYSTEM', 'groupId': group_id, 'event': 'member_left', 'uid': uid, 'text': sys_text })
                    except Exception:
                        pass
        except Exception:
            pass
        _send_cmd(conn, { 'type': 'LEAVE_GROUP_OK', 'ok': True, 'groupId': group_id })
    except Exception as e:
        _send_cmd(conn, { 'type': 'LEAVE_GROUP_OK', 'ok': False, 'error': f'{e}' })


def _cmd_list_group_members(conn, obj: dict):
    uid = _require_uid(conn)
    group_id = (obj.get('groupId') or '').strip()
    if not uid or not group_id:
        _send_cmd(conn, { 'type': 'GROUP_MEMBERS', 'ok': False, 'members': [], 'error': 'missing_params' })
        return
    try:
        init_firebase_if_needed()
        # Require membership to view
        in_group = bool(db.reference(f'/users/{uid}/groups/{group_id}').get())
        if not in_group:
            _send_cmd(conn, { 'type': 'GROUP_MEMBERS', 'ok': False, 'members': [], 'error': 'not_member' })
            return
        mems = db.reference(f'/groups/{group_id}/members').get() or {}
        members: list[dict] = []
        if isinstance(mems, dict):
            for m_uid, linked in mems.items():
                if not linked:
                    continue
                try:
                    email = get_email_for_uid(m_uid) or ''
                except Exception:
                    email = ''
                members.append({ 'uid': m_uid, 'email': email })
        _send_cmd(conn, { 'type': 'GROUP_MEMBERS', 'ok': True, 'groupId': group_id, 'members': members })
    except Exception as e:
        _send_cmd(conn, { 'type': 'GROUP_MEMBERS', 'ok': False, 'members': [], 'error': f'{e}' })

