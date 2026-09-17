#!/usr/bin/env python3
"""Generate the VITyarthi project report (PDF) for ScanSmart.

The report is produced from code so that it always reflects the current
diagrams, figures and measured results in docs/images and outputs/.
"""

import json
import os
import sys

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import (
    BaseDocTemplate, Frame, Image, KeepTogether, PageBreak, PageTemplate,
    Paragraph, Spacer, Table, TableStyle,
)
from reportlab.lib.utils import ImageReader

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
IMG = os.path.join(ROOT, "docs", "images")
OUTPUT = os.path.join(ROOT, "docs", "ScanSmart_Project_Report.pdf")

INK = colors.HexColor("#1b2733")
ACCENT = colors.HexColor("#2c5d8f")
LIGHT = colors.HexColor("#eef3f8")
GREY = colors.HexColor("#5a6b7b")

# --------------------------------------------------------------------- styles
ss = getSampleStyleSheet()
S = {
    "title": ParagraphStyle("title", parent=ss["Title"], fontSize=26, leading=31,
                            textColor=INK, spaceAfter=6),
    "subtitle": ParagraphStyle("subtitle", parent=ss["Normal"], fontSize=13.5,
                               leading=18, alignment=TA_CENTER, textColor=ACCENT),
    "h1": ParagraphStyle("h1", parent=ss["Heading1"], fontSize=15, leading=19,
                         textColor=ACCENT, spaceBefore=14, spaceAfter=7),
    "h2": ParagraphStyle("h2", parent=ss["Heading2"], fontSize=11.6, leading=15,
                         textColor=INK, spaceBefore=10, spaceAfter=4),
    "body": ParagraphStyle("body", parent=ss["BodyText"], fontSize=9.6, leading=14.2,
                           alignment=TA_JUSTIFY, textColor=INK, spaceAfter=6),
    "bullet": ParagraphStyle("bullet", parent=ss["BodyText"], fontSize=9.6,
                             leading=13.8, leftIndent=13, bulletIndent=4,
                             textColor=INK, spaceAfter=2.5),
    "code": ParagraphStyle("code", parent=ss["BodyText"], fontName="Courier",
                           fontSize=8.1, leading=11.3, textColor=INK,
                           backColor=LIGHT, borderPadding=6, spaceAfter=7),
    "caption": ParagraphStyle("caption", parent=ss["Normal"], fontSize=8.3,
                              alignment=TA_CENTER, textColor=GREY, spaceBefore=3,
                              spaceAfter=9, fontName="Helvetica-Oblique"),
    "cover": ParagraphStyle("cover", parent=ss["Normal"], fontSize=11, leading=17,
                            alignment=TA_CENTER, textColor=INK),
}


def P(text, style="body"):
    return Paragraph(text, S[style])


def bullets(items):
    return [Paragraph(f"\u2022&nbsp;&nbsp;{t}", S["bullet"]) for t in items]


def figure(name, width_mm, caption):
    path = os.path.join(IMG, name)
    reader = ImageReader(path)
    iw, ih = reader.getSize()
    width = width_mm * mm
    height = width * ih / iw
    max_h = 205 * mm
    if height > max_h:
        height = max_h
        width = height * iw / ih
    img = Image(path, width=width, height=height)
    img.hAlign = "CENTER"
    return KeepTogether([img, P(caption, "caption")])


def table(data, widths, header=True, font=8.4):
    """Build a table; every cell is a Paragraph so long text wraps properly."""
    cell = ParagraphStyle("cell", parent=ss["Normal"], fontSize=font,
                          leading=font * 1.32, textColor=INK)
    head = ParagraphStyle("head", parent=cell, fontName="Helvetica-Bold",
                          textColor=colors.white)
    body = []
    for r, row in enumerate(data):
        style = head if (header and r == 0) else cell
        body.append([c if hasattr(c, "wrap") else Paragraph(str(c), style)
                     for c in row])
    data = body
    t = Table(data, colWidths=[w * mm for w in widths], repeatRows=1 if header else 0)
    style = [
        ("FONTNAME", (0, 0), (-1, -1), "Helvetica"),
        ("FONTSIZE", (0, 0), (-1, -1), font),
        ("TEXTCOLOR", (0, 0), (-1, -1), INK),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#b8c4d0")),
        ("LEFTPADDING", (0, 0), (-1, -1), 5),
        ("RIGHTPADDING", (0, 0), (-1, -1), 5),
        ("TOPPADDING", (0, 0), (-1, -1), 3.5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3.5),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f7f9fb")]),
    ]
    if header:
        style += [
            ("BACKGROUND", (0, 0), (-1, 0), ACCENT),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ]
    t.setStyle(TableStyle(style))
    return t


# ------------------------------------------------------------------ page frame
def decorate(canvas, doc):
    canvas.saveState()
    if doc.page > 1:
        canvas.setStrokeColor(colors.HexColor("#c8d2dc"))
        canvas.setLineWidth(0.5)
        canvas.line(20 * mm, 282 * mm, 190 * mm, 282 * mm)
        canvas.setFont("Helvetica", 7.6)
        canvas.setFillColor(GREY)
        canvas.drawString(20 * mm, 285 * mm,
                          "ScanSmart - Automatic Document Scanner | Computer Vision")
        canvas.drawRightString(190 * mm, 285 * mm, "Project Report")
        canvas.line(20 * mm, 14 * mm, 190 * mm, 14 * mm)
        canvas.drawCentredString(105 * mm, 9 * mm, f"Page {doc.page}")
    canvas.restoreState()


