#!/usr/bin/env python3
"""Render every design diagram used in the project report.

Diagrams are drawn programmatically with matplotlib so that they can be
regenerated whenever the design changes (no binary editor files in Git).

Outputs (docs/images/): architecture, workflow, usecase, sequence, class,
storage and the results chart.
"""

import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch, Circle, Ellipse, Polygon

OUT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                   "docs", "images")
os.makedirs(OUT, exist_ok=True)

INK = "#1b2733"
BLUE = "#d9e8f5"
GREEN = "#dcefdc"
AMBER = "#fbeccd"
GREY = "#ebedf0"
PURPLE = "#e6dff2"


def new_axes(w, h, xlim, ylim):
    fig, ax = plt.subplots(figsize=(w, h), dpi=190)
    ax.set_xlim(*xlim); ax.set_ylim(*ylim)
    ax.axis("off")
    return fig, ax


def box(ax, x, y, w, h, text, color=BLUE, fs=8.5, bold=False, radius=0.06):
    ax.add_patch(FancyBboxPatch((x, y), w, h,
                                boxstyle=f"round,pad=0.02,rounding_size={radius}",
                                facecolor=color, edgecolor=INK, linewidth=1.1))
    ax.text(x + w / 2, y + h / 2, text, ha="center", va="center", fontsize=fs,
            color=INK, weight="bold" if bold else "normal", linespacing=1.45)


def arrow(ax, p1, p2, style="-|>", ls="-", color=INK, rad=0.0, lw=1.2):
    ax.add_patch(FancyArrowPatch(p1, p2, arrowstyle=style, mutation_scale=11,
                                 linewidth=lw, color=color, linestyle=ls,
                                 connectionstyle=f"arc3,rad={rad}",
                                 shrinkA=2, shrinkB=2))


def label(ax, x, y, text, fs=7.4, style="normal", color=INK, ha="center"):
    ax.text(x, y, text, ha=ha, va="center", fontsize=fs, color=color, style=style)


def save(fig, name):
    path = os.path.join(OUT, name)
    fig.savefig(path, bbox_inches="tight", facecolor="white", pad_inches=0.15)
    plt.close(fig)
    print("wrote", path)


# --------------------------------------------------------------- 1. ARCHITECTURE
def architecture():
    fig, ax = new_axes(9.4, 6.6, (0, 100), (0, 74))
    ax.text(50, 71, "ScanSmart - Layered System Architecture",
            ha="center", fontsize=12.5, weight="bold", color=INK)

    layers = [
        (58, 12, "PRESENTATION LAYER", GREY),
        (41, 11, "ORCHESTRATION LAYER", GREY),
        (17, 23, "PROCESSING LAYER  (Computer Vision Core)", GREY),
        (4, 12, "INFRASTRUCTURE LAYER", GREY),
    ]
    for y, h, title, color in layers:
        ax.add_patch(FancyBboxPatch((3, y), 94, h,
                                    boxstyle="round,pad=0.2,rounding_size=0.4",
                                    facecolor="#fafbfc", edgecolor="#9aa7b4",
                                    linewidth=1.0, linestyle="--"))
        ax.text(4.6, y + h - 1.8, title, fontsize=7.6, weight="bold", color="#5a6b7b")

    box(ax, 8, 59.5, 25, 7, "CLI  (main.py)\nargparse interface", AMBER, bold=True)
    box(ax, 38, 59.5, 24, 7, "Batch summary\nconsole table", AMBER)
    box(ax, 67, 59.5, 24, 7, "Exit codes\n0 / 1 / 2 / 130", AMBER)

    box(ax, 22, 42.3, 30, 6.4, "pipeline.py\nprocess_image / process_batch", GREEN, bold=True)
    box(ax, 57, 42.3, 24, 6.4, "config.py\nScanConfig + validation", GREEN)

    mods = [
        (6, 28.5, "M1  Pre-processing\npreprocessing.py\ngray - CLAHE - blur\nauto-Canny - morphology"),
        (30, 28.5, "M2  Detection + Geometry\ndetector.py / transform.py\ncontours - approxPolyDP\nhomography - warp"),
        (54, 28.5, "M3  Enhancement + Quality\nenhancement.py / quality.py\nshadow removal - adaptive\nthreshold - metrics"),
        (78, 28.5, "Export\nexporter.py\nPDF / JSON / CSV\naggregation"),
    ]
    for x, y, text in mods:
        box(ax, x, y, 21, 8.6, text, BLUE, fs=7.5)

    box(ax, 10, 5.8, 22, 6.6, "io_utils.py\nsafe image read/write", PURPLE)
    box(ax, 39, 5.8, 22, 6.6, "logger.py\nstructured logging", PURPLE)
    box(ax, 68, 5.8, 22, 6.6, "exceptions.py\nerror hierarchy", PURPLE)

    arrow(ax, (20.5, 59.5), (30, 48.7))
    arrow(ax, (37, 48.7), (45, 59.5))
    for x in (16.5, 40.5, 64.5, 88.5):
        arrow(ax, (37, 42.9), (x, 37.1), rad=-0.12, lw=1.0)
    arrow(ax, (16.5, 28.5), (21, 12.4), ls=":", style="-", lw=0.9)
    arrow(ax, (50, 28.5), (50, 12.4), ls=":", style="-", lw=0.9)
    arrow(ax, (88.5, 28.5), (79, 12.4), ls=":", style="-", lw=0.9)
    label(ax, 62, 21.5, "OpenCV 4.x  -  NumPy  -  reportlab", fs=8, style="italic",
          color="#5a6b7b")
    save(fig, "architecture.png")


