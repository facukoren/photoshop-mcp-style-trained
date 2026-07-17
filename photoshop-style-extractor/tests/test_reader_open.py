import os
from PIL import Image
from psd_tools import PSDImage
from extractor.reader import read_psd
from extractor.preview import save_preview


def _make_psd(path):
    img = Image.new("RGB", (80, 60), (120, 200, 80))
    PSDImage.frompil(img).save(path)


def test_read_psd_ok(tmp_path):
    psd_path = tmp_path / "pieza.psd"
    _make_psd(str(psd_path))
    rec = read_psd(str(psd_path), brand="marca-x")
    assert rec.error is None
    assert rec.width == 80 and rec.height == 60
    assert rec.brand == "marca-x"


def test_read_psd_corrupt_sets_error(tmp_path):
    bad = tmp_path / "roto.psd"
    bad.write_bytes(b"esto no es un psd")
    rec = read_psd(str(bad), brand="marca-x")
    assert rec.error is not None
    assert rec.layers == []


def test_save_preview_creates_jpg(tmp_path):
    psd_path = tmp_path / "pieza.psd"
    _make_psd(str(psd_path))
    psd = PSDImage.open(str(psd_path))
    out = tmp_path / "prev.jpg"
    result = save_preview(psd, str(out))
    assert result == str(out)
    assert out.exists()
    with Image.open(str(out)) as im:
        assert max(im.size) <= 1200
