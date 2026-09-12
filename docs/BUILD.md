# Build

The recorded CPU build uses Ubuntu 24.04 under WSL2, GCC 13.3 and CMake in Release mode. The existing CMake configuration enables `-O3 -march=native` for GCC/Clang Release builds. Such binaries are intended for the CPU on which they are compiled.

```bash
sudo apt-get install build-essential cmake
cmake -S . -B build -DCMAKE_BUILD_TYPE=Release \
  -DUSE_OMP=ON -DUSE_KOKKOS=OFF -DBUILD_DUNGEON=ON
cmake --build build --parallel 2
ctest --test-dir build --output-on-failure
```

The recorded build completed and thirteen CTest suites passed. It emitted a `-Wcomment` warning in the optional dungeon application because a source comment contains a nested comment marker. That warning was not suppressed or fixed during this documentation and measurement overhaul. [Original build/test log](../bench/results/2026-09-12/build-tests.log).

Kokkos requires a separately supplied CMake package and `-DUSE_KOKKOS=ON`. It was disabled in the validated build; no CPU Kokkos or GPU performance is claimed. The existing `scripts/build_kokkos.sh` helper and cluster scripts were not revalidated. The Unreal Engine editor is external to this CMake build.
