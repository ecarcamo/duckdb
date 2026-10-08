CREATE OR REPLACE VIEW trips_clean AS
SELECT
    *,
    CASE
        WHEN dropoff_datetime > pickup_datetime
            THEN date_diff('second', pickup_datetime, dropoff_datetime) / 60.0
    END AS duration_minutes
FROM trips
WHERE pickup_datetime >= make_timestamp(source_year, source_month, 1, 0, 0, 0)
  AND pickup_datetime < make_timestamp(source_year, source_month, 1, 0, 0, 0) + INTERVAL 1 MONTH
  AND (
      dropoff_datetime > pickup_datetime
      OR (VendorID = 7 AND dropoff_datetime = pickup_datetime)
  )
  AND dropoff_datetime <= pickup_datetime + INTERVAL 6 HOUR
  AND trip_distance > 0
  AND trip_distance <= 100
  AND fare_amount >= 0
  AND total_amount > 0
  AND total_amount <= 1000;
