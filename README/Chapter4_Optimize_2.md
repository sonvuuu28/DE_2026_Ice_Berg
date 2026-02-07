# Optimizing the Performance


## 📖 Table of Contents
1. [I. Metrics Collection](#i-metrics-collection)
2. [II. Rewriting Manifests](#ii-rewriting-manifests)



## I. Metrics Collection
Như đã biết metadata file theo dõi các cột để pruning/query optimization => Có thể hạn chế cách theo dõi các cột.

```sql
ALTER TABLE catalog.db.students SET TBLPROPERTIES (
    'write.metadata.metrics.column.col1'='none',
    'write.metadata.metrics.column.col2'='full',
    'write.metadata.metrics.column.col3'='counts',
    'write.metadata.metrics.column.col4'='truncate(16)',
);
```

* `none`: Ko theo dõi
* `full`: Theo dõi đủ
* `counts`: Theo dõi các chỉ số như đếm null values, distinct values, total values (ko quan tâm min, max)
* `truncate`: Theo dõi n kí tự

----

## II. Rewriting Manifests
#### 1. Lí do
- Như đã biết manifest file chứa path của các datafile.
- `Vấn đề:` 1 manifest file quản lý quá ít datafile thì sao? tốn công IO đọc.
- `Giải pháp:` 1 manifest quản lý nhiều datafile hơn. Hạn chế tốn công đọc metadata.

#### 2. Code
```sql
CALL catalog.system.rewrite_manifests('MyTable')
```

* `rewrite_manifests`: hàm rewrite lại manifest file.

Trong trường hợp gặp vấn đề về memory (Spark executor OOM), có thể tắt Spark caching bằng cách truyền thêm tham số false:

```sql
CALL catalog.system.rewrite_manifests('MyTable', false)
```

#### 3. Lưu ý
- Nên rewrite datafile trước rồi mới nghĩ rewrite manifest file để tránh ko tối ưu.

----


## III. Optimizing Storage
Snapshot được sinh ra khi có dữ liệu mới insert. Nếu ko clean sẽ phình ác.

#### 1. Expire Snapshots

```sql
CALL catalog.system.expire_snapshots(
  'MyTable',
  TIMESTAMP '2023-02-01 00:00:00.000',
  100
)
```

Ý nghĩa:
* Xoá snapshot ≤ timestamp
* Nhưng vẫn giữ ít nhất 100 snapshot gần nhất

```sql
CALL catalog.system.expire_snapshots(
  table => 'MyTable',
  snapshot_ids => ARRAY(53)
)
```


| Tham số                  | Ý nghĩa                                         |
| ------------------------ | ----------------------------------------------- |
| `table`                  | Table cần dọn                                   |
| `older_than`             | Xoá snapshot trước mốc thời gian                |
| `retain_last`            | Số snapshot tối thiểu giữ lại                   |
| `snapshot_ids`           | Snapshot chỉ định                               |
| `max_concurrent_deletes` | Số thread xoá file                              |
| `stream_results`         | Stream danh sách file xoá về driver (tránh OOM) |



#### 2. Orphan files
Trong quá trình ingest dự liệu lỡ failed job, một số file sẽ bị mồ côi. Nhưng file mồ côi lại ko được trỏ vào snapshot nào. Nên phải tự dọn.

```sql
CALL catalog.system.remove_orphan_files(table => 'MyTable')
```

| Tham số                  | Ý nghĩa                 |
| ------------------------ | ----------------------- |
| `table`                  | Table cần dọn           |
| `older_than`             | Chỉ xoá file cũ hơn mốc |
| `location`               | Directory cần scan      |
| `dry_run`                | Chỉ list, không xoá     |
| `max_concurrent_deletes` | Thread xoá              |


## IV. Write Distribution Mode
Trong quá trình ghi song song từ các PP (Parallel Processing) sẽ tạo ra rất nhiều file do phân tasks theo cơ chế Spark.
Việc này sẽ ảnh hưởng việc lưu trữ và truy vấn sau này.
Ice Berg cho table được set property để khi Spark xử lý xong yêu cầu làm thêm bước shuffle => ra luật để các PP shuffle có lợi nhất

```sql
ALTER TABLE catalog.MyTable SET TBLPROPERTIES (
    'write.distribution-mode'='hash',
    'write.delete.distribution-mode'='none',
    'write.update.distribution-mode'='range',
    'write.merge.distribution-mode'='hash',
);
```

| Operation | Mode  | Lý do                 |
| --------- | ----- | --------------------- |
| INSERT    | hash  | Ít file, ổn định      |
| DELETE    | none  | Tránh shuffle         |
| UPDATE    | range | File gọn, query nhanh |
| MERGE     | hash  | Cân bằng hiệu năng    |


-----

## IV. Object Storage
Các Object Storage trông giống như tổ chức theo đường dẫn thư mục.

Nếu nhiều request song song truy cập các file **cùng một prefix**
→ có thể gây nghẽn object storage.

```
s3://bucket/database/table/field=value1/datafile1.parquet
s3://bucket/database/table/field=value1/datafile2.parquet
s3://bucket/database/table/field=value1/datafile3.parquet
```

Iceberg có setting để **đánh hash vào prefix**, giúp các file trong cùng partition được phân tán ra nhiều prefix khác nhau:

```sql
ALTER TABLE catalog.MyTable SET TBLPROPERTIES (
  'write.object-storage.enabled' = true
);
```

Khi đó layout vật lý sẽ như sau:

```
s3://bucket/4809098/database/table/field=value1/datafile1.parquet
s3://bucket/5840329/database/table/field=value1/datafile2.parquet
s3://bucket/2342344/database/table/field=value1/datafile3.parquet
```

👉 Nhờ vậy, các request được **chia đều**, tránh nghẽn do quá nhiều request dồn vào cùng một prefix.


👍 **Rất tốt rồi — đúng bản chất ~95%**.
Mình chỉ **chỉnh nhẹ vài chỗ cho chuẩn thuật ngữ và logic**, không thêm ý mới nhé.

---

## V. Bloom Filter

Bloom filter là metadata giúp kiểm tra nhanh một datafile có thể chứa giá trị A hay không thông qua một dãy bit (0, 1).

* Nếu Bloom filter nói không có → chắc chắn không có
* Nếu nói có thể có → chưa chắc, vẫn phải scan file

---

### Cơ chế

Ban đầu, Bloom filter là một dãy bit toàn 0:

```
A = [0 0 0 0 0 0 0 0 0 0]
```

Giả sử datafile có các `user_id`:

```
[12, 25, 88]
```

---

**Insert dữ liệu**

* `Hash(12)` → vị trí 3 → bật bit 3

```
A = [0 0 0 1 0 0 0 0 0 0]
```

* `Hash(25)` → vị trí 7 → bật bit 7

```
A = [0 0 0 1 0 0 0 1 0 0]
```

* `Hash(88)` → vị trí 3 → trùng → bit đã bật, giữ nguyên

```
A = [0 0 0 1 0 0 0 1 0 0]
```

👉 Bloom filter **chỉ bật bit**, không lưu giá trị thật.

---

### Khi người dùng query

* `user_id = 25`
  → `Hash(25)` → vị trí 7 → bit = 1
  → có thể có → scan file

* `user_id = 99`
  → `Hash(99)` → vị trí 4 → bit = 0
  → chắc chắn không có → skip file

---

### Lưu ý (trade-off)

* Nếu **dữ liệu nhiều**, **cardinality cao**
* Nhưng **dãy bit quá ngắn**

👉 Dễ xảy ra **false positive** (đụng hash)
👉 Tốn thêm:

* Metadata (Bloom filter)
* Một bước check trước khi đọc file

```sql
ALTER TABLE catalog.MyTable SET TBLPROPERTIES (
  'write.parquet.bloom-filter-enabled.column.col1'= true,
  'write.parquet.bloom-filter-max-bytes'= 1048576
);
```
