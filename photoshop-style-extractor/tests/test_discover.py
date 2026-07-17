from extractor.discover import discover_psds


def test_brand_from_subfolder_and_root(tmp_path):
    (tmp_path / "PizzeriaRoma").mkdir()
    (tmp_path / "PizzeriaRoma" / "post1.psd").write_bytes(b"x")
    (tmp_path / "suelto.psd").write_bytes(b"x")
    (tmp_path / "notas.txt").write_text("ignorar")

    result = discover_psds(str(tmp_path))
    brands = {path.split("/")[-1].split("\\")[-1]: brand for path, brand in result}
    assert brands["post1.psd"] == "PizzeriaRoma"
    assert brands["suelto.psd"] == "sin-marca"
    assert all(p.lower().endswith(".psd") for p, _ in result)
    assert len(result) == 2


def test_case_insensitive_extension(tmp_path):
    (tmp_path / "A.PSD").write_bytes(b"x")
    result = discover_psds(str(tmp_path))
    assert len(result) == 1


def test_stable_alphabetical_order(tmp_path):
    (tmp_path / "b.psd").write_bytes(b"x")
    (tmp_path / "a.psd").write_bytes(b"x")
    result = discover_psds(str(tmp_path))
    names = [p.split("\\")[-1].split("/")[-1] for p, _ in result]
    assert names == ["a.psd", "b.psd"]
