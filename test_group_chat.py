#!/usr/bin/env python3
"""
Demo script để test chức năng chat nhóm
Chạy script này để test các tính năng:
1. Tạo nhóm chat
2. Gửi tin nhắn nhóm
3. Xem lịch sử nhóm
"""

import sys
import os

# Add the Chat directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'Chat'))

def main():
    print("=== DEMO CHAT NHOM ===")
    print("Chuc nang da duoc them vao ung dung chat:")
    print()
    print("1. TAB 'TAO NHOM':")
    print("   - Nhap ten nhom")
    print("   - Chon ban be tu danh sach")
    print("   - Nhan 'Tao nhom' de tao nhom moi")
    print()
    print("2. TAB 'NHOM CHAT':")
    print("   - Xem danh sach cac nhom da tham gia")
    print("   - Nhan 'Mo nhom' de vao chat nhom")
    print("   - Nhan 'Tao nhom moi' de chuyen sang tab tao nhom")
    print()
    print("3. CHAT NHOM:")
    print("   - Gui tin nhan trong nhom")
    print("   - Xem lich su tin nhan")
    print("   - Hien thi thanh vien nhom")
    print()
    print("CACH SU DUNG:")
    print("1. Chay server: python Chat/Server/main.py")
    print("2. Chay client: python Chat/Client/run.py")
    print("3. Dang nhap voi 2+ tai khoan khac nhau")
    print("4. Ket ban giua cac tai khoan")
    print("5. Tao nhom va test chat nhom")
    print()
    print("TINH NANG MOI:")
    print("+ Tao nhom chat voi ten tuy chinh")
    print("+ Chon ban be de them vao nhom")
    print("+ Chat nhom real-time")
    print("+ Luu tru lich su tin nhan")
    print("+ Hien thi danh sach nhom")
    print("+ Quan ly thanh vien nhom")
    print()
    print("Database Schema:")
    print("- /groups/{groupId}: Thong tin nhom")
    print("- /groups/{groupId}/messages: Tin nhan nhom")
    print("- /users/{uid}/groups: Danh sach nhom cua user")

if __name__ == '__main__':
    main()
