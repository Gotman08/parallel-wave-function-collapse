"""Measure the existing WFC benchmark executable; do not rebuild or modify it."""
from __future__ import annotations

import argparse
import csv
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import platform
import re
import shlex
import statistics
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
SAMPLE = "samples/binary_5x5.txt"
CONFIGS = [(size, backend, threads) for size in (64, 128)
           for backend, threads in [("serial", 1), ("omp", 1), ("omp", 2),
                                    ("omp", 4), ("omp", 8)]]


def capture(command):
    result = subprocess.run(command, cwd=ROOT, capture_output=True, text=True, check=False)
    return {"argv": command, "exit_code": result.returncode,
            "stdout": result.stdout, "stderr": result.stderr}


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def selected_cpus():
    allowed = sorted(os.sched_getaffinity(0))
    chosen, cores = [], set()
    for cpu in allowed:
        topology = Path(f"/sys/devices/system/cpu/cpu{cpu}/topology")
        try:
            key = ((topology / "physical_package_id").read_text().strip(),
                   (topology / "core_id").read_text().strip())
        except OSError:
            key = ("unknown", str(cpu))
        if key not in cores:
            cores.add(key)
            chosen.append(cpu)
    if len(chosen) < 8:
        raise RuntimeError("The recorded protocol requires eight distinct visible cores")
    return allowed, chosen[:8]


