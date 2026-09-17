"""Integration tests: I/O, end-to-end pipeline and reporting."""

import json
import os

import cv2
import numpy as np
import pytest

from scansmart.config import ScanConfig
from scansmart.exceptions import ImageLoadError
from scansmart.exporter import summarise, write_csv_report, write_json_report
from scansmart.io_utils import discover_images, load_image, resize_to_height, save_image
from scansmart.pipeline import process_batch, process_image


@pytest.fixture
def sample_dir(tmp_path, synthetic_photo):
    """A temporary folder containing three photographs."""
    image, _ = synthetic_photo
    for i in range(3):
        cv2.imwrite(str(tmp_path / f"page_{i}.jpg"), image)
    (tmp_path / "notes.txt").write_text("ignore me")
    return str(tmp_path)


def test_load_missing_file_raises():
    with pytest.raises(ImageLoadError):
        load_image("/no/such/file.png")


def test_load_corrupt_file_raises(tmp_path):
    bad = tmp_path / "broken.png"
    bad.write_bytes(b"not an image")
    with pytest.raises(ImageLoadError):
        load_image(str(bad))


def test_discover_skips_non_images(sample_dir, config):
    files = discover_images(sample_dir, config)
    assert len(files) == 3
    assert all(f.endswith(".jpg") for f in files)


def test_discover_empty_folder_raises(tmp_path, config):
    with pytest.raises(ImageLoadError):
        discover_images(str(tmp_path), config)


def test_resize_preserves_aspect_ratio(synthetic_photo):
    image, _ = synthetic_photo
    resized, scale = resize_to_height(image, 300)
    assert resized.shape[0] == 300
    assert scale == pytest.approx(image.shape[0] / 300)


def test_resize_skips_small_images(flat_page):
    resized, scale = resize_to_height(flat_page, 10_000)
    assert scale == 1.0 and resized.shape == flat_page.shape


def test_save_image_creates_directories(tmp_path, flat_page):
    target = tmp_path / "nested" / "deep" / "out.png"
    save_image(flat_page, str(target))
    assert target.is_file()


def test_process_image_end_to_end(tmp_path, synthetic_photo):
    image, _ = synthetic_photo
    path = str(tmp_path / "doc.jpg")
    cv2.imwrite(path, image)
    result = process_image(path, ScanConfig())
    assert result.status == "ok"
    assert result.image is not None and result.image.size > 0
    assert result.metrics is not None and result.detection is not None
    assert result.elapsed_ms > 0


def test_process_image_records_failure_instead_of_raising(tmp_path):
    bad = tmp_path / "bad.jpg"
    bad.write_bytes(b"\x00\x01\x02")
    result = process_image(str(bad), ScanConfig())
    assert result.status == "failed" and result.error


def test_process_batch_writes_outputs(sample_dir, tmp_path):
    out = str(tmp_path / "out")
    results = process_batch(sample_dir, out, ScanConfig(), save_overlay=True)
    assert len(results) == 3
    assert all(r.status == "ok" for r in results)
    assert len(os.listdir(out)) == 6              # scanned + detected per page


def test_reports_are_written(sample_dir, tmp_path):
    out = str(tmp_path / "out")
    records = [r.to_record() for r in process_batch(sample_dir, out, ScanConfig())]
    json_path = write_json_report(records, ScanConfig().to_dict(),
                                  os.path.join(out, "report.json"))
    csv_path = write_csv_report(records, os.path.join(out, "report.csv"))

    payload = json.loads(open(json_path).read())
    assert payload["summary"]["processed"] == 3
    assert len(payload["pages"]) == 3
    assert open(csv_path).readline().startswith("source,output,status")


def test_summarise_counts_failures():
    records = [
        {"status": "ok", "grade": "GOOD", "confidence": 0.8, "elapsed_ms": 100},
        {"status": "failed", "error": "boom", "elapsed_ms": 10},
    ]
    stats = summarise(records)
    assert stats["processed"] == 1 and stats["failed"] == 1
    assert stats["success_rate"] == 0.5
