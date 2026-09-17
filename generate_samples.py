#!/usr/bin/env python3
"""Generate synthetic test photographs of documents.

Creates a flat page (text, heading, table), warps it with a random
perspective, drops it onto a textured desk background and adds a lighting
gradient plus sensor noise - i.e. a realistic phone photo. Because the true
corner positions are known, these samples double as ground truth for the
detection accuracy experiment described in the report.
"""

import argparse
import json
import os
import sys

import cv2
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

PAGE_W, PAGE_H = 850, 1100
RNG = np.random.default_rng(7)

LINES = [
    "INVOICE / DELIVERY NOTE",
    "",
    "Order ID    : SCN-2024-0{n}",
    "Customer    : Department of Computing",
    "Issued on   : 18 March 2024",
    "",
    "Item                 Qty      Rate     Amount",
    "-------------------------------------------",
    "Optical sensor        02    1250.00    2500.00",
    "Mounting bracket      04     180.50     722.00",
    "Calibration target    01     940.00     940.00",
    "-------------------------------------------",
    "Subtotal                            4162.00",
    "Tax (18%)                            749.16",
    "TOTAL                               4911.16",
    "",
    "Scanned using the ScanSmart computer vision",
    "pipeline: edge detection, contour approximation,",
    "homography estimation and adaptive thresholding.",
]


def render_page(index: int) -> np.ndarray:
    """Draw a synthetic printed page on white paper."""
    page = np.full((PAGE_H, PAGE_W, 3), 252, np.uint8)
    cv2.rectangle(page, (40, 40), (PAGE_W - 40, PAGE_H - 40), (215, 215, 215), 2)
    y = 130
    for i, line in enumerate(LINES):
        text = line.replace("{n}", str(index))
        scale, thickness = (1.05, 3) if i == 0 else (0.62, 2)
        cv2.putText(page, text, (80, y), cv2.FONT_HERSHEY_SIMPLEX,
                    scale, (25, 25, 25), thickness, cv2.LINE_AA)
        y += 58 if i == 0 else 42
    cv2.putText(page, f"Page {index}", (PAGE_W - 200, PAGE_H - 70),
                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (120, 120, 120), 1, cv2.LINE_AA)
    return page


def make_background(height: int, width: int) -> np.ndarray:
    """Textured wooden-desk style background."""
    base = RNG.integers(70, 105, size=(height, width, 3), dtype=np.uint8)
    base = cv2.GaussianBlur(base, (0, 0), 9)
    base[:, :, 0] = np.clip(base[:, :, 0] * 0.75, 0, 255)      # warmer tone
    base[:, :, 2] = np.clip(base[:, :, 2] * 1.15, 0, 255)
    for _ in range(18):                                        # grain streaks
        y = int(RNG.integers(0, height))
        cv2.line(base, (0, y), (width, y + int(RNG.integers(-25, 25))),
                 tuple(int(v) for v in RNG.integers(55, 95, 3)), int(RNG.integers(1, 4)))
    return cv2.GaussianBlur(base, (5, 5), 0)


def apply_lighting(image: np.ndarray, strength: float = 0.35) -> np.ndarray:
    """Multiply by a smooth gradient to emulate a directional light source."""
    h, w = image.shape[:2]
    cx, cy = RNG.uniform(0.2, 0.8), RNG.uniform(0.2, 0.8)
    xs = np.linspace(0, 1, w)[None, :]
    ys = np.linspace(0, 1, h)[:, None]
    distance = np.sqrt((xs - cx) ** 2 + (ys - cy) ** 2)
    mask = 1.0 - strength * (distance / distance.max())
    return np.clip(image * mask[:, :, None], 0, 255).astype(np.uint8)


def photograph(page: np.ndarray, out_size=(1000, 1400), jitter: float = 0.12):
    """Composite the page onto a background with a random perspective."""
    out_w, out_h = out_size
    background = make_background(out_h, out_w)

    margin_x, margin_y = out_w * 0.14, out_h * 0.10
    base = np.float32([
        [margin_x, margin_y],
        [out_w - margin_x, margin_y],
        [out_w - margin_x, out_h - margin_y],
        [margin_x, out_h - margin_y],
    ])
    offsets = RNG.uniform(-jitter, jitter, size=(4, 2)) * np.float32([out_w, out_h])
    corners = (base + offsets).astype(np.float32)

    src = np.float32([[0, 0], [PAGE_W, 0], [PAGE_W, PAGE_H], [0, PAGE_H]])
    matrix = cv2.getPerspectiveTransform(src, corners)
    warped = cv2.warpPerspective(page, matrix, (out_w, out_h))

    mask = cv2.warpPerspective(
        np.full((PAGE_H, PAGE_W), 255, np.uint8), matrix, (out_w, out_h)
    )
    mask3 = cv2.cvtColor(cv2.GaussianBlur(mask, (3, 3), 0), cv2.COLOR_GRAY2BGR) / 255.0
    composite = (warped * mask3 + background * (1 - mask3)).astype(np.uint8)

    composite = apply_lighting(composite)
    noise = RNG.normal(0, 4.0, composite.shape)
    composite = np.clip(composite + noise, 0, 255).astype(np.uint8)
    return cv2.GaussianBlur(composite, (3, 3), 0), corners


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate synthetic samples")
    parser.add_argument("-n", "--count", type=int, default=6)
    parser.add_argument("-o", "--output", default="data/samples")
    args = parser.parse_args()

    os.makedirs(args.output, exist_ok=True)
    truth = {}
    for i in range(1, args.count + 1):
        image, corners = photograph(render_page(i), jitter=0.05 + 0.03 * (i % 3))
        name = f"sample_{i:02d}.jpg"
        cv2.imwrite(os.path.join(args.output, name), image,
                    [int(cv2.IMWRITE_JPEG_QUALITY), 92])
        truth[name] = corners.tolist()
        print(f"wrote {name}")

    with open(os.path.join(args.output, "ground_truth.json"), "w") as handle:
        json.dump(truth, handle, indent=2)
    print(f"ground truth for {len(truth)} images saved")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
