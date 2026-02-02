from pyspark.sql import SparkSession


def get_spark():
    spark = (
        SparkSession.builder.appName("iceberg")
        # Khai báo 1 Catalog
        .config("spark.sql.catalog.demo1", "org.apache.iceberg.spark.SparkCatalog")
        # Định nghĩa là REST
        .config(
            "spark.sql.catalog.demo1.catalog-impl",
            "org.apache.iceberg.rest.RESTCatalog",
        )
        # Địa chỉ Iceberg REST Catalog service. rest tên container
        .config("spark.sql.catalog.demo1.uri", "http://rest:8181")
        # Root path lưu table IceBerg
        .config("spark.sql.catalog.demo1.warehouse", "s3://warehouse/")
        .config("spark.sql.catalog.demo1.io-impl", "org.apache.iceberg.aws.s3.S3FileIO")
        # Chỉ định minIO
        .config("spark.sql.catalog.demo1.s3.endpoint", "http://minio:9000")
        .config("spark.sql.catalog.demo1.s3.path-style-access", "true")
        # Demo sẽ là spark default catalog
        .config("spark.sql.defaultCatalog", "demo1")
        .getOrCreate()
    )

    return spark
