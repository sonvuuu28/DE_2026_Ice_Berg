# LIFECYCLE WRITING & READING IN ICE BERG
## I. Quy trình ghi file
1. User gửi query (INSERT / MERGE / UPDATE…) vào query engine → engine parse và lập kế hoạch ghi.

2. Engine tương tác với catalog
→ lấy metadata hiện tại của table
→ biết schema và partition spec đang được dùng.

3. Engine ghi data files
→ ghi các datafile mới xuống file storage system (S3 / HDFS / MinIO…).

4. Engine tạo metadata mới cho lần ghi
- Tạo manifest file mới (mô tả các datafile vừa ghi)
- Tạo manifest list mới (trỏ tới các manifest file hợp lệ)
- Tạo metadata file mới (đại diện cho version mới của table)

5. Cập nhật catalog
→ catalog được update để trỏ sang metadata file mới
![alt text](images/4.png)

## 