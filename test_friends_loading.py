#!/usr/bin/env python3
"""
Test script để kiểm tra việc tải danh sách bạn bè trong tab tạo nhóm
"""

import sys
import os

# Add the Chat directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'Chat'))

def main():
    print("=== TEST TAI DANH SACH BAN BE ===")
    print()
    print("CAC BUOC KIEM TRA:")
    print("1. Chay server: python Chat/Server/main.py")
    print("2. Chay client: python Chat/Client/run.py")
    print("3. Dang nhap voi tai khoan")
    print("4. Ket ban voi it nhat 1 nguoi khac")
    print("5. Chuyen sang tab 'Tao nhom'")
    print("6. Kiem tra danh sach ban be co hien thi khong")
    print()
    print("KIEM TRA CU THE:")
    print("- Tab 'Tao nhom' se tu dong tai danh sach ban be")
    print("- Neu chua co ban be, se hien thi thong bao 'Chua co ban be nao'")
    print("- Neu co ban be, se hien thi checkbox cho tung ban be")
    print("- Nhan 'Lam moi danh sach' de tai lai danh sach")
    print()
    print("TROUBLESHOOTING:")
    print("- Neu khong thay danh sach ban be:")
    print("  + Kiem tra da ket ban chua")
    print("  + Nhan 'Lam moi danh sach'")
    print("  + Chuyen sang tab 'Ban be' roi quay lai")
    print("- Neu co loi ket noi:")
    print("  + Kiem tra server co chay khong")
    print("  + Kiem tra Firebase connection")
    print()
    print("LUU Y:")
    print("- Danh sach ban be se duoc tai tu dong khi mo tab")
    print("- Danh sach se duoc cap nhat khi co ban be moi")
    print("- Chi hien thi ban be da ket ban thanh cong")

if __name__ == '__main__':
    main()