def cache_settings(build):
    settings = {}
    for line in (ROOT / build / "CMakeCache.txt").read_text().splitlines():
        match = re.match(r"([^:#]+):[^=]+=(.*)", line)
        if match and (match[1].startswith("USE_") or match[1].startswith("BUILD_")
                      or match[1] in ("CMAKE_BUILD_TYPE", "CMAKE_CXX_COMPILER",
                                      "CMAKE_CXX_FLAGS", "CMAKE_CXX_FLAGS_RELEASE",
                                      "CMAKE_GENERATOR")):
            settings[match[1]] = match[2]
    return settings


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--build", default="build")
    parser.add_argument("--output", type=Path, default=Path("bench/results/local"))
    args = parser.parse_args()
    os.chdir(ROOT)
    benchmark = Path(args.build) / "wfc_benchmark"
    if not benchmark.is_file():
        raise RuntimeError("Build wfc_benchmark with USE_OMP=ON before measuring")
    settings = cache_settings(args.build)
    if settings.get("USE_OMP") != "ON" or settings.get("CMAKE_BUILD_TYPE") != "Release":
        raise RuntimeError("This protocol requires an OpenMP Release build")
    raw = args.output / "raw"
    raw.mkdir(parents=True, exist_ok=True)
    allowed, cpus = selected_cpus()
    revision = capture(["git", "rev-parse", "HEAD"])["stdout"].strip()
    environment = {
        "recorded_at_utc": datetime.now(timezone.utc).isoformat(),
        "source_revision": revision, "binary_sha256": digest(benchmark),
        "collector_sha256": digest(Path(__file__)),
        "sample": SAMPLE, "sample_sha256": digest(Path(SAMPLE)),
        "platform": platform.platform(), "python": sys.version,
        "os_release": Path("/etc/os-release").read_text(),
        "lscpu": capture(["lscpu", "-J"]),
        "memory": next(line for line in Path("/proc/meminfo").read_text().splitlines()
                       if line.startswith("MemTotal:")),
        "available_cpus": allowed, "selected_cpus": cpus,
        "affinity_policy": "first visible logical CPU per core; first n selected cores for n threads",
        "cmake_cache": settings,
        "compiler": capture([settings["CMAKE_CXX_COMPILER"], "--version"]),
        "cmake": capture(["cmake", "--version"]),
        "openmp_runtime": capture(["dpkg-query", "-W", "libgomp1"]),
        "kokkos_packages": capture(["dpkg-query", "-W", "-f=${binary:Package} ${db:Status-Status} ${Version}\n",
                                     "libtrilinos-kokkos*"]),
        "protocol": {"tile_size": 2, "attempts": 5, "sizes": [64, 128],
                     "warmup_seed": 41, "measured_seeds": [42, 43, 44, 45, 46],
                     "warmup_runs_per_config": 1, "measured_runs_per_config": 5,
                     "metric": "solve_s from the existing SolverStats timer",
                     "quartiles": "statistics.quantiles(method='inclusive')",
                     "config_order": CONFIGS, "process_timeout_s": 180,
                     "OMP_DYNAMIC": "FALSE", "OMP_PROC_BIND": "close",
                     "OMP_PLACES": "cores", "OMP_WAIT_POLICY": "PASSIVE"},
    }
    (args.output / "environment.json").write_text(json.dumps(environment, indent=2) + "\n")
    all_rows, invocations = [], []
    for size, backend, threads in CONFIGS:
        label = f"{backend}_{threads}_{size}"
        csv_path = raw / f"{label}.csv"
        affinity = ",".join(map(str, cpus[:threads]))
        command = ["taskset", "-c", affinity, str(benchmark), "--sample", SAMPLE,
                   "--sizes", str(size), "--threads", str(threads), "--repeats", "6",
                   "--seed", "41", "--N", "2", "--attempts", "5",
                   "--label", label, "--backends", backend, "-o", str(csv_path)]
        env = dict(os.environ, OMP_NUM_THREADS=str(threads), OMP_DYNAMIC="FALSE",
                   OMP_PROC_BIND="close", OMP_PLACES="cores", OMP_WAIT_POLICY="PASSIVE")
        print(shlex.join(command), flush=True)
        started = time.perf_counter()
        process = subprocess.run(command, env=env, cwd=ROOT, capture_output=True,
                                 text=True, timeout=180, check=False)
        wall = time.perf_counter() - started
        (raw / f"{label}.stdout.log").write_text(process.stdout)
        (raw / f"{label}.stderr.log").write_text(process.stderr)
        invocations.append({"argv": command, "exit_code": process.returncode,
                            "process_wall_s": wall, "affinity": cpus[:threads],
                            "OMP_NUM_THREADS": threads})
        (args.output / "commands.json").write_text(json.dumps(invocations, indent=2) + "\n")
        if process.returncode:
            raise RuntimeError(f"{label} exited with {process.returncode}; see raw logs")
        with csv_path.open(newline="") as stream:
            rows = list(csv.DictReader(stream))
        if len(rows) != 6 or [int(row["seed"]) for row in rows] != list(range(41, 47)):
            raise RuntimeError(f"Unexpected repetition/seed set for {label}")
        for row in rows:
            row["phase"] = "warmup" if row["repeat"] == "0" else "measured"
            all_rows.append(row)
        print(f"{label}: {sum(row['success'] == '1' for row in rows)}/6 successful solves", flush=True)
    with (args.output / "runs.csv").open("w", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=all_rows[0].keys())
        writer.writeheader()
        writer.writerows(all_rows)
    summaries = []
    for size, backend, threads in CONFIGS:
        rows = [row for row in all_rows if row["phase"] == "measured"
                and int(row["rows"]) == size and row["backend"] == backend
                and int(row["threads"]) == threads]
        if any(row["success"] != "1" for row in rows):
            raise RuntimeError("A measured solve failed; do not aggregate failed and successful runs")
        values = [float(row["solve_s"]) for row in rows]
        q1, _, q3 = statistics.quantiles(values, n=4, method="inclusive")
        summaries.append({"size": size, "backend": backend, "threads": threads,
                          "n": len(values), "median_s": statistics.median(values),
                          "q1_s": q1, "q3_s": q3, "iqr_s": q3 - q1})
    for row in summaries:
        baseline = next(base["median_s"] for base in summaries
                        if base["size"] == row["size"] and base["backend"] == "serial")
        row["speedup_vs_serial"] = baseline / row["median_s"]
    with (args.output / "summary.csv").open("w", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=summaries[0].keys())
        writer.writeheader()
        writer.writerows(summaries)
    failure_command = ["taskset", "-c", str(cpus[0]), str(Path(args.build) / "wfc_serial"),
                       "samples/binary_checker.txt", "--rows", "3", "--cols", "3", "-N", "2",
                       "--seed", "42", "--attempts", "1"]
    failure = capture(failure_command)
    (args.output / "contradiction.json").write_text(json.dumps(failure, indent=2) + "\n")
    print(json.dumps(summaries, indent=2), flush=True)
    print("Completed benchmark and captured the separate contradiction example", flush=True)


if __name__ == "__main__":
    main()
