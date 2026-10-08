CREATE OR REPLACE VIEW yellow_raw AS
SELECT *
FROM read_parquet('data/raw/yellow/*/*.parquet', union_by_name = true, filename = true);

CREATE OR REPLACE VIEW green_raw AS
SELECT *
FROM read_parquet('data/raw/green/*/*.parquet', union_by_name = true, filename = true);
