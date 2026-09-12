# Recorded CPU results

The 2026-09-12 run compares the existing serial and OpenMP solvers on `samples/binary_5x5.txt` with tile size 2. It records sixty solves: one warm-up and five measured solves for each of ten configurations. All sixty report success. [Runs](../bench/results/2026-09-12/runs.csv), [summary](../bench/results/2026-09-12/summary.csv), [commands](../bench/results/2026-09-12/commands.json) and [environment](../bench/results/2026-09-12/environment.json) are committed.

## Protocol

Each configuration starts a separate `wfc_benchmark` process. Its six repetitions use seeds 41 through 46. Seed 41 is the warm-up and is excluded; seeds 42 through 46 are shared by all backends and output sizes. The maximum retry count is five. Symmetry expansion, backtracking and parallel attempts retain the application's default settings.

The primary metric is the existing `SolverStats::seconds_solve`, exposed as `solve_s`. It accumulates observation/propagation work across attempts. It excludes initial rule construction, wave allocation and final grid export. `rules_s`, `total_s` and whole-process elapsed time are also preserved, with their original boundaries. The two timed workloads are 64 × 64 and 128 × 128; the backend order is serial, OpenMP 1, 2, 4, 8 threads for each size.

The machine is an Intel Core i9-13900H running Ubuntu 24.04.4 under WSL2 kernel 6.6.87.2. The guest reports twenty logical CPUs and 16149672 kB of memory. The collector chooses the first logical CPU for each distinct core reported by the guest: 0, 2, 4, 6, 8, 10, 12, 14. Each configuration uses the first requested number of those CPUs through `taskset`. The guest topology is recorded; it is not used to infer the host's physical core design.

The build uses GCC 13.3.0, C++17, Release `-O3 -march=native`, OpenMP enabled, Kokkos and LTO disabled. OpenMP uses `OMP_DYNAMIC=FALSE`, `OMP_PROC_BIND=close`, `OMP_PLACES=cores`, `OMP_WAIT_POLICY=PASSIVE` and the requested thread count. Full tool versions, cache settings, source/binary/sample hashes and exact affinity lists are in the environment and command records. [Compiler flags](../bench/results/2026-09-12/compiler-flags.txt).

## Statistics

Times are medians of the five measured seeds. Quartiles use `statistics.quantiles(..., method="inclusive")`; the IQR is Q3 minus Q1. Speedup is the serial median divided by the corresponding backend median, not a ratio of individual paired trials. The seed set is fixed, but changing the seed also changes the generated problem; the IQR therefore combines workload and timing variation.

| Grid | Backend | Median, s | Q1, s | Q3, s | Serial/backend |
|---|---|---:|---:|---:|---:|
| 64 × 64 | Serial | 0.212073 | 0.211757 | 0.214570 | 1.000 |
| 64 × 64 | OpenMP 1 | 0.219687 | 0.218470 | 0.220033 | 0.965 |
| 64 × 64 | OpenMP 2 | 0.569424 | 0.565393 | 0.571919 | 0.372 |
| 64 × 64 | OpenMP 4 | 0.947773 | 0.913040 | 0.977212 | 0.224 |
| 64 × 64 | OpenMP 8 | 1.675720 | 1.658630 | 1.688390 | 0.127 |
| 128 × 128 | Serial | 3.347680 | 3.339830 | 3.357750 | 1.000 |
| 128 × 128 | OpenMP 1 | 3.464460 | 3.444750 | 3.485200 | 0.966 |
| 128 × 128 | OpenMP 2 | 4.121690 | 3.970550 | 4.263480 | 0.812 |
| 128 × 128 | OpenMP 4 | 5.300080 | 5.186700 | 5.462660 | 0.632 |
| 128 × 128 | OpenMP 8 | 8.536540 | 8.425520 | 8.620620 | 0.392 |

No OpenMP configuration improved on serial in this experiment. This is a result for the recorded sample, topology and passive-wait policy. It does not establish a universal scaling bound or isolate the cause of the slowdown. The configuration order was fixed rather than randomized; frequency and thermal drift were not controlled. Peak memory and energy were not measured.

## Reproduce and inspect

Build according to the root README, then run `BUILD_DIR=build PYTHON=python3 bash bench/run.sh`. Local output defaults to the ignored `bench/results/local/` directory. To preserve a separate snapshot, supply an output directory as the first argument. The collector requires Linux affinity support and eight distinct cores visible through guest topology.

Install `bench/requirements.txt` into a virtual environment and run `.venv/bin/python bench/plot.py` to regenerate both committed SVG theme variants from the recorded summary. Use `--input bench/results/local/summary.csv` to plot a new run. The figure reports solve-time medians and IQR bars; the speedup panel does not imply confidence intervals.

The separate [contradiction example](../bench/results/2026-09-12/contradiction.json) records a 3 × 3 checkerboard request that reports failure after one attempt but exits with code 0. This demonstrates why callers must inspect solver status.

The existing CPU build and thirteen CTest suites passed before collection, and their [log](../bench/results/2026-09-12/build-tests.log) is retained without rerunning them. The optional dungeon target emits one source-comment warning. The original application sources and build configuration were not changed.

## Unmeasured and historical material

Kokkos was disabled and no Kokkos package was configured in the validated build; no CPU Kokkos or GPU result is reported. The Unreal Engine editor, sanitizer configurations, LaTeX compilation and historical figure pipelines were not exercised. Hosted CI is configured but has not run on this unpublished branch.

Earlier CPU/GPU tables, gallery images and report illustrations remain as historical material. The [old gallery](gallery.md) and French report sources do not constitute evidence of this run. Exact duplicates were consolidated with the [artifact path map](artifact-map.json); image references in the report now use the retained copies.
