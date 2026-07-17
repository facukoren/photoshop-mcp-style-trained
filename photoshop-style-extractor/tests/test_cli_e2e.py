import os
from PIL import Image
from psd_tools import PSDImage
from extractor.cli import run_extraction


def _make_psd(path, color=(120, 200, 80)):
    PSDImage.frompil(Image.new("RGB", (80, 60), color)).save(path)


def test_end_to_end_generates_style_layer(tmp_path):
    inp = tmp_path / "psds"
    (inp / "Roma").mkdir(parents=True)
    _make_psd(str(inp / "Roma" / "post1.psd"), (200, 30, 40))
    _make_psd(str(inp / "Roma" / "post2.psd"), (200, 30, 40))
    (inp / "suelto.psd").write_bytes(b"no es psd")  # ilegible

    out = tmp_path / "style-layer"
    summary = run_extraction(str(inp), str(out))

    assert (out / "style-guide.md").exists()
    assert (out / "brands" / "Roma.md").exists()
    assert (out / "recipes" / "Roma.md").exists()
    assert (out / "report.md").exists()
    assert (out / "references" / "post1.jpg").exists()
    assert summary["psd_count"] == 2
    assert len(summary["unreadable"]) == 1
    assert "Roma" in summary["brands"]
    # El reporte menciona el PSD ilegible
    report = (out / "report.md").read_text(encoding="utf-8")
    assert "suelto.psd" in report
