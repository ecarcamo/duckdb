SELECT
    taxi_type,
    count(*) AS duplicated_groups,
    sum(copies - 1) AS extra_rows
FROM (
    SELECT taxi_type, row_hash, count(*) AS copies
    FROM (SELECT taxi_type, hash(t) AS row_hash FROM trips AS t)
    GROUP BY taxi_type, row_hash
    HAVING count(*) > 1
)
GROUP BY taxi_type
ORDER BY taxi_type DESC;
