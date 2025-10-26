Mô hình lai 

1. Kiến trúc Hybrid

Khi người nhận ONLINE:
Tin nhắn được lưu vào Firebase
Tin nhắn được gửi real-time qua TCP
Người nhận nhận được ngay lập tức

Khi người nhận OFFLINE:
Tin nhắn được lưu vào Firebase
Không có gửi qua TCP (vì không có socket)
Khi người nhận online lại, sẽ tải tin nhắn từ Firebase

2. Ưu điểm của kiến trúc này:
Real-time: Tin nhắn đến ngay khi người nhận online
Persistence: Tin nhắn không bị mất khi server restart
Offline support: Tin nhắn được lưu khi người nhận offline
Scalability: Firebase xử lý lưu trữ, server chỉ xử lý real-time