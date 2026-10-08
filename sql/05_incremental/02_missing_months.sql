WITH present AS (
    SELECT
        split_part(file, '/', 3) AS taxi_type,
        CAST(split_part(file, '/', 4) AS INTEGER) AS year,
        CAST(regexp_extract(file, '-(\d{2})\.parquet$', 1) AS INTEGER) AS month
    FROM glob('data/raw/*/*/*.parquet')
),
expected AS (
    SELECT t.taxi_type, y.year, m.month
    FROM (SELECT DISTINCT taxi_type FROM present) AS t
    CROSS JOIN (SELECT DISTINCT year FROM present) AS y
    CROSS JOIN range(1, 13) AS m(month)
)
SELECT
    e.taxi_type,
    e.year,
    count(p.month) AS months_present,
    list(e.month ORDER BY e.month) FILTER (WHERE p.month IS NULL) AS missing_months
FROM expected AS e
LEFT JOIN present AS p USING (taxi_type, year, month)
GROUP BY e.taxi_type, e.year
ORDER BY e.taxi_type DESC, e.year;
