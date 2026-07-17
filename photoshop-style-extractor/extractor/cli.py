import argparse
import os
from extractor.discover import discover_psds
from extractor.reader import read_psd
from extractor.aggregate import aggregate, list_fonts, list_unreadable
from extractor.render import (
    render_style_guide, render_brand, render_recipe, render_report,
)


def _write(path: str, content: str) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(content)


def _safe_name(brand: str) -> str:
    keep = "-_ áéíóúñÁÉÍÓÚÑ"
    cleaned = "".join(c for c in brand if c.isalnum() or c in keep).strip()
    return cleaned or "sin-marca"


def run_extraction(input_dir: str, output_dir: str) -> dict:
    references_dir = os.path.join(output_dir, "references")
    pairs = discover_psds(input_dir)
    records = [read_psd(path, brand, preview_dir=references_dir) for path, brand in pairs]

    glob, brand_styles = aggregate(records)
    fonts = list_fonts(records)
    unreadable = list_unreadable(records)

    _write(os.path.join(output_dir, "style-guide.md"), render_style_guide(glob))
    for brand in brand_styles:
        name = _safe_name(brand.brand)
        _write(os.path.join(output_dir, "brands", f"{name}.md"), render_brand(brand))
        _write(os.path.join(output_dir, "recipes", f"{name}.md"), render_recipe(brand))
    _write(os.path.join(output_dir, "report.md"),
           render_report(fonts, unreadable, glob.psd_count))

    return {
        "psd_count": glob.psd_count,
        "brands": glob.brands,
        "unreadable": unreadable,
        "output_dir": output_dir,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Extractor de estilo: analiza PSDs y genera la capa de estilo.")
    parser.add_argument("--input", required=True, help="Carpeta con los .psd")
    parser.add_argument("--output", required=True, help="Carpeta de salida de la capa de estilo")
    args = parser.parse_args(argv)
    summary = run_extraction(args.input, args.output)
    print(f"OK: {summary['psd_count']} PSDs analizados.")
    print(f"Marcas: {', '.join(summary['brands']) or '(ninguna)'}")
    print(f"No legibles: {len(summary['unreadable'])}")
    print(f"Salida en: {summary['output_dir']}")
    return 0
