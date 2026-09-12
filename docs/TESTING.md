# Tests and evidence

The recorded Release build with OpenMP and the dungeon CLI enabled passed thirteen CTest suites. [Build and CTest output](../bench/results/2026-09-12/build-tests.log).

The generated [coverage report](coverage/README.md) is historical and was not regenerated. No current line or branch coverage percentage is claimed.

The twelve core suites exercise bitsets, grids, grid I/O, tile extraction, overlap rules, wave storage, shared solver operations, serial solving, edge cases, parallel attempts, symmetry expansion and backtracking. The additional OpenMP suite checks successful equality with the serial solver, reseeding, multivalue cases and contradiction handling.

Run them with `ctest --test-dir build --output-on-failure`. Kokkos-specific tests are conditional on a Kokkos build and were not run. Sanitizers and the Unreal Engine editor were not exercised in this overhaul. The configured hosted CI uses the CPU build and CTest command, but its hosted result remains pending publication.

The benchmark is separate from CTest. [bench/run.sh](../bench/run.sh) preserves solver CSVs, checks every measured solve's success flag, excludes one warm-up and summarizes five fixed seeds per configuration. Its additional contradiction example records both the textual failure status and process exit code. [Protocol](results.md).