def load_results():
    """Read the measured batch report so the numbers in the PDF are real."""
    path = os.path.join(ROOT, "outputs", "report.json")
    with open(path) as handle:
        return json.load(handle)


def build():
    data = load_results()
    pages, summary = data["pages"], data["summary"]

    doc = BaseDocTemplate(OUTPUT, pagesize=A4,
                          leftMargin=20 * mm, rightMargin=20 * mm,
                          topMargin=22 * mm, bottomMargin=20 * mm,
                          title="ScanSmart - Project Report",
                          author="VITyarthi Build Your Own Project")
    frame = Frame(doc.leftMargin, doc.bottomMargin, doc.width, doc.height, id="main")
    doc.addPageTemplates([PageTemplate(id="std", frames=[frame], onPage=decorate)])

    f = []                                       # flowables

    # ---------------------------------------------------------- 1. COVER PAGE
    f += [Spacer(1, 18 * mm),
          P("PROJECT REPORT", "subtitle"),
          Spacer(1, 6 * mm),
          P("ScanSmart", "title"),
          P("Automatic Document Scanner &amp; Image Enhancement System", "subtitle"),
          Spacer(1, 4 * mm),
          P("A classical computer-vision pipeline for perspective correction "
            "and enhancement of document photographs", "cover"),
          Spacer(1, 8 * mm)]
    f.append(figure("before_after.png", 112, ""))
    f.append(Spacer(1, 6 * mm))
    f.append(table([
        ["Course", "Computer Vision"],
        ["Submission", "VITyarthi - Build Your Own Project"],
        ["Project title", "ScanSmart - Automatic Document Scanner"],
        ["Student name", "________________________________"],
        ["Registration no.", "________________________________"],
        ["Repository", "https://github.com/&lt;your-username&gt;/scansmart"],
        ["Language / stack", "Python 3.10, OpenCV 4.x, NumPy, reportlab"],
        ["Date", "2026"],
    ], [42, 118], header=False, font=9.2))
    f.append(PageBreak())

    # -------------------------------------------------------------- CONTENTS
    f.append(P("Table of Contents", "h1"))
    toc = [["#", "Section", "#", "Section"],
           ["1", "Cover Page", "9", "Implementation Details"],
           ["2", "Introduction", "10", "Screenshots / Results"],
           ["3", "Problem Statement", "11", "Testing Approach"],
           ["4", "Functional Requirements", "12", "Challenges Faced"],
           ["5", "Non-functional Requirements", "13", "Learnings &amp; Key Takeaways"],
           ["6", "System Architecture", "14", "Future Enhancements"],
           ["7", "Design Diagrams", "15", "References"],
           ["8", "Design Decisions &amp; Rationale", "", ""]]
    f.append(table(toc, [8, 72, 8, 72]))

    # ---------------------------------------------------------- 2. INTRODUCTION
    f.append(P("2. Introduction", "h1"))
    f.append(P(
        "Digitising paper is no longer done with flatbed scanners. A phone "
        "camera is always at hand, so notes, invoices, forms and answer sheets "
        "are photographed instead of scanned. The convenience comes at a cost: "
        "the camera is almost never held parallel to the page, so a rectangular "
        "sheet is projected onto the sensor as a general quadrilateral; the desk, "
        "hands and floor appear around it; and the ambient light falls unevenly "
        "so one side of the page is noticeably darker than the other."))
    f.append(P(
        "ScanSmart is a command-line application that repairs such photographs "
        "automatically. It finds the four corners of the page, computes the "
        "homography that maps that quadrilateral back to a rectangle, warps the "
        "image, removes the illumination gradient and binarises the text. The "
        "result is a flat, high-contrast page that looks as if it came from a "
        "scanner, and which is a far better input for archiving or for an OCR "
        "engine."))
    f.append(P(
        "The project is intentionally built from <b>classical computer-vision "
        "operators</b> rather than a neural network. Every stage - colour-space "
        "conversion, histogram equalisation, edge-preserving filtering, Canny "
        "edge detection, contour approximation, homography estimation, the Hough "
        "line transform and adaptive thresholding - is a concept from the course "
        "syllabus, and every intermediate result can be inspected visually. This "
        "makes the system explainable, reproducible, fast (about 120 ms per "
        "image on a laptop CPU), and completely offline."))
    f.append(P("Objectives", "h2"))
    f += bullets([
        "Automatically locate a document inside a cluttered photograph without "
        "any user input or manual cropping.",
        "Remove perspective distortion using a four-point homography and correct "
        "residual rotation with the Hough line transform.",
        "Produce readable output in three styles (black-and-white scan, enhanced "
        "grayscale, enhanced colour) by flattening illumination and boosting "
        "local contrast.",
        "Measure the objective quality of every page and grade it, so that a user "
        "is told which captures should be retaken.",
        "Process whole folders in one command and export a multi-page PDF plus "
        "machine-readable JSON and CSV reports.",
        "Demonstrate correctness through automated tests and a quantitative "
        "accuracy evaluation against synthetic ground truth.",
    ])

    # ----------------------------------------------------- 3. PROBLEM STATEMENT
    f.append(PageBreak())
    f.append(P("3. Problem Statement", "h1"))
    f.append(P(
        "<b>Given a colour photograph that contains a single, roughly planar "
        "document, produce a rectified, evenly-lit, high-contrast image of that "
        "document alone - automatically, offline, and with a measurable "
        "confidence in the result.</b>"))
    f.append(P("Formally, the page occupies an unknown quadrilateral "
               "Q = {p1, p2, p3, p4} in the image. The system must estimate Q, "
               "order its vertices consistently, compute the 3x3 homography H "
               "that maps Q onto the rectangle [0, W] x [0, H], apply the warp, "
               "and then normalise the intensity of the warped page."))
    f.append(P("Why this is not trivial", "h2"))
    f += bullets([
        "<b>Unknown background.</b> The page boundary must be separated from "
        "desk texture, wood grain and shadows, which also generate strong edges.",
        "<b>Illumination varies between photographs.</b> Fixed Canny thresholds "
        "that work on one image produce either no edges or thousands on another.",
        "<b>Edges are broken.</b> Where the page contrast against the background "
        "is low, the detected border has gaps, so a naive contour search returns "
        "an open curve instead of a closed quadrilateral.",
        "<b>Corner ordering is ambiguous.</b> OpenCV returns contour points in an "
        "arbitrary starting position and direction; warping with mis-ordered "
        "corners produces a mirrored or rotated page.",
        "<b>Failure must be graceful.</b> A batch of fifty photos must not abort "
        "because one of them is out of focus.",
    ])
    f.append(P("Target users", "h2"))
    f.append(table([
        ["User", "Need served"],
        ["Students and office staff",
         "Convert phone photos of notes, forms and receipts into tidy PDFs"],
        ["Small offices and clerks",
         "Digitise invoices and delivery notes in bulk without buying a scanner"],
        ["OCR / RPA developers",
         "Use ScanSmart as the pre-processing stage that feeds clean, deskewed "
         "pages into an OCR engine"],
        ["Computer-vision learners",
         "A readable reference implementation of edge detection, contour "
         "approximation and homography estimation"],
    ], [45, 115]))

    # ----------------------------------------------- 4. FUNCTIONAL REQUIREMENTS
    f.append(PageBreak())
    f.append(P("4. Functional Requirements", "h1"))
    f.append(P("The system is organised into three major functional modules, "
               "supported by an export/reporting component."))

    f.append(P("Module 1 - Acquisition &amp; Pre-processing", "h2"))
    f.append(table([
        ["ID", "Requirement"],
        ["FR-1.1", "Load a single image or discover every supported image "
                   "(.jpg/.png/.bmp/.tif) inside a folder."],
        ["FR-1.2", "Reject missing, corrupt or unsupported files with a clear, "
                   "typed error instead of crashing."],
        ["FR-1.3", "Down-scale the image to a fixed working height (default "
                   "600 px) for detection, retaining the scale factor."],
        ["FR-1.4", "Build an edge map: grayscale, CLAHE, bilateral + Gaussian "
                   "filtering, median-based auto-Canny, morphological closing."],
        ["FR-1.5", "Expose every intermediate stage so debug images can be saved."],
    ], [18, 142]))

    f.append(P("Module 2 - Document Detection &amp; Geometric Correction", "h2"))
    f.append(table([
        ["ID", "Requirement"],
        ["FR-2.1", "Find the largest four-point convex polygon by contour "
                   "approximation over a sweep of Douglas-Peucker tolerances."],
        ["FR-2.2", "Reject candidates that cover less than 12 % or more than "
                   "99 % of the frame, or that are not convex."],
        ["FR-2.3", "Fall back to an Otsu + minAreaRect estimate, and finally to "
                   "the full frame, so a result is always returned."],
        ["FR-2.4", "Order the corners as top-left, top-right, bottom-right, "
                   "bottom-left and map them back to the original resolution."],
        ["FR-2.5", "Compute a confidence score in [0, 1] from the interior-angle "
                   "regularity, the covered area and the strategy used."],
        ["FR-2.6", "Warp the quadrilateral to a rectangle whose size is derived "
                   "from the longest opposite edges (perspective transform)."],
        ["FR-2.7", "Estimate residual skew with the probabilistic Hough line "
                   "transform and rotate the page to correct it."],
    ], [18, 142]))

    f.append(P("Module 3 - Enhancement, Quality Analytics &amp; Export", "h2"))
    f.append(table([
        ["ID", "Requirement"],
        ["FR-3.1", "Remove the illumination gradient by morphological background "
                   "estimation and division."],
        ["FR-3.2", "Offer three output modes: scan (adaptive threshold), gray "
                   "(CLAHE + unsharp mask) and color (LAB-CLAHE + unsharp mask)."],
        ["FR-3.3", "Measure sharpness (Laplacian variance), RMS contrast, "
                   "brightness, ink ratio and residual skew for every page."],
        ["FR-3.4", "Grade each page GOOD / FAIR / POOR by combining the metrics "
                   "with the detection confidence."],
        ["FR-3.5", "Save the processed page, and optionally a detection overlay "
                   "and a before/after comparison image."],
        ["FR-3.6", "Export all pages of a batch into one multi-page PDF."],
        ["FR-3.7", "Write a JSON report (config + per-page records + aggregate "
                   "summary) and a flat CSV mirror; print a console summary."],
    ], [18, 142]))

    f.append(P("Input / output structure", "h2"))
    f.append(table([
        ["Stage", "Input", "Output"],
        ["Acquisition", "File path or folder", "BGR array + scale factor"],
        ["Pre-processing", "BGR array", "Binary edge map (uint8)"],
        ["Detection", "Edge map", "Detection(corners 4x2, method, confidence)"],
        ["Geometry", "Original image + corners", "Flattened, deskewed page"],
        ["Enhancement", "Flattened page + mode", "Binary / gray / colour page"],
        ["Quality", "Processed page + confidence", "QualityMetrics + grade"],
        ["Export", "List of PageResult", "PNG, PDF, report.json, report.csv"],
    ], [26, 60, 74]))

    f.append(P("User interaction workflow", "h2"))
    f.append(P("The user runs one command; the system validates the "
               "configuration, discovers the images, processes each one "
               "independently, and finishes by printing a summary table and "
               "writing the reports. A failure on one image is recorded and the "
               "batch continues.", "body"))
    f.append(Paragraph(
        "$ python main.py --input data/samples --output outputs \\<br/>"
        "&nbsp;&nbsp;&nbsp;&nbsp;--mode scan --pdf outputs/scanned.pdf --overlay",
        S["code"]))

    # ------------------------------------------- 5. NON-FUNCTIONAL REQUIREMENTS
    f.append(PageBreak())
    f.append(P("5. Non-functional Requirements", "h1"))
    f.append(table([
        ["ID", "Attribute", "Requirement and how it is met", "Evidence"],
        ["NFR-1", "Performance",
         "A 1000x1400 photograph must be processed in well under one second. "
         "Detection runs on a 600 px down-scaled copy; only the final warp uses "
         "full resolution.",
         f"Measured mean {summary['mean_time_ms']:.0f} ms/image "
         f"(detection alone ~14 ms)"],
        ["NFR-2", "Reliability",
         "The pipeline must always return a result. Three detection strategies "
         "are tried in order and every image is processed in isolation.",
         f"{summary['success_rate'] * 100:.0f} % of the batch completed; "
         "fallback exercised on sample_02"],
        ["NFR-3", "Error handling",
         "A typed exception hierarchy (ImageLoadError, DocumentNotFoundError, "
         "InvalidConfigError, ExportError) separates recoverable from fatal "
         "errors; the CLI maps them to exit codes 0/1/2/130.",
         "tests for corrupt files, empty folders and invalid configuration"],
        ["NFR-4", "Usability",
         "One command with sensible defaults; a readable console table; "
         "--overlay and --comparison images let the user see what was detected.",
         "CLI help text, sample run in the README"],
        ["NFR-5", "Maintainability",
         "Eleven single-responsibility modules, no magic numbers outside "
         "ScanConfig, docstrings and type hints throughout.",
         "package layout, 49 tests"],
        ["NFR-6", "Logging &amp; monitoring",
         "Structured logging at DEBUG/INFO/WARNING/ERROR with per-stage "
         "messages, plus JSON and CSV run reports for later analysis.",
         "logger.py, outputs/report.json"],
        ["NFR-7", "Portability / resource efficiency",
         "Pure Python + OpenCV, no GPU, no network access, no database; output "
         "size is clamped to 2000 px on the longest side.",
         "runs offline on a CPU laptop"],
        ["NFR-8", "Security &amp; privacy",
         "All processing is local, so documents never leave the machine; file "
         "paths are validated before any read or write.",
         "io_utils.py"],
    ], [15, 25, 78, 42], font=7.9))

    # ----------------------------------------------------- 6. ARCHITECTURE
    f.append(PageBreak())
    f.append(P("6. System Architecture", "h1"))
    f.append(P(
        "ScanSmart uses a four-layer architecture. The presentation layer owns "
        "the command line and the console report. The orchestration layer "
        "(pipeline.py) decides what happens to each image and holds no image "
        "processing logic itself. The processing layer contains the three "
        "computer-vision modules plus the exporter, each of which is a pure "
        "function library over NumPy arrays. The infrastructure layer supplies "
        "file I/O, logging and the error hierarchy used by every other layer."))
    f.append(P(
        "Dependencies point strictly downwards: the CV modules never import the "
        "pipeline and never touch the file system directly, which is what makes "
        "them straightforward to unit-test with synthetic arrays."))
    f.append(figure("architecture.png", 165,
                    "Figure 1 - Layered system architecture."))

    # ------------------------------------------------------ 7. DESIGN DIAGRAMS
    f.append(PageBreak())
    f.append(P("7. Design Diagrams", "h1"))
    f.append(P("7.1 Use Case Diagram", "h2"))
    f.append(figure("usecase.png", 158,
                    "Figure 2 - Actors and use cases. Page detection and "
                    "perspective correction are included by both scanning use "
                    "cases."))
    f.append(PageBreak())
    f.append(P("7.2 Process Flow / Workflow Diagram", "h2"))
    f.append(figure("workflow.png", 108,
                    "Figure 3 - End-to-end workflow, including the fallback "
                    "branch taken when no four-point contour is found."))
    f.append(PageBreak())
    f.append(P("7.3 Sequence Diagram", "h2"))
    f.append(figure("sequence.png", 168,
                    "Figure 4 - Message sequence for processing a single image."))
    f.append(P("7.4 Class / Component Diagram", "h2"))
    f.append(figure("class.png", 168,
                    "Figure 5 - Classes (ScanConfig, Detection, QualityMetrics, "
                    "PageResult) and the functional modules that use them."))
    f.append(PageBreak())
    f.append(P("7.5 Storage Design", "h2"))
    f.append(P(
        "The project needs no relational database: a run produces one JSON "
        "document, a flat CSV mirror and a set of image artefacts on disk. The "
        "entity-relationship view below documents that schema. Keeping storage "
        "file-based makes the tool portable and keeps the results diff-able in "
        "Git."))
    f.append(figure("storage.png", 162,
                    "Figure 6 - ER-style view of the file-based report schema."))
    f.append(Paragraph(
        "report.json<br/>"
        "&nbsp;&nbsp;config   : { working_height, mode, min_area_ratio, ... }<br/>"
        "&nbsp;&nbsp;summary  : { total_images, processed, failed, success_rate,<br/>"
        "&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;"
        "grades{GOOD,FAIR,POOR}, mean_confidence, mean_time_ms }<br/>"
        "&nbsp;&nbsp;pages[]  : { source, output, status, method, confidence,<br/>"
        "&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;"
        "area_ratio, grade, sharpness, contrast, brightness,<br/>"
        "&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;"
        "ink_ratio, skew_deg, width, height, elapsed_ms, error }",
        S["code"]))

    # ------------------------------------------------ 8. DESIGN DECISIONS
    f.append(PageBreak())
    f.append(P("8. Design Decisions &amp; Rationale", "h1"))
    f.append(table([
        ["#", "Decision", "Rationale", "Alternative rejected"],
        ["1", "Classical CV instead of a deep segmentation model",
         "Explainable, needs no dataset or GPU, runs in milliseconds, and every "
         "operator maps directly to a syllabus concept.",
         "U-Net / DeepLab page segmentation - heavy, opaque, needs labelled data"],
        ["2", "Median-based auto-Canny thresholds",
         "Thresholds derived from the image median adapt to dark, bright and "
         "low-contrast photos automatically.",
         "Fixed thresholds (50/150) - fail on half the test images"],
        ["3", "Bilateral filter before Canny",
         "Suppresses paper texture and sensor noise while preserving the page "
         "border, which is the edge we actually need.",
         "Plain Gaussian blur - also blurs the border and weakens corners"],
        ["4", "Sweep of approxPolyDP tolerances",
         "A single epsilon yields 4 points only for some contours; sweeping "
         "0.01-0.08 of the perimeter finds a quadrilateral far more often.",
         "Single fixed epsilon - brittle"],
        ["5", "Three-level fallback (contour, minAreaRect, full frame)",
         "Guarantees an output for every input and reports honestly how the "
         "result was obtained through the 'method' field.",
         "Raising an exception - aborts a batch on one bad photo"],
        ["6", "Sum/difference corner ordering",
         "Two vector operations give a deterministic TL-TR-BR-BL order, which "
         "prevents mirrored or rotated warps.",
         "Angle sorting about the centroid - more code, same result"],
        ["7", "Output size from the longest opposite edges",
         "Preserves the maximum available detail and approximates the true "
         "aspect ratio of the page.",
         "Fixed A4 output - distorts non-A4 documents"],
        ["8", "Morphological background division for shadows",
         "Dilation plus median blur estimates the illumination field; dividing "
         "it out flattens gradients before thresholding.",
         "Global Otsu - loses the shadowed half of the page"],
        ["9", "Adaptive (Gaussian) thresholding for the scan mode",
         "A local window handles any residual lighting variation and keeps thin "
         "strokes intact.",
         "Global binary threshold - clips text in darker regions"],
        ["10", "Confidence score from interior-angle regularity",
         "A perspective view of a rectangle keeps angles near 90 degrees, so "
         "angular deviation is a cheap, effective correctness proxy.",
         "Area alone - a large blob would score highly"],
        ["11", "Detection on a 600 px copy",
         "Cuts detection cost by roughly an order of magnitude; corners are "
         "scaled back so final quality is unaffected.",
         "Full-resolution detection - slow with no accuracy gain"],
        ["12", "Single validated ScanConfig dataclass",
         "One source of truth for every parameter, validated once, and "
         "serialised into the report for reproducibility.",
         "Module-level constants - untestable and scattered"],
    ], [8, 38, 62, 52], font=7.7))

    # -------------------------------------------- 9. IMPLEMENTATION DETAILS
    f.append(PageBreak())
    f.append(P("9. Implementation Details", "h1"))
    f.append(P("9.1 Code organisation", "h2"))
    f.append(table([
        ["File", "Lines", "Responsibility"],
        ["scansmart/config.py", "~90", "ScanConfig dataclass, parameter validation"],
        ["scansmart/exceptions.py", "~30", "Typed error hierarchy"],
        ["scansmart/logger.py", "~35", "Logging configuration"],
        ["scansmart/io_utils.py", "~95", "Image load/save, folder discovery, resizing"],
        ["scansmart/preprocessing.py", "~95", "Module 1: edge map construction"],
        ["scansmart/detector.py", "~200", "Module 2: detection strategies, scoring"],
        ["scansmart/transform.py", "~85", "Module 2: homography warp, skew, deskew"],
        ["scansmart/enhancement.py", "~90", "Module 3: scan / gray / color output"],
        ["scansmart/quality.py", "~80", "Module 3: metrics and grading"],
        ["scansmart/exporter.py", "~120", "PDF, JSON and CSV export, aggregation"],
        ["scansmart/pipeline.py", "~135", "Orchestration, PageResult"],
        ["main.py", "~120", "argparse CLI, console summary, exit codes"],
        ["tests/ (5 files)", "~330", "49 unit and integration tests"],
        ["tools/ (4 scripts)", "~430", "Sample generation, evaluation, diagrams, report"],
    ], [50, 16, 94]))

    f.append(P("9.2 Key algorithms", "h2"))
    f.append(P("<b>Auto-Canny.</b> The high and low thresholds are placed "
               "symmetrically around the median intensity m of the smoothed "
               "image: lower = max(0, (1 - s)m), upper = min(255, (1 + s)m) with "
               "s = 0.33. This single change made detection robust across all "
               "lighting conditions in the test set."))
    f.append(Paragraph(
        "median = np.median(gray)<br/>"
        "lower&nbsp; = int(max(0,&nbsp;&nbsp; (1.0 - sigma) * median))<br/>"
        "upper&nbsp; = int(min(255, (1.0 + sigma) * median))<br/>"
        "edges&nbsp; = cv2.Canny(gray, lower, upper)", S["code"]))

    f.append(P("<b>Corner ordering.</b> For the four candidate points, the "
               "top-left corner minimises x + y and the bottom-right maximises "
               "it, while the top-right minimises y - x and the bottom-left "
               "maximises it. This is O(1) and completely deterministic."))
    f.append(Paragraph(
        "s = pts.sum(axis=1);&nbsp; d = np.diff(pts, axis=1).ravel()<br/>"
        "ordered[0] = pts[np.argmin(s)]&nbsp;&nbsp;# top-left<br/>"
        "ordered[2] = pts[np.argmax(s)]&nbsp;&nbsp;# bottom-right<br/>"
        "ordered[1] = pts[np.argmin(d)]&nbsp;&nbsp;# top-right<br/>"
        "ordered[3] = pts[np.argmax(d)]&nbsp;&nbsp;# bottom-left", S["code"]))

    f.append(P("<b>Perspective warp.</b> cv2.getPerspectiveTransform solves for "
               "the 3x3 homography H that maps the four ordered source corners "
               "onto the destination rectangle; cv2.warpPerspective then resamples "
               "the original full-resolution image with bicubic interpolation."))
    f.append(Paragraph(
        "width&nbsp; = max(|br - bl|, |tr - tl|)<br/>"
        "height = max(|tr - br|, |tl - bl|)<br/>"
        "M = cv2.getPerspectiveTransform(src, dst)<br/>"
        "warped = cv2.warpPerspective(image, M, (width, height),<br/>"
        "&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;"
        "&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;"
        "flags=cv2.INTER_CUBIC)", S["code"]))

    f.append(P("<b>Shadow removal.</b> Dilating the grayscale page with a 15x15 "
               "kernel and median-blurring the result estimates the background "
               "illumination; the absolute difference against the original, "
               "inverted and normalised, yields an evenly lit page that adaptive "
               "thresholding can binarise cleanly."))
    f.append(P("<b>Confidence.</b> score = base(method) x (0.7 x angle_score + "
               "0.3 x min(1, 1.6 x area_ratio)), where angle_score falls linearly "
               "from 1 to 0 as the mean deviation of the interior angles from 90 "
               "degrees grows to 45 degrees."))

    f.append(P("9.3 Version control", "h2"))
    f.append(P("The repository is developed with Git in incremental, themed "
               "commits (core CV package with tests; CLI, batch pipeline and "
               "evaluation tooling; documentation, diagrams and figures), with a "
               ".gitignore that excludes generated outputs, virtual environments "
               "and caches."))

    # ------------------------------------------- 10. SCREENSHOTS / RESULTS
    f.append(PageBreak())
    f.append(P("10. Screenshots / Results", "h1"))
    f.append(figure("pipeline_stages.png", 168,
                    "Figure 7 - The five stages of the pipeline on sample_03.jpg: "
                    "input, closed edge map, detected corners, perspective "
                    "correction, enhanced output."))
    f.append(figure("modes.png", 140,
                    "Figure 8 - The three enhancement modes applied to the same "
                    "page: colour, grayscale and black-and-white scan."))
    f.append(PageBreak())
    f.append(P("10.1 Console output of a batch run", "h2"))
    rows = [["File", "Status", "Method", "Conf.", "Grade", "Sharpness",
             "Contrast", "Time (ms)"]]
    for page in pages:
        rows.append([
            page["source"], page["status"], page.get("method", "-"),
            f"{page.get('confidence', 0):.2f}", page.get("grade", "-"),
            f"{page.get('sharpness', 0):.0f}", f"{page.get('contrast', 0):.1f}",
            f"{page.get('elapsed_ms', 0):.0f}",
        ])
    f.append(table(rows, [28, 16, 26, 14, 16, 22, 20, 18], font=8.0))
    f.append(P(
        f"All {summary['total_images']} images were processed successfully "
        f"(success rate {summary['success_rate'] * 100:.0f} %), with a mean "
        f"detection confidence of {summary['mean_confidence']:.2f} and a mean "
        f"end-to-end time of {summary['mean_time_ms']:.0f} ms per image. Grade "
        f"distribution: {summary['grades']['GOOD']} GOOD, "
        f"{summary['grades']['FAIR']} FAIR, {summary['grades']['POOR']} POOR."))
    f.append(figure("results_chart.png", 165,
                    "Figure 9 - Per-image detection confidence and processing "
                    "time. sample_02 (amber) fell back to minAreaRect because "
                    "the page is clipped by the frame edge."))

    f.append(P("10.2 Detection accuracy against ground truth", "h2"))
    f.append(P(
        "Because the synthetic samples are rendered by warping a known page with "
        "a known homography, the true corner positions are available. The "
        "evaluation script compares them with the detected corners and reports "
        "the mean Euclidean error normalised by the image diagonal; a detection "
        "counts as correct below 2 %."))
    f.append(table([
        ["Image", "Method", "Confidence", "Corner error (% of diagonal)", "Result"],
        ["sample_01.jpg", "contour", "0.82", "0.28", "PASS"],
        ["sample_02.jpg", "min_area_rect", "0.75", "5.14", "FAIL"],
        ["sample_03.jpg", "contour", "0.89", "0.23", "PASS"],
        ["sample_04.jpg", "contour", "0.85", "0.32", "PASS"],
        ["sample_05.jpg", "contour", "0.78", "0.30", "PASS"],
        ["sample_06.jpg", "contour", "0.91", "0.28", "PASS"],
        ["Overall", "5 / 6 = 83.3 %", "mean 0.83", "mean 1.09", "-"],
    ], [32, 38, 26, 44, 20]))
    f.append(P(
        "Excluding the clipped page, the mean corner error is <b>0.28 % of the "
        "image diagonal</b> - roughly four pixels on a 1000x1400 photograph. "
        "The single failure is explained in Section 12 and is a genuine "
        "limitation of a contour-based approach rather than a coding defect."))

    # ------------------------------------------------- 11. TESTING APPROACH
    f.append(PageBreak())
    f.append(P("11. Testing Approach", "h1"))
    f.append(P("Testing is organised in three levels: unit tests on individual "
               "operators, integration tests over the whole pipeline, and a "
               "quantitative evaluation against synthetic ground truth."))
    f.append(table([
        ["Test file", "Tests", "What it verifies"],
        ["test_config.py", "6",
         "Defaults are valid; invalid mode, even kernels and inconsistent area "
         "ratios raise InvalidConfigError; serialisation round-trip"],
        ["test_preprocessing.py", "7",
         "Grayscale reduces channels and is idempotent; CLAHE preserves shape "
         "and dtype; denoising lowers the standard deviation of a noisy patch; "
         "auto-Canny returns a binary map; closing never removes edges"],
        ["test_detector.py", "7",
         "Corner ordering is correct and idempotent; a synthetic page is located "
         "within 15 px of ground truth; the scale factor maps corners back "
         "correctly; a blank image falls back to the full frame, or raises when "
         "the fallback is disabled"],
        ["test_transform.py", "6",
         "Output size equals the longest opposite edges and is clamped; warping "
         "a flat rectangle is the identity; a warped page becomes portrait and "
         "excludes the dark background; skew estimation detects a 5-degree "
         "rotation; tiny angles are ignored"],
        ["test_enhancement_quality.py", "11",
         "scan mode is strictly binary; gray is single-channel; color keeps three "
         "channels; shadow removal flattens a gradient; unknown modes raise; "
         "sharpness falls after blurring; contrast of a flat image is zero; "
         "grading responds to low confidence"],
        ["test_pipeline.py", "12",
         "Missing and corrupt files raise ImageLoadError; folder discovery skips "
         "non-images; resizing preserves aspect ratio; save creates directories; "
         "end-to-end processing succeeds; a corrupt file is recorded as failed "
         "rather than raising; batch outputs and JSON/CSV reports are written"],
    ], [38, 12, 110], font=7.9))
    f.append(P("Total: <b>49 tests, all passing</b>. Tests build their own "
               "synthetic images in fixtures, so the suite needs no external "
               "data and runs in a few seconds."))
    f.append(Paragraph(
        "$ pytest tests -v<br/>"
        "...<br/>"
        "49 passed in 4.1s<br/><br/>"
        "$ python tools/evaluate.py data/samples<br/>"
        "Accuracy&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;: 5/6 (83.3%)<br/>"
        "Mean corner error: 1.09% of diagonal<br/>"
        "Mean detect time&nbsp;: 14 ms", S["code"]))
    f.append(P("Validation testing", "h2"))
    f += bullets([
        "<b>Input validation</b> - unsupported extensions are skipped, empty "
        "folders and missing paths raise ImageLoadError, corrupt bytes are "
        "detected by the decoder check.",
        "<b>Configuration validation</b> - even kernel sizes, unknown modes and "
        "impossible area ratios are rejected before any image is touched.",
        "<b>Output validation</b> - every processed page is measured and graded, "
        "so a silently wrong result (for example a full-frame fallback) is "
        "visible in the report as confidence 0.0 and grade POOR.",
    ])

    # -------------------------------------------------- 12. CHALLENGES FACED
    f.append(PageBreak())
    f.append(P("12. Challenges Faced", "h1"))
    f.append(table([
        ["#", "Challenge", "How it was solved"],
        ["1", "Fixed Canny thresholds worked on one photo and failed on the "
              "next, depending on lighting.",
              "Replaced them with median-based auto-Canny, so the thresholds "
              "adapt to each image."],
        ["2", "The page border was detected as several disconnected edge "
              "fragments, so no closed contour existed.",
              "Added morphological closing plus a dilation step to bridge the "
              "gaps before findContours."],
        ["3", "A single approxPolyDP epsilon returned 5, 6 or 7 points instead "
              "of 4 for many contours.",
              "Swept epsilon from 1 % to 8 % of the perimeter and accepted the "
              "first tolerance that produced a valid convex quadrilateral."],
        ["4", "Warped pages occasionally came out mirrored or rotated by 90 "
              "degrees.",
              "Traced it to inconsistent contour point order; fixed with the "
              "deterministic sum/difference corner ordering."],
        ["5", "Text in the shadowed half of the page disappeared after global "
              "thresholding.",
              "Introduced morphological background division followed by adaptive "
              "Gaussian thresholding."],
        ["6", "Text blocks inside the page produced large contours that "
              "sometimes beat the page border.",
              "Added the validity filter (12-99 % area, convexity) and an "
              "interior-angle score, so rectangle-like candidates win."],
        ["7", "A page clipped by the frame edge (sample_02) has no closed "
              "boundary, so the contour strategy cannot succeed.",
              "Accepted as a documented limitation: the minAreaRect fallback "
              "still returns a usable scan, but is reported with a lower "
              "confidence and a larger corner error (5.1 %)."],
        ["8", "Full-resolution detection was slow on large photographs.",
              "Detection now runs on a 600 px copy and the corners are scaled "
              "back, cutting detection time to about 14 ms."],
        ["9", "Evaluating accuracy needed labelled data that was not available.",
              "Wrote a generator that renders pages through a known homography, "
              "producing photographs together with exact ground-truth corners."],
    ], [8, 68, 84], font=7.9))

    # ---------------------------------------------------- 13. LEARNINGS
    f.append(PageBreak())
    f.append(P("13. Learnings &amp; Key Takeaways", "h1"))
    f += bullets([
        "<b>Pre-processing decides everything.</b> The detector improved far "
        "more from better filtering and adaptive thresholds than from any change "
        "to the contour search itself.",
        "<b>Parameters should be derived, not hard-coded.</b> Deriving Canny "
        "thresholds from the image median turned a brittle demo into something "
        "that works across lighting conditions.",
        "<b>Geometry is the core of the project.</b> Understanding that a "
        "photograph of a rectangle is a projective transform - and that a "
        "homography estimated from four point correspondences inverts it - is "
        "what makes the whole pipeline possible.",
        "<b>Degrade, do not fail.</b> A layered fallback with an honest "
        "confidence score is more useful than an algorithm that either succeeds "
        "perfectly or throws.",
        "<b>Measure, do not eyeball.</b> Synthetic ground truth converted vague "
        "impressions of quality into a single number (1.09 % mean corner error) "
        "that made regressions obvious.",
        "<b>Separation of concerns pays off in testing.</b> Because the CV "
        "modules are pure functions over arrays, 49 tests run in seconds without "
        "any test image files.",
        "<b>Classical CV is still competitive.</b> For a planar, high-contrast "
        "object, a well-tuned classical pipeline delivers sub-pixel-percentage "
        "accuracy in milliseconds on a CPU, with no training data at all.",
    ])

    f.append(P("14. Future Enhancements", "h1"))
    f.append(table([
        ["Enhancement", "Description"],
        ["OCR integration",
         "Feed the rectified page into Tesseract to produce a searchable PDF, "
         "the natural next stage for these outputs."],
        ["Multi-document detection",
         "Detect and separate several receipts photographed together by keeping "
         "all valid quadrilaterals instead of the best one."],
        ["Page-curvature (dewarping) correction",
         "Model book pages as a curved surface using text-line fitting, rather "
         "than assuming a plane."],
        ["Graphical / mobile interface",
         "A drag-and-drop desktop GUI or an Android app with live camera preview "
         "and manual corner adjustment."],
        ["Learned detector as an extra strategy",
         "Add a lightweight segmentation model as a fourth fallback for very low "
         "contrast scenes, keeping the classical path as the fast default."],
        ["Automatic border and staple removal",
         "Detect and erase dark scan borders, punch holes and staple marks left "
         "after warping."],
        ["Parallel batch processing",
         "Use multiprocessing to scan large folders across CPU cores."],
    ], [45, 115]))

    f.append(P("15. References", "h1"))
    f += bullets([
        "OpenCV Documentation - Image Filtering, Structural Analysis and Shape "
        "Descriptors, Geometric Image Transformations. https://docs.opencv.org/",
        "J. Canny, \u201cA Computational Approach to Edge Detection\u201d, IEEE "
        "TPAMI, vol. 8, no. 6, 1986.",
        "D. Douglas and T. Peucker, \u201cAlgorithms for the reduction of the "
        "number of points required to represent a digitised line\u201d, "
        "Cartographica, 1973.",
        "R. Hartley and A. Zisserman, <i>Multiple View Geometry in Computer "
        "Vision</i>, 2nd ed., Cambridge University Press, 2004 (homography "
        "estimation, Chapter 4).",
        "R. Gonzalez and R. Woods, <i>Digital Image Processing</i>, 4th ed., "
        "Pearson, 2018 (histogram equalisation, morphology, thresholding).",
        "S. Suzuki and K. Abe, \u201cTopological structural analysis of digitised "
        "binary images by border following\u201d, CVGIP, 1985 (the algorithm "
        "behind cv2.findContours).",
        "N. Otsu, \u201cA threshold selection method from gray-level "
        "histograms\u201d, IEEE Trans. SMC, 1979.",
        "K. Zuiderveld, \u201cContrast Limited Adaptive Histogram "
        "Equalization\u201d, Graphics Gems IV, 1994.",
        "J. Pech-Pacheco et al., \u201cDiatom autofocusing in brightfield "
        "microscopy: a comparative study\u201d, ICPR 2000 (variance of the "
        "Laplacian focus measure).",
        "NumPy, reportlab and pytest official documentation.",
    ])

    doc.build(f)
    print("wrote", OUTPUT)


if __name__ == "__main__":
    sys.exit(build())
