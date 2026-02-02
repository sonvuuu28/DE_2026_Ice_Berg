from spark_session import *

spark = get_spark()

print("=====SHOW CATALOGS=====")
spark.sql("show catalogs;").show()


print("=====SHOW DATABASES=====")
spark.sql("create database if not exists demo1.db")
spark.sql("show databases in demo1;").show()


print("=====SHOW TABLES=====")
spark.sql("show tables in demo1.db;").show()
spark.sql("drop table if exists demo1.db.taxis")
spark.sql("show tables in demo1.db;").show()


# df = spark.read.parquet("/home/iceberg/data/yellow_tripdata_2021-04.parquet")
# df.writeTo("demo1.db.taxis").create()
