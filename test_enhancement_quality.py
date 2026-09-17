"""Unit tests for enhancement and quality analytics."""

import cv2
import numpy as np
import pytest

from scansmart.config import ScanConfig
from scansmart.enhancement import enhance, remove_shadows, to_color, to_gray, to_scan
from scansmart.exceptions import InvalidConfigError
from scansmart.quality import analyse, contrast_score, ink_ratio, sharpness_score


def test_scan_mode_is_binary(flat_page, config):
    out = to_scan(flat_page, config)
    assert set(np.unique(out)).issubset({0, 255})


def test_gray_mode_is_single_channel(flat_page, config):
    assert to_gray(flat_page, config).ndim == 2


def test_color_mode_keeps_three_channels(synthetic_photo, config):
    image, _ = synthetic_photo
    assert to_color(image, config).shape == image.shape


def test_remove_shadows_flattens_gradient():
    gradient = np.tile(np.linspace(60, 250, 300, dtype=np.uint8), (300, 1))
    assert remove_shadows(gradient).std() < gradient.std()


def test_enhance_dispatches_on_mode(flat_page):
    assert enhance(flat_page, ScanConfig(mode="gray")).ndim == 2
    assert enhance(flat_page, ScanConfig(mode="color")).ndim == 3


def test_enhance_rejects_unknown_mode(flat_page):
    config = ScanConfig()
    object.__setattr__(config, "mode", "bogus")     # bypass validation on purpose
    with pytest.raises(InvalidConfigError):
        enhance(flat_page, config)


def test_sharpness_drops_after_blurring(flat_page):
    blurred = cv2.GaussianBlur(flat_page, (15, 15), 0)
    assert sharpness_score(blurred) < sharpness_score(flat_page)


def test_contrast_of_flat_image_is_zero():
    assert contrast_score(np.full((50, 50), 128, np.uint8)) == pytest.approx(0.0)


def test_ink_ratio_in_unit_interval(flat_page):
    assert 0.0 <= ink_ratio(flat_page) <= 1.0


def test_analyse_grades_a_clean_page(flat_page, config):
    metrics = analyse(flat_page, confidence=0.9, config=config)
    assert metrics.grade in {"GOOD", "FAIR"}
    assert metrics.to_dict()["sharpness"] == metrics.sharpness


def test_low_confidence_is_graded_poor(flat_page, config):
    assert analyse(flat_page, confidence=0.0, config=config).grade == "POOR"
