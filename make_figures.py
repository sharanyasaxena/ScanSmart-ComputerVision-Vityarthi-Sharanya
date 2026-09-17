#!/usr/bin/env python3
"""Build the result figures used in the report (pipeline montage + charts)."""

import json
import os
import sys

import cv2
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from scansmart.config import ScanConfig                     # noqa: E402
from scansmart.detector import detect_document, draw_detection  # noqa: E402
from scansmart.enhancement import enhance                   # noqa: E402
from scansmart.io_utils import load_image, resize_to_height  # noqa: E402
from scansmart.logger import setup_logging                  # noqa: E402
from scansmart.preprocessing import build_edge_map          # noqa: E402
from scansmart.transform import four_point_transform        # noqa: E402

OUT = os.path.join(ROOT, "docs", "images")
PANEL_H = 520


def panel(image: np.ndarray, caption: str) -> np.ndarray:
    """Resize an image to a fixed height and add a caption strip below it."""
    if image.ndim == 2:
        image = cv2.cvtColor(image, cv2.COLOR_GRAY2BGR)
    scale = PANEL_H / image.shape[0]
    resized = cv2.resize(image, (int(image.shape[1] * scale), PANEL_H))
    strip = np.full((46, resized.shape[1], 3), 255, np.uint8)
    cv2.putText(strip, caption, (8, 31), cv2.FONT_HERSHEY_SIMPLEX, 0.62,
                (25, 35, 50), 2, cv2.LINE_AA)
    tile = np.vstack([resized, strip])
    return cv2.copyMakeBorder(tile, 6, 6, 6, 6, cv2.BORDER_CONSTANT, value=(210, 214, 220))


def pipeline_montage(sample: str = "data/samples/sample_03.jpg") -> None:
    """Five-stage visual walk-through of the algorithm."""
    config = ScanConfig()
    original = load_image(os.path.join(ROOT, sample))
    working, scale = resize_to_height(original, config.working_height)
    stages = build_edge_map(working, config)
    detection = detect_document(working, config, scale=scale)
    overlay = draw_detection(original, detection)
    warped = four_point_transform(original, detection.corners, config)
    final = enhance(warped, config)

    panels = [
        panel(original, "1. Input photograph"),
        panel(stages["closed"], "2. Canny + morphology"),
        panel(overlay, "3. Detected corners"),
        panel(warped, "4. Perspective corrected"),
        panel(final, "5. Enhanced output"),
    ]
    montage = np.hstack(panels)
    cv2.imwrite(os.path.join(OUT, "pipeline_stages.png"), montage)
    print("wrote pipeline_stages.png", montage.shape)

    before_after = np.hstack([panel(original, "Before"), panel(final, "After")])
    cv2.imwrite(os.path.join(OUT, "before_after.png"), before_after)
    print("wrote before_after.png")


def modes_figure(sample: str = "data/samples/sample_05.jpg") -> None:
    """Show the three enhancement modes side by side."""
    original = load_image(os.path.join(ROOT, sample))
    panels = []
    for mode in ("color", "gray", "scan"):
        config = ScanConfig(mode=mode)
        working, scale = resize_to_height(original, config.working_height)
        detection = detect_document(working, config, scale=scale)
        warped = four_point_transform(original, detection.corners, config)
        panels.append(panel(enhance(warped, config), f"mode = {mode}"))
    cv2.imwrite(os.path.join(OUT, "modes.png"), np.hstack(panels))
    print("wrote modes.png")


def results_chart(report: str = "outputs/report.json") -> None:
    """Bar charts of per-image confidence and processing time."""
    with open(os.path.join(ROOT, report)) as handle:
        data = json.load(handle)
    pages = data["pages"]
    names = [p["source"].replace("sample_", "S").replace(".jpg", "") for p in pages]
    confidence = [p.get("confidence", 0) for p in pages]
    times = [p.get("elapsed_ms", 0) for p in pages]

    fig, axes = plt.subplots(1, 2, figsize=(9.6, 3.3), dpi=185)
    colors = ["#4c78a8" if c >= 0.55 else "#e0a03c" for c in confidence]
    axes[0].bar(names, confidence, color=colors, edgecolor="#1b2733", linewidth=0.7)
    axes[0].axhline(0.55, color="#c0392b", ls="--", lw=1, label="GOOD threshold")
    axes[0].set_ylim(0, 1.0)
    axes[0].set_title("Detection confidence per image", fontsize=10)
    axes[0].set_ylabel("confidence")
    axes[0].legend(fontsize=7)

    axes[1].bar(names, times, color="#6aa84f", edgecolor="#1b2733", linewidth=0.7)
    axes[1].set_title("End-to-end processing time", fontsize=10)
    axes[1].set_ylabel("milliseconds")
    for ax in axes:
        ax.tick_params(labelsize=8)
        ax.spines[["top", "right"]].set_visible(False)
        ax.grid(axis="y", alpha=0.25)
    fig.tight_layout()
    fig.savefig(os.path.join(OUT, "results_chart.png"), bbox_inches="tight",
                facecolor="white")
    plt.close(fig)
    print("wrote results_chart.png")


if __name__ == "__main__":
    setup_logging(verbose=False)
    pipeline_montage()
    modes_figure()
    results_chart()
