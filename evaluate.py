#!/usr/bin/env python3
"""Quantitative evaluation against the synthetic ground truth.

For every sample the script compares the four detected corners with the true
corners used to render the photograph and reports the mean corner error in
pixels, normalised by the image diagonal. A detection is counted as correct
when the normalised error is below 2%.
"""

import json
import os
import sys
import time

import cv2
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scansmart.config import ScanConfig            # noqa: E402
from scansmart.detector import detect_document, order_corners  # noqa: E402
from scansmart.io_utils import load_image, resize_to_height    # noqa: E402
from scansmart.logger import setup_logging          # noqa: E402

TOLERANCE = 0.02          # 2% of the image diagonal


def corner_error(predicted: np.ndarray, truth: np.ndarray, diagonal: float) -> float:
    """Mean Euclidean distance between matched corners, normalised."""
    p, t = order_corners(predicted), order_corners(truth)
    return float(np.mean(np.linalg.norm(p - t, axis=1)) / diagonal)


def main(folder: str = "data/samples") -> int:
    setup_logging(verbose=False)
    truth_path = os.path.join(folder, "ground_truth.json")
    if not os.path.isfile(truth_path):
        print("ground_truth.json missing - run tools/generate_samples.py first")
        return 1

    with open(truth_path) as handle:
        ground_truth = json.load(handle)

    config = ScanConfig()
    rows, errors, times, correct = [], [], [], 0

    for name, corners in sorted(ground_truth.items()):
        path = os.path.join(folder, name)
        image = load_image(path)
        diagonal = float(np.hypot(*image.shape[:2]))

        start = time.perf_counter()
        working, scale = resize_to_height(image, config.working_height)
        detection = detect_document(working, config, scale=scale)
        elapsed = (time.perf_counter() - start) * 1000

        error = corner_error(detection.corners, np.array(corners, np.float32), diagonal)
        ok = error < TOLERANCE
        correct += int(ok)
        errors.append(error)
        times.append(elapsed)
        rows.append((name, detection.method, detection.confidence, error * 100,
                     elapsed, "PASS" if ok else "FAIL"))

    print(f"\n{'FILE':<18}{'METHOD':<16}{'CONF':>6}{'ERR %':>8}{'ms':>8}{'RESULT':>9}")
    print("-" * 65)
    for name, method, conf, err, ms, verdict in rows:
        print(f"{name:<18}{method:<16}{conf:>6.2f}{err:>8.2f}{ms:>8.0f}{verdict:>9}")
    print("-" * 65)
    print(f"Accuracy         : {correct}/{len(rows)} "
          f"({100.0 * correct / len(rows):.1f}%)")
    print(f"Mean corner error: {100 * float(np.mean(errors)):.2f}% of diagonal")
    print(f"Mean detect time : {float(np.mean(times)):.0f} ms\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1] if len(sys.argv) > 1 else "data/samples"))
