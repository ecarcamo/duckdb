CREATE OR REPLACE VIEW trips AS
SELECT
    'yellow' AS taxi_type,
    CAST(regexp_extract(filename, '_(\d{4})-\d{2}\.parquet$', 1) AS INTEGER) AS source_year,
    CAST(regexp_extract(filename, '_\d{4}-(\d{2})\.parquet$', 1) AS INTEGER) AS source_month,
    * EXCLUDE (filename) RENAME (
        tpep_pickup_datetime AS pickup_datetime,
        tpep_dropoff_datetime AS dropoff_datetime
    )
FROM yellow_raw
UNION ALL BY NAME
SELECT
    'green' AS taxi_type,
    CAST(regexp_extract(filename, '_(\d{4})-\d{2}\.parquet$', 1) AS INTEGER) AS source_year,
    CAST(regexp_extract(filename, '_\d{4}-(\d{2})\.parquet$', 1) AS INTEGER) AS source_month,
    * EXCLUDE (filename) RENAME (
        lpep_pickup_datetime AS pickup_datetime,
        lpep_dropoff_datetime AS dropoff_datetime
    )
FROM green_raw;
