SELECT
    taxi_type,
    VendorID AS vendor_id,
    count(*) AS trips,
    round(100.0 * count(*) FILTER (WHERE abs(
        fare_amount + extra + mta_tax + tip_amount + tolls_amount + improvement_surcharge
        + coalesce(congestion_surcharge, 0) + coalesce(Airport_fee, 0) + coalesce(cbd_congestion_fee, 0)
        - total_amount) < 0.01) / count(*), 2) AS pct_components_match_total,
    round(100.0 * count(*) FILTER (WHERE abs(
        fare_amount + extra + mta_tax + tip_amount + tolls_amount + improvement_surcharge
        - total_amount) < 0.01) / count(*), 2) AS pct_match_without_surcharges
FROM trips_clean
GROUP BY ALL
ORDER BY taxi_type DESC, vendor_id;
