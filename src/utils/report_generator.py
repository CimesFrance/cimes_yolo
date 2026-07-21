"""Génération de rapports PDF pour l'application CIMES."""

import json
import os

import matplotlib

matplotlib.use("Agg")  # Doit être appelé avant l'import de pyplot

import matplotlib.pyplot as plt  # pylint: disable=wrong-import-position
from reportlab.lib import colors  # pylint: disable=wrong-import-position
from reportlab.lib.pagesizes import A4  # pylint: disable=wrong-import-position
from reportlab.lib.styles import (  # pylint: disable=wrong-import-position
    getSampleStyleSheet,
    ParagraphStyle,
)
from reportlab.lib.units import inch  # pylint: disable=wrong-import-position
from reportlab.platypus import (  # pylint: disable=wrong-import-position
    Image,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)


def _build_granulo_curve(data: dict, options: dict, curve_path: str) -> None:
    """Génère et sauvegarde la courbe granulométrique dans `curve_path`."""
    plt.figure(figsize=(6, 4))
    plt.plot(data["tamis_exp"], data["cumulative_raw"], marker="o", label="Brute")
    if options.get("dna_correction_enabled") and "cumulative_corrected" in data:
        plt.plot(
            data["tamis_exp"],
            data["cumulative_corrected"],
            marker="s",
            label="Corrigée",
        )
    plt.title("Courbe Granulométrique")
    plt.xlabel("Taille des mailles (mm)")
    plt.ylabel("Passant cumulé (%)")
    plt.grid(True)
    plt.legend()
    plt.tight_layout()
    plt.savefig(curve_path)
    plt.close()


def _build_stats_table(stats: dict) -> Table:
    """Construit et retourne le tableau ReportLab des statistiques."""
    table_data = [
        ["Métrique", "Petit Axe (mm)", "Grand Axe (mm)"],
        [
            "Minimum",
            f"{stats.get('min_mm_minor', 0):.2f}",
            f"{stats.get('min_mm_major', 0):.2f}",
        ],
        [
            "Maximum",
            f"{stats.get('max_mm_minor', 0):.2f}",
            f"{stats.get('max_mm_major', 0):.2f}",
        ],
        [
            "Moyenne",
            f"{stats.get('moyenne_mm_minor', 0):.2f}",
            f"{stats.get('moyenne_mm_major', 0):.2f}",
        ],
        [
            "Médiane",
            f"{stats.get('mediane_mm_minor', 0):.2f}",
            f"{stats.get('mediane_mm_major', 0):.2f}",
        ],
        [
            "D10",
            f"{stats.get('d10_minor', 0):.2f}",
            f"{stats.get('d10_major', 0):.2f}",
        ],
        [
            "D50",
            f"{stats.get('d50_minor', 0):.2f}",
            f"{stats.get('d50_major', 0):.2f}",
        ],
        [
            "D90",
            f"{stats.get('d90_minor', 0):.2f}",
            f"{stats.get('d90_major', 0):.2f}",
        ],
    ]
    table = Table(table_data, colWidths=[2 * inch, 2 * inch, 2 * inch])
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#374151")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("BOTTOMPADDING", (0, 0), (-1, 0), 12),
                ("BACKGROUND", (0, 1), (-1, -1), colors.HexColor("#f3f4f6")),
                ("GRID", (0, 0), (-1, -1), 1, colors.black),
            ]
        )
    )
    return table


def generate_pdf_report(capture_dir, app):  # pylint: disable=too-many-locals,too-many-branches,too-many-statements
    """Génère un rapport PDF basé sur les options configurées par l'utilisateur.

    Le PDF est sauvegardé dans `capture_dir` sous le nom "Rapport.pdf".

    Returns:
        Le chemin absolu du fichier PDF généré, ou None en cas d'échec.
    """
    pdf_path = os.path.join(capture_dir, "Rapport.pdf")

    options = {
        "include_captured_image": app.report_options["include_captured_image"].get(),
        "include_segmented_image": app.report_options["include_segmented_image"].get(),
        "include_granulometric_curve": app.report_options["include_granulometric_curve"].get(),
        "include_distribution_curve": app.report_options["include_distribution_curve"].get(),
        "include_statistics": app.report_options["include_statistics"].get(),
        "custom_comment": app.report_options["custom_comment"].get(),
        "dna_correction_enabled": app.show_corrected_curve_var.get(),
    }

    data_path = os.path.join(capture_dir, "data.json")
    if not os.path.exists(data_path):
        return None
    with open(data_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    stats_path = os.path.join(capture_dir, "statistiques.json")
    stats = None
    if os.path.exists(stats_path):
        with open(stats_path, "r", encoding="utf-8") as f:
            stats = json.load(f)

    doc = SimpleDocTemplate(
        pdf_path,
        pagesize=A4,
        rightMargin=50,
        leftMargin=50,
        topMargin=50,
        bottomMargin=50,
    )
    story = []
    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        "TitleStyle",
        parent=styles["Heading1"],
        fontSize=18,
        textColor=colors.HexColor("#1f2937"),
        spaceAfter=20,
        alignment=1,
    )

    story.append(
        Paragraph(
            f"Rapport de Granulométrie - Capture #{data.get('id', '?')}",
            title_style,
        )
    )
    story.append(
        Paragraph(f"<b>Date et Heure :</b> {data.get('timestamp', '')}", styles["Normal"])
    )
    if options.get("custom_comment"):
        story.append(Spacer(1, 10))
        story.append(Paragraph("<b>Commentaire :</b>", styles["Normal"]))
        story.append(Paragraph(options["custom_comment"], styles["Normal"]))
    story.append(Spacer(1, 20))

    raw_img_path = os.path.join(capture_dir, "raw.png")
    seg_img_path = os.path.join(capture_dir, "segmented.png")

    if options.get("include_captured_image") and os.path.exists(raw_img_path):
        story.append(Paragraph("<b>Image Capturée</b>", styles["Heading2"]))
        story.append(Image(raw_img_path, width=4 * inch, height=3 * inch))
        story.append(Spacer(1, 15))

    if options.get("include_segmented_image") and os.path.exists(seg_img_path):
        story.append(Paragraph("<b>Image Segmentée</b>", styles["Heading2"]))
        story.append(Image(seg_img_path, width=4 * inch, height=3 * inch))
        story.append(Spacer(1, 15))

    curve_path = os.path.join(capture_dir, "temp_granulo.png")
    if (
        options.get("include_granulometric_curve")
        and "tamis_exp" in data
        and "cumulative_raw" in data
    ):
        _build_granulo_curve(data, options, curve_path)
        story.append(Paragraph("<b>Courbe Granulométrique</b>", styles["Heading2"]))
        story.append(Image(curve_path, width=5 * inch, height=3.3 * inch))
        story.append(Spacer(1, 15))

    if options.get("include_statistics") and stats:
        story.append(Paragraph("<b>Statistiques</b>", styles["Heading2"]))
        story.append(_build_stats_table(stats))

    try:
        doc.build(story)
    except OSError as e:
        print(f"[REPORT] Échec de la génération du document PDF : {e}")
        if os.path.exists(curve_path):
            try:
                os.remove(curve_path)
            except OSError:
                pass
        raise RuntimeError(
            f"Erreur d'écriture du fichier PDF (vérifiez qu'il n'est pas déjà ouvert) : {e}"
        ) from e

    if os.path.exists(curve_path):
        try:
            os.remove(curve_path)
        except OSError:
            pass

    return pdf_path
