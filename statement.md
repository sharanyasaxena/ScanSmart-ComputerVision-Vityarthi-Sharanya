# Problem Statement

## 1. Problem

Most documents today are captured with a phone camera rather than a flatbed
scanner. A hand-held photograph of a page is convenient but poor as a record:
the page appears as a **trapezoid instead of a rectangle** because the camera
is not parallel to the paper, the background (desk, floor, hands) is included
in the frame, the lighting is uneven so one half of the page is in shadow, and
the text has low contrast against grey paper.

Such images are large, hard to read, hard to archive, and unusable as input to
downstream tools such as OCR. Manually cropping and correcting each photo in an
image editor is slow and inconsistent, and commercial scanner apps are
closed-source, often cloud-based, and cannot be inspected or tuned by a student.

**ScanSmart** solves this with a classical computer-vision pipeline that
automatically locates the page inside the photograph, removes the perspective
distortion, flattens the illumination and produces a clean, binarised,
scanner-quality page - locally, offline, and in about a tenth of a second.

## 2. Scope of the Project

### In scope
- Detection of a single, roughly rectangular document in a photograph.
- Automatic corner ordering and perspective (homography) correction.
- Residual skew correction using the Hough line transform.
- Three output styles: black-and-white *scan*, enhanced *gray*, and *color*.
- Objective quality measurement (sharpness, contrast, skew, grade) per page.
- Batch processing of a folder, multi-page PDF export, and JSON/CSV reports.
- A command-line interface, unit/integration tests and an accuracy evaluation
  against synthetic ground truth.

### Out of scope
- Optical Character Recognition (text is not converted to characters).
- Detection of several documents in one frame, or of curved/folded pages.
- Deep-learning based segmentation; the project deliberately uses classical
  CV so that every step is explainable.
- Real-time video capture and a graphical user interface.

## 3. Target Users

| User | Need served |
|------|-------------|
| Students & office staff | Convert phone photos of notes, forms and receipts into tidy PDFs |
| Small offices / clerks | Digitise invoices and delivery notes in bulk without a scanner |
| OCR / RPA developers | Use ScanSmart as a pre-processing stage that feeds clean, deskewed pages to an OCR engine |
| CV learners | A readable reference implementation of edge detection, contour approximation and homography |

## 4. High-Level Features

1. **Automatic page detection** - auto-thresholded Canny edges, morphological
   closing, contour approximation, with a `minAreaRect` fallback and a
   full-frame last resort so the tool never crashes on a difficult photo.
2. **Perspective correction** - four-point homography warp that turns the
   distorted quadrilateral into a flat, correctly proportioned page, followed
   by Hough-based deskew.
3. **Image enhancement** - morphological shadow removal, adaptive
   thresholding, CLAHE and unsharp masking in three selectable modes.
4. **Quality analytics** - per-page sharpness, contrast, brightness, ink ratio,
   residual skew and a GOOD/FAIR/POOR grade; aggregated into a batch summary.
5. **Batch processing & export** - whole folders in one command, a multi-page
   PDF, and machine-readable JSON/CSV reports.
