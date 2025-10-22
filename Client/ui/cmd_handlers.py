from tkinter import messagebox


def handle_find_user_result(win, obj):
    found = bool(obj.get('found'))
    if not found:
        win._found_user_email = None
        try:
            win.tab_find.disable_send()
            win.tab_find.hide_result()
        except Exception:
            pass
        error = obj.get('error') or 'Người dùng không tồn tại.'
        if 'not_found' in error:
            error = 'Người dùng không tồn tại.'
        messagebox.showerror('Tìm bạn', error)
        return

    email = obj.get('email') or ''
    display_name = obj.get('displayName') or (email.split('@', 1)[0] if '@' in email else email)
    win._found_user_email = email

    # Disable sending to self or existing friend
    email_lower = email.strip().lower()
    can_send = True
    try:
        if win.current_user_email and email_lower == (win.current_user_email or '').strip().lower():
            can_send = False
        elif any((email_lower == (f.get('email') or '').strip().lower()) for f in (win._friends or [])):
            can_send = False
            messagebox.showinfo('Kết bạn', 'Người dùng này đã là bạn của bạn.')
    except Exception:
        pass

    try:
        win.tab_find.show_result(email, display_name, can_send=can_send)
    except Exception:
        pass
    messagebox.showinfo('Tìm bạn', f'Đã tìm thấy người dùng: {email}')


def handle_friends(win, obj):
    friends = obj.get('friends') or []
    win._friends = friends
    try:
        win.tab_friends.set_friends(friends)
    except Exception:
        pass


def handle_friend_requests(win, obj):
    requests = obj.get('requests') or []
    win._incoming_requests = requests
    emails = []
    for r in requests:
        email = r.get('fromEmail') or r.get('fromUid') or ''
        if email:
            emails.append(email)
    try:
        win.tab_profile.set_friend_requests(emails)
    except Exception:
        pass


def handle_friend_request_sent(win, obj):
    ok = bool(obj.get('ok'))
    if ok:
        messagebox.showinfo('Yêu cầu kết bạn', f'Đã gửi yêu cầu kết bạn đến {win._found_user_email}.')
        try:
            win.tab_find.disable_send()
            win.tab_find.hide_result()
        except Exception:
            pass
    else:
        err = obj.get('error') or 'Không gửi được yêu cầu.'
        # Chuẩn hóa lỗi user-friendly
        if err == 'already_friends':
            err = 'Hai người đã là bạn.'
        elif err == 'already_requested':
            err = 'Bạn đã gửi yêu cầu trước đó.'
        messagebox.showerror('Yêu cầu kết bạn', err)


def handle_friend_request_accepted(win, obj):
    ok = bool(obj.get('ok'))
    if ok:
        try:
            win.tab_profile.remove_selected_request()
        except Exception:
            pass
        messagebox.showinfo('Kết bạn', 'Đã chấp nhận lời mời kết bạn.')
        # Refresh lists
        try:
            win.network.send_command({ 'type': 'LIST_FRIENDS' })
            win.network.send_command({ 'type': 'FRIEND_REQUESTS' })
        except Exception:
            pass
        try:
            win.notebook.select(win.tab_friends)
        except Exception:
            pass
    else:
        err = obj.get('error') or 'Không chấp nhận được lời mời.'
        messagebox.showerror('Kết bạn', err)


def handle_friend_request_rejected(win, obj):
    ok = bool(obj.get('ok'))
    if ok:
        try:
            win.tab_profile.remove_selected_request()
        except Exception:
            pass
        messagebox.showinfo('Kết bạn', 'Đã từ chối lời mời kết bạn.')
        try:
            win.network.send_command({ 'type': 'FRIEND_REQUESTS' })
        except Exception:
            pass
    else:
        err = obj.get('error') or 'Không từ chối được lời mời.'
        messagebox.showerror('Kết bạn', err)


def handle_dm(win, obj):
    from_uid = obj.get('fromUid') or ''
    text = obj.get('text') or ''
    thread_id = obj.get('threadId') or None
    tab = win._find_dm_tab_by_thread_or_uid(thread_id, from_uid)
    if tab is None:
        friend = { 'uid': from_uid, 'email': '', 'displayName': '' }
        win._open_dm_from_friend(friend)
        tab = win._find_dm_tab_by_thread_or_uid(None, from_uid)
    if tab is None:
        return
    transcript = getattr(tab, 'transcript', None)
    if transcript is None:
        return
    try:
        transcript.configure(state="normal")
        transcript.insert('end', f"Friend: {text}\n")
        transcript.configure(state="disabled")
        transcript.see('end')
    except Exception:
        pass


def handle_dm_delivered(win, obj):
    if not bool(obj.get('ok')):
        err = obj.get('error') or 'Gửi tin nhắn thất bại'
        win.log(f"DM error: {err}")


def handle_dm_history(win, obj):
    if not bool(obj.get('ok')):
        return
    thread_id = obj.get('threadId') or None
    peer_uid = obj.get('peerUid') or None
    me_uid = obj.get('meUid') or ''
    messages = obj.get('messages') or []
    tab = win._find_dm_tab_by_thread_or_uid(thread_id, peer_uid)
    if tab is None:
        friend = { 'uid': peer_uid, 'email': '', 'displayName': '' }
        win._open_dm_from_friend(friend)
        tab = win._find_dm_tab_by_thread_or_uid(thread_id, peer_uid)
    if tab is None:
        return
    try:
        tab.append_history(messages, me_uid)
    except Exception:
        pass


# Group chat handlers
def handle_groups(win, obj):
    """Handle groups list response"""
    groups = obj.get('groups') or []
    win.set_groups(groups)


def handle_group_created(win, obj):
    """Handle group creation response"""
    ok = bool(obj.get('ok'))
    if ok:
        group_id = obj.get('groupId', '')
        group_name = obj.get('name', '')
        messagebox.showinfo('Tạo nhóm', f'Nhóm "{group_name}" đã được tạo thành công!')
        # Refresh groups list
        try:
            win.network.send_command({ 'type': 'LIST_GROUPS' })
        except Exception:
            pass
    else:
        error = obj.get('error') or 'Không thể tạo nhóm'
        messagebox.showerror('Tạo nhóm', error)


def handle_group_message(win, obj):
    """Handle incoming group message"""
    group_id = obj.get('groupId', '')
    sender_uid = obj.get('senderUid', '')
    text = obj.get('text', '')
    
    if not group_id or not text:
        return
    
    # Add message to group chat tab
    win.add_group_message(group_id, sender_uid, text, sender_uid)


def handle_group_history(win, obj):
    """Handle group chat history response"""
    if not bool(obj.get('ok')):
        return
    
    group_id = obj.get('groupId', '')
    messages = obj.get('messages') or []
    
    if not group_id:
        return
    
    # Load messages into group chat tab
    win.load_group_messages(group_id, messages)


