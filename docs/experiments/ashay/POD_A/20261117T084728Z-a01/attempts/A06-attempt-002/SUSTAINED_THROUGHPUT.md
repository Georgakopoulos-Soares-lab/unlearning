# Measured R5 throughput

Production has 14965 real rows/1873 physical8 forwards. Measured GPU-stage wall including model load, validation and I/O: 366.801 seconds; synchronized forward/capture time: 202.559 seconds. TRAIN qualification is separate: 4 forwards. No billable-GPU-time or cost is inferred.

H3 production has 78 final heads and the same number of unchanged-base applications. CPU per-unit time sums differ from pool elapsed; exact supervised command wall and PID/start records are in RESOURCE_MEASUREMENTS.json. Six supplemental full-CV audit refits are separate from production. CPU worker bounds remain two workers, four BLAS threads each and32 GiB AS per worker.

Allocated workspace 224668375040 bytes under freshly checked500GB provider quota; no historical deletion or purchase. Compression, upload, fresh logical archive transfer, all-member hashing and restored computation are separately measured. Original/rental starts, rate and cost remain null; no deadline/cap/reserve.
