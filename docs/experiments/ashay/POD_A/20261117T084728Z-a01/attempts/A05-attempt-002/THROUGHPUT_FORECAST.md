# R5 measured production forecast

The prior R4/R6 production extraction analog is [602.6, 626.0] seconds for one candidate across H3 and other-five, including startup and capture. A planning allowance of [452.0, 1565.1] seconds accounts for variability; it is neither a deadline nor a GPU cap. The A04 64.56-second qualification run is excluded.

R5 other-five has 390 heads versus 780 in the measured A07: linear fitting analog 397.8 seconds, with convergence-dependent uncertainty. Production uses 7,020 initial CV/final solver calls; the 36 full-CV audit refits add 540 initial calls separately. Exact measured compression/upload/download/member-hash timings and sources are in THROUGHPUT_FORECAST.json. New comparisons and report rendering require separate stage measurements.

500 GB persistent capacity, actual allocated baseline 217720445952 bytes; conservative coexistence peak 280935537750 bytes plus 50000000000 bytes protected free headroom fits. Two CPU workers with four BLAS threads and 32 GiB address-space limits each fit the current cgroup. Recheck actual capacity and locks before any approved production. No rate, rental start or cost is invented.
