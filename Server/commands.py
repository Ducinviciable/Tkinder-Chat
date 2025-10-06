import json

try:
    from Chat.Server.firebase_admin_utils import get_user_by_email
except Exception:
    from firebase_admin_utils import get_user_by_email


def handle_command_line(conn, obj: dict):
    cmd_type = (obj.get('type') or '').upper()
    if cmd_type == 'FIND_USER':
        _cmd_find_user(conn, obj)
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