# ------------------------------------------------------------------ 2. WORKFLOW
def workflow():
    fig, ax = new_axes(6.6, 10.2, (0, 60), (0, 100))
    ax.text(30, 97, "Process Flow / Workflow", ha="center", fontsize=12,
            weight="bold", color=INK)

    def node(y, text, color=BLUE, w=34, h=5.6, fs=8.2):
        box(ax, 30 - w / 2, y, w, h, text, color, fs=fs)
        return y

    seq = [
        (88, "Start: user runs CLI\n--input --output --mode", GREEN),
        (80, "Validate configuration\n(ScanConfig)", AMBER),
        (72, "Discover images in folder", BLUE),
        (64, "Load image  ->  down-scale to 600 px", BLUE),
        (56, "Pre-process: gray, CLAHE, bilateral,\nauto-Canny, morphological closing", BLUE),
    ]
    for y, text, color in seq:
        node(y, text, color)
    for i in range(len(seq) - 1):
        arrow(ax, (30, seq[i][0]), (30, seq[i + 1][0] + 5.6))

    # decision diamond
    dia = Polygon([[30, 50.5], [48, 44], [30, 37.5], [12, 44]], closed=True,
                  facecolor=AMBER, edgecolor=INK, linewidth=1.1)
    ax.add_patch(dia)
    ax.text(30, 44, "4-point contour\nfound?", ha="center", va="center", fontsize=8)
    arrow(ax, (30, 56), (30, 50.5))

    box(ax, 0.5, 47, 13, 8, "Fallback:\nminAreaRect\nor full frame\n(flagged)", GREY, fs=6.9)
    arrow(ax, (12, 44), (7, 47), rad=-0.2)
    label(ax, 7.5, 43.5, "no", fs=7.4, style="italic")
    arrow(ax, (7, 47), (13, 32.5), rad=-0.3, ls=":", style="-|>")

    rest = [
        (29, "Order corners (TL,TR,BR,BL)\nestimate homography", BLUE),
        (21, "Warp perspective  ->  flat page\nHough-based deskew", BLUE),
        (13, "Enhance: shadow removal +\nadaptive threshold (scan/gray/color)", BLUE),
        (5, "Quality metrics  ->  grade\nsave PNG / PDF / JSON / CSV", GREEN),
    ]
    arrow(ax, (30, 37.5), (30, 34.6))
    label(ax, 33.5, 36, "yes", fs=7.4, style="italic")
    for y, text, color in rest:
        node(y, text, color)
    for i in range(len(rest) - 1):
        arrow(ax, (30, rest[i][0]), (30, rest[i + 1][0] + 5.6))
    arrow(ax, (47, 7.8), (47, 66.8), rad=0.38, ls="--", style="-|>", color="#7a8896")
    label(ax, 53, 34, "next image\nin the batch", fs=7, style="italic", color="#7a8896")
    save(fig, "workflow.png")


