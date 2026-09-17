"""Unit tests for configuration validation."""

import pytest

from scansmart.config import ScanConfig
from scansmart.exceptions import InvalidConfigError


def test_defaults_are_valid():
    assert ScanConfig().mode == "scan"


def test_rejects_unknown_mode():
    with pytest.raises(InvalidConfigError):
        ScanConfig(mode="sepia")


def test_rejects_even_blur_kernel():
    with pytest.raises(InvalidConfigError):
        ScanConfig(blur_kernel=4)


def test_rejects_even_adaptive_block():
    with pytest.raises(InvalidConfigError):
        ScanConfig(adaptive_block=30)


def test_rejects_bad_area_ratios():
    with pytest.raises(InvalidConfigError):
        ScanConfig(min_area_ratio=0.9, max_area_ratio=0.5)


def test_to_dict_round_trip():
    data = ScanConfig(mode="gray").to_dict()
    assert data["mode"] == "gray"
    assert "working_height" in data
