# CATALOG
Iceberg open cho nhiều công nghệ nhưng không phải catalog nào cũng an toàn cho production vì ko đảm bảo ACID. 

---

## I. Hadoop Catalog

📁 **Metadata lưu trực tiếp trên filesystem** (HDFS / S3 / GCS)

#### Bản chất

* Mỗi table = 1 thư mục
* Metadata (`metadata.json`) nằm ngay trong thư mục đó
* Không có service trung tâm

#### Ưu điểm

* Đơn giản nhất
* Không cần cài thêm gì
* Phù hợp demo

#### Nhược điểm

* ❌ Không phù hợp multi-user / production
* ❌ Không có concurrency control tốt
* Rename table = rename folder (nguy hiểm)

#### Dùng khi

👉 Test, học Iceberg, job đơn lẻ

---

## II. Hive Catalog

🐝 **Dùng Hive Metastore để quản lý metadata**

#### Bản chất

* Iceberg **chỉ lưu pointer** tới metadata file trong Hive Metastore
* Metadata thật vẫn nằm trên object storage

#### Ưu điểm

* Phổ biến, nhiều engine hỗ trợ
* Tốt hơn Hadoop Catalog về quản lý

#### Nhược điểm

* ❌ Phụ thuộc Hive Metastore
* ❌ Scaling kém khi metadata lớn


---

## III. REST Catalog

🌐 **Catalog là một service REST API**

#### Bản chất

* Client gọi HTTP
* Catalog service quản lý metadata
* Backend có thể là DB / cloud service

#### Ưu điểm

* Cloud-native
* Tách compute và metadata
* Dễ mở rộng, dễ auth

#### Nhược điểm

* Phải deploy service
* Thêm network hop

#### Dùng khi

👉 Production hiện đại
👉 Multi-engine, multi-team
👉 Dùng Iceberg “chuẩn bài”

---

## IV. AWS Glue Catalog

☁️ **Managed Hive Metastore của AWS**

#### Bản chất

* Giống Hive Catalog
* Nhưng Metastore do AWS quản lý

#### Ưu điểm

* Không cần quản lý Hive Metastore
* Tích hợp tốt với S3, Athena, EMR

#### Nhược điểm

* ❌ Vendor lock-in AWS
* ❌ Metadata lớn → chậm

#### Dùng khi

👉 All-in AWS

---

## V. Project Nessie Catalog

🧬 **Catalog có versioning như Git**

#### Bản chất

* Metadata có **branch / tag / commit**
* Iceberg + Nessie = data version control

#### Ưu điểm

* Time travel nâng cao
* Branch để test data
* Rollback an toàn

#### Nhược điểm

* Phức tạp
* Không cần nếu chỉ CRUD data

#### Dùng khi

👉 ML / Experiment
👉 Data governance
👉 DataOps “xịn”

---

## VI. JDBC Catalog

🗄️ **Metadata lưu trong database (MySQL / Postgres)**

#### Bản chất

* Catalog state nằm trong RDBMS
* Iceberg dùng DB để quản lý table

#### Ưu điểm

* Transaction mạnh
* Dễ backup
* Không cần Hive

#### Nhược điểm

* Scale phụ thuộc DB
* Ít phổ biến hơn REST

#### Dùng khi

👉 On-prem
👉 Muốn strong consistency
👉 Không muốn Hive

---

## VII. Catalog Migration
Thực chất chỉ thay đổi Catalog file ko quan tâm 99% dữ liệu kia.

=> Iceberg làm rất tốt vì ko bị công nghệ nào khống chế

#### Dùng khi
- Case 1: Catalog cũ thiếu chức năng
- Case 2: Đổi môi trường từ onprem <-> Cloud
- Case 3: Từ thử nghiệm sang Production.

#### Apache Iceberg Catalog Migration CLI
* Tool CLI (thuộc Project Nessie)
* Chuyển Iceberg table giữa các catalog (Không copy data)
* Giữ toàn bộ history (snapshot, time travel)

#### 2 lệnh chính
`migrate` (khuyên dùng)

* Chuyển table **từ catalog cũ → catalog mới**
* **Xóa table khỏi catalog cũ**
* An toàn cho production

`register` (chỉ để test)

* Đăng ký table sang catalog mới
* Table tồn tại **ở cả 2 catalog**
* ⚠️ **Không được ghi từ 2 catalog cùng lúc** → dễ mất dữ liệu


#### Lưu ý sống còn

* ❌ Không migrate khi table đang bị ghi
* ✅ Pause job, migrate theo batch
* Viết lại job trỏ sang catalog mới sau migration

---

## VIII. Using an Engine
* Không chắc cú như xài CLI
* Dùng **Spark SQL procedures**
* Cấu hình **2 catalog (source & target)** trong cùng Spark session
* Spark **chỉ là công cụ thao tác metadata**, không tự migrate gì cả

---

#### 2 procedure chính trong Spark

`register_table()`
* Đăng ký table sang catalog mới
* **Dùng chung data files với source**
* ❌ Không nên ghi data
* ❌ Không được expire snapshot
* ✅ Giữ full history

👉 Dùng khi:
* Test migration
* Giữ nguyên location data lake


`snapshot()`

* Tạo table mới ở catalog mới
* **Metadata & thay đổi ghi ở location mới**
* Source và target **độc lập**
* ❌ Không expire snapshot ở target
* ✅ Giữ full history

👉 Dùng khi:
* Test có ghi dữ liệu
* Muốn **dần dần đổi location** (on-prem → cloud)
