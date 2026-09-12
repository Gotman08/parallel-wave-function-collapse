"""Render the recorded summary as matching light/dark SVG figures."""
import argparse
import csv
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=ROOT / "bench/results/2026-09-12/summary.csv")
    parser.add_argument("--output", type=Path, default=ROOT / "docs/assets")
    parser.add_argument("--preview", type=Path, help="Optional PNG preview directory")
    args = parser.parse_args()
    with args.input.open(newline="") as stream:
        rows = list(csv.DictReader(stream))
    args.output.mkdir(parents=True, exist_ok=True)
    plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 11,
                         "svg.fonttype": "none", "svg.hashsalt": "projet801-benchmark"})
    for theme, bg, fg, muted, colors in [
        ("light", "#ffffff", "#17212b", "#627180", ["#1b5678", "#a64925"]),
        ("dark", "#101820", "#e6edf3", "#a4b3c0", ["#74bedf", "#f7b08b"]),
    ]:
        fig, axes = plt.subplots(1, 2, figsize=(11, 4.4), layout="constrained", facecolor=bg)
        labels = ["Serial", "OMP 1", "OMP 2", "OMP 4", "OMP 8"]
        for ax in axes:
            ax.set_facecolor(bg)
            ax.tick_params(colors=fg, which="both")
            ax.xaxis.label.set_color(fg)
            ax.yaxis.label.set_color(fg)
            for spine in ax.spines.values():
                spine.set_color(muted)
            ax.spines["top"].set_visible(False)
            ax.spines["right"].set_visible(False)
            ax.grid(axis="y", color=muted, alpha=0.18)
        for size, color, marker in zip([64, 128], colors, ["o", "s"]):
            group = [row for row in rows if int(row["size"]) == size]
            medians = [float(row["median_s"]) * 1000 for row in group]
            lower = [median - float(row["q1_s"]) * 1000 for row, median in zip(group, medians)]
            upper = [float(row["q3_s"]) * 1000 - median for row, median in zip(group, medians)]
            axes[0].errorbar(range(5), medians, yerr=[lower, upper], color=color,
                             marker=marker, capsize=4, linewidth=1.8, label=f"{size} × {size}")
            axes[1].plot(range(5), [float(row["speedup_vs_serial"]) for row in group],
                         color=color, marker=marker, linewidth=1.8, label=f"{size} × {size}")
        for ax in axes:
            ax.set_xticks(range(5), labels)
            ax.set_xlabel("Backend and requested threads")
        axes[0].set_yscale("log")
        axes[0].set_ylabel("Median solve time (ms), bars = IQR")
        axes[1].set_ylabel("Serial median / backend median")
        axes[1].axhline(1, color=muted, linestyle="--", linewidth=1)
        axes[1].set_yscale("log")
        axes[0].legend(frameon=False, labelcolor=fg)
        fig.savefig(args.output / f"benchmark-{theme}.svg", metadata={"Date": None}, facecolor=bg)
        if args.preview:
            args.preview.mkdir(parents=True, exist_ok=True)
            fig.savefig(args.preview / f"benchmark-{theme}.png", dpi=150, facecolor=bg)
        plt.close(fig)


if __name__ == "__main__":
    main()
