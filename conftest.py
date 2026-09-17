"""Shared pytest fixtures."""

import os
import sys

import cv2
import numpy as np
import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scansmart.config import ScanConfig            # noqa: E402


@pytest.fixture
def config() -> ScanConfig:
    """Default configuration used by most tests."""
    return ScanConfig()


@pytest.fixture
def synthetic_photo():
    """A dark background with a bright, perspective-distorted white page.

    Returns (image, true_corners) so detection accuracy can be asserted.
    """
    image = np.full((600, 450, 3), 40, np.uint8)
    corners = np.float32([[60, 40], [390, 75], [370, 540], [45, 500]])
    cv2.fillConvexPoly(image, corners.astype(np.int32), (245, 245, 245))
    cv2.putText(image, "TEST", (120, 300), cv2.FONT_HERSHEY_SIMPLEX,
                1.4, (20, 20, 20), 3)
    return image, corners


@pytest.fixture
def flat_page():
    """An axis-aligned page with printed text (no perspective)."""
    page = np.full((400, 300), 235, np.uint8)
    for y in range(60, 340, 40):
        cv2.line(page, (40, y), (260, y), 30, 4)
    return page
