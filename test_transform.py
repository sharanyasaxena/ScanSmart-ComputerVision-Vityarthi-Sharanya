"""Unit tests for geometric correction."""

import cv2
import numpy as np

from scansmart.transform import (
    deskew, estimate_output_size, estimate_skew, four_point_transform,
)


def test_output_size_matches_longest_edges(config):
    corners = np.float32([[0, 0], [200, 0], [200, 400], [0, 400]])
    assert estimate_output_size(corners, config) == (200, 400)


def test_output_size_is_clamped(config):
    corners = np.float32([[0, 0], [9000, 0], [9000, 12000], [0, 12000]])
    width, height = estimate_output_size(corners, config)
    assert max(width, height) <= config.max_output_side


def test_warp_produces_axis_aligned_rectangle(synthetic_photo, config):
    image, corners = synthetic_photo
    warped = four_point_transform(image, corners, config)
    assert warped.shape[0] > warped.shape[1]        # portrait page preserved
    # The page is bright, the background dark: warping must keep only the page.
    assert warped.mean() > 180


def test_warp_of_full_frame_is_identity(config):
    """Warping an already-flat rectangle must return the same image back."""
    noise = np.random.default_rng(1).integers(0, 255, (300, 200, 3), dtype=np.uint8)
    source = cv2.GaussianBlur(noise, (9, 9), 0)     # smooth: interpolation-safe
    corners = np.float32([[0, 0], [200, 0], [200, 300], [0, 300]])
    warped = four_point_transform(source, corners, config)
    assert warped.shape == source.shape
    # Interior pixels must be preserved (edges may differ by interpolation).
    diff = np.abs(warped[5:-5, 5:-5].astype(int) - source[5:-5, 5:-5].astype(int))
    assert diff.mean() < 12


def test_estimate_skew_detects_rotation():
    page = np.full((400, 400), 255, np.uint8)
    for y in range(60, 340, 40):
        cv2.line(page, (40, y), (360, y), 0, 3)
    rotated = deskew(page, -5.0)                   # rotate by +5 degrees
    assert abs(estimate_skew(rotated)) > 2.0


def test_deskew_ignores_tiny_angles(flat_page):
    assert np.array_equal(deskew(flat_page, 0.02), flat_page)
