from extractor.model import PSDRecord, LayerRecord, TextInfo
from extractor.aggregate import aggregate, list_fonts, list_unreadable


def _text_layer(name, font, color):
    return LayerRecord(
        name=name, kind="type", visible=True, opacity=255, blend_mode="normal",
        bbox=(0, 0, 10, 10), depth=0, effects=["dropshadoweffect"], colors=[color],
        text=TextInfo(text="x", fonts=[font], sizes_px=[], colors=[color]),
    )


def _psd(path, brand, layers, w=1080, h=1080, error=None):
    return PSDRecord(path=path, brand=brand, width=w, height=h, color_mode="RGB",
                     layers=layers, preview_path=None, error=error)


def test_aggregate_counts_by_brand_and_global():
    records = [
        _psd("a.psd", "roma", [_text_layer("titulo", "Montserrat-Bold", "#FF0000")]),
        _psd("b.psd", "roma", [_text_layer("titulo", "Montserrat-Bold", "#FF0000")]),
        _psd("c.psd", "lima", [_text_layer("titulo", "Poppins-Regular", "#00FF00")]),
    ]
    glob, brands = aggregate(records)
    assert glob.psd_count == 3
    assert set(glob.brands) == {"roma", "lima"}
    assert glob.fonts[0] == ("Montserrat-Bold", 2)
    roma = next(b for b in brands if b.brand == "roma")
    assert roma.piece_count == 2
    assert roma.colors[0] == ("#FF0000", 2)
    assert roma.effects[0] == ("dropshadoweffect", 2)
    assert roma.layer_names[0] == ("titulo", 2)
    # bbox (0,0,10,10) sobre lienzo 1080 → banda "arriba"
    assert roma.text_bands == [("arriba", 2)]


def test_aggregate_ignores_unreadable():
    records = [
        _psd("ok.psd", "roma", [_text_layer("t", "Arial", "#000000")]),
        _psd("bad.psd", "roma", [], error="boom"),
    ]
    glob, brands = aggregate(records)
    assert glob.psd_count == 1
    assert next(b for b in brands if b.brand == "roma").piece_count == 1


def test_list_fonts_unique_sorted():
    records = [
        _psd("a.psd", "roma", [_text_layer("t", "Poppins", "#000000")]),
        _psd("b.psd", "roma", [_text_layer("t", "Arial", "#000000")]),
        _psd("c.psd", "roma", [_text_layer("t", "Arial", "#000000")]),
    ]
    assert list_fonts(records) == ["Arial", "Poppins"]


def test_list_unreadable():
    records = [_psd("bad.psd", "roma", [], error="X: y")]
    assert list_unreadable(records) == [("bad.psd", "X: y")]
