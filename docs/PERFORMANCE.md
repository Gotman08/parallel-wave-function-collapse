# Performance evidence

The current CPU experiment, exact commands, raw measurements and limitations are in [results.md](results.md). It compares the existing serial and OpenMP backends with a fixed sample, tile size, seed set and CPU affinity policy.

Historical Romeo, GPU and optimization-pass data remain under `results/` and in the original report. They were not rerun on their original machines. The old analysis is retained in Git history at `f179ae0`; its speedups and explanations are not presented as results of the new environment.
