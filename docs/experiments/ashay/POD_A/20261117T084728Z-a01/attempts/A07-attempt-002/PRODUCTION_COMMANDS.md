# Executed finite A07 commands

PRODUCTION_COMMANDS.json contains actual interpreter/script paths, all flags and immutable source identities for every job. CPU-only worker7.py supervises a single declared R5 job, removes credential variables, disables CUDA and caps AS32GiB/four BLAS threads. fit_other_five.py uses at most two workers. Initial invocation names exactly TF/final_norm/seed42 and splice/final_norm/seed42; five subsequent task batches reuse these seals without refitting. build_other_five_cache.py concatenates verified A06 chunks unchanged. INITIAL_PRODUCTION_GATE.json was PASS before remaining task batches.

All 390 units are sealed and excluded from automatic rerun. Do not rerun a head to fix a report or path. Unsealed output is quarantined, never trusted by existence alone. Resume with the exact manifest/source/cache identity; allocate a new job name for a justified retry and preserve old diagnostics. No A08 executable is dispatched.
