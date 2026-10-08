# Resultados del benchmark

Archivo generado por `scripts/benchmark.py`. Tiempos en segundos. «Mediana» es la mediana de
5 ejecuciones repetidas, medidas después de una primera ejecución que se reporta
aparte. La aceleración es tiempo con Parquet dividido entre tiempo con la tabla materializada.

## Datos y materialización

| Escala | Archivos | Viajes | Parquet (MiB) | Tabla DuckDB (MiB) | Tiempo de materialización (s) |
|---|---|---|---|---|---|
| 1 mes (ene 2026) | 2 | 3,765,161 | 62.1 | 102.3 | 0.90 |
| Año 2026 | 16 | 30,040,469 | 495.7 | 816.3 | 3.01 |
| Todos los años | 40 | 71,870,407 | 1,171.7 | 1,972.0 | 7.46 |

## 1 mes (ene 2026) (3,765,161 viajes)

| Consulta | Parquet: mediana | Tabla: mediana | Aceleración | Parquet: primera | Tabla: primera |
|---|---|---|---|---|---|
| Q1 Conteo por tipo | 0.006 | 0.002 | 2.4× | 0.006 | 0.005 |
| Q2 Volumen mensual | 0.126 | 0.039 | 3.2× | 0.112 | 0.041 |
| Q3 Hora y día de la semana | 0.155 | 0.043 | 3.6× | 0.161 | 0.044 |
| Q4 Percentiles del viaje | 0.721 | 0.648 | 1.1× | 0.781 | 0.666 |
| Q5 Medio de pago | 0.136 | 0.055 | 2.5× | 0.139 | 0.056 |
| Q6 Zonas principales (1 join) | 0.166 | 0.036 | 4.6× | 0.155 | 0.038 |
| Q7 Aeropuertos (2 joins) | 0.182 | 0.049 | 3.7× | 0.197 | 0.042 |
| Q8 Un solo día (filtro selectivo) | 0.017 | 0.002 | 7.8× | 0.019 | 0.002 |

## Año 2026 (30,040,469 viajes)

| Consulta | Parquet: mediana | Tabla: mediana | Aceleración | Parquet: primera | Tabla: primera |
|---|---|---|---|---|---|
| Q1 Conteo por tipo | 0.009 | 0.008 | 1.1× | 0.008 | 0.009 |
| Q2 Volumen mensual | 0.320 | 0.251 | 1.3× | 0.327 | 0.268 |
| Q3 Hora y día de la semana | 0.380 | 0.264 | 1.4× | 0.398 | 0.249 |
| Q4 Percentiles del viaje | 5.467 | 5.480 | 1.0× | 6.385 | 5.458 |
| Q5 Medio de pago | 0.349 | 0.429 | 0.8× | 0.506 | 0.422 |
| Q6 Zonas principales (1 join) | 0.381 | 0.215 | 1.8× | 0.386 | 0.228 |
| Q7 Aeropuertos (2 joins) | 0.481 | 0.326 | 1.5× | 0.480 | 0.320 |
| Q8 Un solo día (filtro selectivo) | 0.028 | 0.003 | 10.0× | 0.031 | 0.003 |

## Todos los años (71,870,407 viajes)

| Consulta | Parquet: mediana | Tabla: mediana | Aceleración | Parquet: primera | Tabla: primera |
|---|---|---|---|---|---|
| Q1 Conteo por tipo | 0.014 | 0.019 | 0.7× | 0.014 | 0.029 |
| Q2 Volumen mensual | 0.664 | 0.540 | 1.2× | 0.780 | 0.661 |
| Q3 Hora y día de la semana | 0.809 | 0.576 | 1.4× | 0.839 | 0.561 |
| Q4 Percentiles del viaje | 16.738 | 15.553 | 1.1× | 16.154 | 16.679 |
| Q5 Medio de pago | 0.709 | 0.925 | 0.8× | 0.942 | 0.925 |
| Q6 Zonas principales (1 join) | 0.814 | 0.471 | 1.7× | 0.813 | 0.468 |
| Q7 Aeropuertos (2 joins) | 1.004 | 0.757 | 1.3× | 1.004 | 0.750 |
| Q8 Un solo día (filtro selectivo) | 0.046 | 0.004 | 10.8× | 0.048 | 0.007 |
