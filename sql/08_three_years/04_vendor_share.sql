SELECT
    taxi_type,
    source_year AS year,
    VendorID AS vendor_id,
    count(*) AS trips,
    round(100.0 * count(*) / sum(count(*)) OVER (PARTITION BY taxi_type, source_year), 2) AS pct_of_year
FROM trips_clean
GROUP BY taxi_type, source_year, VendorID
ORDER BY taxi_type DESC, year, vendor_id;
