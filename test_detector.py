"""Unit tests for document detection."""

import numpy as np
import pytest

from scansmart.detector import Detection, detect_document, draw_detection, order_corners
from scansmart.exceptions import DocumentNotFoundError


def test_order_corners_sorts_clockwise_from_top_left():
    shuffled = np.float32([[300, 400], [10, 20], [300, 20], [10, 400]])
    tl, tr, br, bl = order_corners(shuffled)
    assert list(tl) == [10, 20]
    assert list(tr) == [300, 20]
    assert list(br) == [300, 400]
    assert list(bl) == [10, 400]


def test_order_corners_is_idempotent():
    pts = np.float32([[0, 0], [100, 5], [95, 200], [3, 190]])
    assert np.allclose(order_corners(order_corners(pts)), order_corners(pts))


def test_detects_page_close_to_ground_truth(synthetic_photo, config):
    image, truth = synthetic_photo
    detection = detect_document(image, config)
    assert isinstance(detection, Detection)
    error = np.mean(np.linalg.norm(detection.corners - order_corners(truth), axis=1))
    assert error < 15                       # pixels
    assert detection.confidence > 0.4


def test_scale_maps_back_to_original_resolution(synthetic_photo, config):
    image, _ = synthetic_photo
    small = detect_document(image, config, scale=1.0)
    scaled = detect_document(image, config, scale=2.0)
    assert np.allclose(scaled.corners, small.corners * 2.0, atol=1e-3)


def test_blank_image_falls_back_to_full_frame(config):
    blank = np.full((300, 300, 3), 127, np.uint8)
    detection = detect_document(blank, config)
    assert detection.method == "full_frame"
    assert detection.confidence == 0.0


def test_blank_image_raises_when_fallback_disabled(config):
    blank = np.full((300, 300, 3), 127, np.uint8)
    with pytest.raises(DocumentNotFoundError):
        detect_document(blank, config, allow_fallback=False)


def test_draw_detection_returns_colour_overlay(synthetic_photo, config):
    image, _ = synthetic_photo
    detection = detect_document(image, config)
    overlay = draw_detection(image, detection)
    assert overlay.shape == image.shape
    assert not np.array_equal(overlay, image)