# ------------------------------------------------------------------- 3. USE CASE
def usecase():
    fig, ax = new_axes(9.0, 6.2, (0, 100), (0, 68))
    ax.text(50, 65, "Use Case Diagram", ha="center", fontsize=12, weight="bold", color=INK)

    def actor(x, y, name):
        ax.add_patch(Circle((x, y + 8), 2.2, facecolor="white", edgecolor=INK, lw=1.2))
        ax.plot([x, x], [y + 5.8, y], color=INK, lw=1.2)
        ax.plot([x - 3, x + 3], [y + 4.4, y + 4.4], color=INK, lw=1.2)
        ax.plot([x, x - 2.6], [y, y - 4], color=INK, lw=1.2)
        ax.plot([x, x + 2.6], [y, y - 4], color=INK, lw=1.2)
        ax.text(x, y - 6.5, name, ha="center", fontsize=8.4, weight="bold")

    actor(9, 40, "User /\nStudent")
    actor(91, 40, "File\nSystem")

    ax.add_patch(FancyBboxPatch((24, 6), 52, 54, boxstyle="round,pad=0.3,rounding_size=0.5",
                                facecolor="#fafbfc", edgecolor="#9aa7b4", lw=1.1))
    ax.text(50, 57.5, "ScanSmart System", ha="center", fontsize=9, style="italic",
            color="#5a6b7b")

    cases = [
        (50, 52, "Scan a single photo"),
        (50, 42.5, "Batch-scan a folder"),
        (50, 34.5, "Choose output mode\n(scan / gray / colour)"),
        (50, 26.5, "Export multi-page PDF"),
        (50, 18.5, "View quality report\n(JSON / CSV / console)"),
        (50, 10.5, "Inspect detection overlay"),
    ]
    for x, y, text in cases:
        ax.add_patch(Ellipse((x, y), 40, 5.8, facecolor=BLUE, edgecolor=INK, lw=1.0))
        ax.text(x, y, text, ha="center", va="center", fontsize=7.8)
        arrow(ax, (13.5, 40), (x - 20, y), style="-", lw=0.9)
        arrow(ax, (86.5, 40), (x + 20, y), style="-", lw=0.9, color="#7a8896")

    arrow(ax, (40, 48.8), (40, 45.8), style="-|>", ls="--", color="#7a8896", lw=0.9)
    label(ax, 58, 47.3, "<<include>>  detect + warp", fs=6.3, style="italic",
          color="#5a6b7b")
    save(fig, "usecase.png")


# ------------------------------------------------------------------- 4. SEQUENCE
def sequence():
    fig, ax = new_axes(10.0, 6.8, (0, 108), (0, 74))
    ax.text(54, 71, "Sequence Diagram - processing one image", ha="center",
            fontsize=12, weight="bold", color=INK)

    actors = [(8, "User\n(CLI)"), (27, "Pipeline"), (47, "Detector"), (66, "Transform"),
              (84, "Enhancer\n+ Quality"), (101, "Exporter")]
    for x, name in actors:
        box(ax, x - 8, 60, 16, 6.5, name, GREEN, fs=7.6, bold=True)
        ax.plot([x, x], [60, 6], color="#9aa7b4", lw=0.9, ls="--")

    msgs = [
        (8, 27, 55, "process_image(path)"),
        (27, 47, 50.5, "detect_document(img)"),
        (47, 47, 47, "build_edge_map + contours"),
        (47, 27, 40.5, "Detection(corners, confidence)"),
        (27, 66, 37, "four_point_transform(corners)"),
        (66, 27, 32.5, "flattened page"),
        (27, 84, 28, "enhance() + analyse()"),
        (84, 27, 23.5, "processed page + metrics"),
        (27, 101, 19, "save PNG / PDF / report"),
        (101, 27, 14.5, "output paths"),
        (27, 8, 10, "PageResult (status, grade)"),
    ]
    for x1, x2, y, text in msgs:
        if x1 == x2:                                   # self-call
            ax.plot([x1, x1 + 7, x1 + 7, x1], [y, y, y - 3, y - 3], color=INK, lw=1.1)
            arrow(ax, (x1 + 6.5, y - 3), (x1, y - 3))
            label(ax, x1 + 9, y + 1.3, text, fs=6.9, ha="left")
        else:
            dashed = x2 < x1
            arrow(ax, (x1, y), (x2, y), ls="--" if dashed else "-",
                  color="#5a6b7b" if dashed else INK)
            label(ax, (x1 + x2) / 2, y + 1.7, text, fs=6.9,
                  style="italic" if dashed else "normal")
    save(fig, "sequence.png")


