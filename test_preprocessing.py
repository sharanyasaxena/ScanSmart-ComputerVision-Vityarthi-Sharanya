"""Unit tests for the pre-processing module."""

import numpy as np

from scansmart.preprocessing import (
    auto_canny, build_edge_map, close_gaps, denoise, equalize, to_grayscale,
)


def test_grayscale_reduces_channels(synthetic_photo):
    image, _ = synthetic_photo
    gray = to_grayscale(image)
    assert gray.ndim == 2 and gray.shape == image.shape[:2]


def test_grayscale_is_idempotent(flat_page):
    assert to_grayscale(flat_page).shape == flat_page.shape


def test_equalize_preserves_shape_and_dtype(flat_page, config):
    out = equalize(flat_page, config)
    assert out.shape == flat_page.shape and out.dtype == np.uint8


def test_denoise_reduces_noise(config):
    rng = np.random.default_rng(0)
    clean = np.full((200, 200), 128, np.uint8)
    noisy = np.clip(clean + rng.normal(0, 25, clean.shape), 0, 255).astype(np.uint8)
    assert denoise(noisy, config).std() < noisy.std()


def test_auto_canny_returns_binary_edges(synthetic_photo, config):
    image, _ = synthetic_photo
    edges = auto_canny(to_grayscale(image), config)
    assert set(np.unique(edges)).issubset({0, 255})
    assert np.count_nonzero(edges) > 0


def test_closing_does_not_remove_edges(synthetic_photo, config):
    image, _ = synthetic_photo
    edges = auto_canny(to_grayscale(image), config)
    assert np.count_nonzero(close_gaps(edges, config)) >= np.count_nonzero(edges)


def test_build_edge_map_returns_all_stages(synthetic_photo, config):
    image, _ = synthetic_photo
    stages = build_edge_map(image, config)
    assert {"gray", "equalized", "smoothed", "edges", "closed"} <= set(stages)