# ---------------------------------------------------------------------- 5. CLASS
def klass():
    fig, ax = new_axes(9.6, 7.0, (0, 100), (0, 74))
    ax.text(50, 71, "Class / Component Diagram", ha="center", fontsize=12,
            weight="bold", color=INK)

    def uml(x, y, w, h, title, attrs, color=BLUE):
        box(ax, x, y, w, h, "", color, radius=0.02)
        ax.text(x + w / 2, y + h - 2.4, title, ha="center", fontsize=8.2, weight="bold")
        ax.plot([x, x + w], [y + h - 4.2, y + h - 4.2], color=INK, lw=1.0)
        ax.text(x + 1.4, y + h - 5.4, attrs, ha="left", va="top", fontsize=6.7,
                linespacing=1.6)

    uml(3, 46, 27, 22, "ScanConfig",
        "+ working_height: int\n+ mode: str\n+ min_area_ratio: float\n"
        "+ adaptive_block: int\n- - -\n+ validate()\n+ to_dict()", GREEN)
    uml(36, 46, 28, 22, "ScanPipeline  <<module>>",
        "+ process_image(path, cfg)\n+ process_batch(dir, out, cfg)\n- - -\n"
        "uses Detector, Transform,\nEnhancer, Quality, Exporter", AMBER)
    uml(70, 46, 27, 22, "PageResult",
        "+ source: str\n+ status: str\n+ detection: Detection\n+ metrics: QualityMetrics\n"
        "- - -\n+ to_record(): dict", GREEN)

    uml(3, 18, 27, 22, "Detector  <<module>>",
        "+ detect_document()\n+ order_corners()\n- _find_by_contour()\n"
        "- _find_by_min_area_rect()\n- _angle_score()")
    uml(36, 18, 28, 22, "Transform  <<module>>",
        "+ four_point_transform()\n+ estimate_output_size()\n+ estimate_skew()\n+ deskew()")
    uml(70, 18, 27, 22, "Enhancement  <<module>>",
        "+ enhance(img, cfg)\n+ to_scan() / to_gray()\n+ to_color()\n+ remove_shadows()")

    uml(3, 1, 27, 14, "Detection",
        "+ corners: ndarray(4,2)\n+ method: str\n+ confidence: float", PURPLE)
    uml(36, 1, 28, 14, "QualityMetrics",
        "+ sharpness / contrast\n+ skew_deg / ink_ratio\n+ grade: str", PURPLE)
    uml(70, 1, 27, 14, "Exporter  <<module>>",
        "+ export_pdf()\n+ write_json_report()\n+ summarise()", PURPLE)

    arrow(ax, (30, 57), (36, 57)); label(ax, 33, 59, "uses", fs=6.5, style="italic")
    arrow(ax, (64, 57), (70, 57)); label(ax, 67, 59, "creates", fs=6.5, style="italic")
    arrow(ax, (45, 46), (16.5, 40), rad=0.12)
    arrow(ax, (50, 46), (50, 40))
    arrow(ax, (55, 46), (83.5, 40), rad=-0.12)
    arrow(ax, (16.5, 18), (16.5, 15), style="-|>")
    arrow(ax, (83.5, 18), (50, 15), rad=0.1)
    arrow(ax, (83, 46), (83.5, 15), rad=-0.45, ls="--", color="#7a8896")
    save(fig, "class.png")


# -------------------------------------------------------------------- 6. STORAGE
def storage():
    fig, ax = new_axes(9.2, 5.2, (0, 100), (0, 56))
    ax.text(50, 53, "Storage Design - file-based report schema (ER-style)",
            ha="center", fontsize=11.5, weight="bold", color=INK)

    def entity(x, y, w, h, title, fields, color=BLUE):
        box(ax, x, y, w, h, "", color, radius=0.02)
        ax.text(x + w / 2, y + h - 2.2, title, ha="center", fontsize=8.4, weight="bold")
        ax.plot([x, x + w], [y + h - 3.8, y + h - 3.8], color=INK, lw=1.0)
        ax.text(x + 1.4, y + h - 5.0, fields, ha="left", va="top", fontsize=6.7,
                linespacing=1.6)

    entity(3, 20, 27, 26, "RUN  (report.json)",
        "PK run_file: path\n   timestamp\n   config: ScanConfig\n   summary: Summary\n"
        "   pages: Page[ ]", GREEN)
    entity(37, 20, 28, 26, "PAGE  (record)",
        "PK source: filename\n   output: filename\n   status: ok | failed\n"
        "   method / confidence\n   grade / sharpness\n   contrast / skew_deg\n"
        "   width / height / elapsed_ms")
    entity(72, 30, 25, 16, "SUMMARY",
        "   total_images\n   processed / failed\n   success_rate\n   grades{}\n"
        "   mean_confidence", PURPLE)
    entity(72, 5, 25, 20, "ARTEFACT (disk)",
        "PK path\n   kind: scanned |\n         detected |\n         comparison | pdf\n"
        "FK source", AMBER)

    arrow(ax, (30, 33), (37, 33), style="-"); label(ax, 33.5, 35, "1 : N", fs=6.8)
    arrow(ax, (65, 38), (72, 38), style="-"); label(ax, 68.5, 40, "N : 1", fs=6.8)
    arrow(ax, (65, 24), (72, 17), style="-", rad=-0.12); label(ax, 68.5, 23, "1 : N", fs=6.8)
    label(ax, 50, 2, "No RDBMS is used: a run is one JSON document plus a flat CSV mirror, "
                     "which keeps the tool portable and dependency-free.",
          fs=7.2, style="italic", color="#5a6b7b")
    save(fig, "storage.png")


if __name__ == "__main__":
    architecture(); workflow(); usecase(); sequence(); klass(); storage()
