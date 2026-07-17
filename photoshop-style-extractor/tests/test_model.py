from extractor.model import TextInfo, LayerRecord, PSDRecord, BrandStyle, GlobalStyle


def test_layer_record_holds_text_and_defaults():
    txt = TextInfo(text="OFERTA", fonts=["Montserrat-Bold"], sizes_px=[72.0], colors=["#FF0000"])
    layer = LayerRecord(
        name="titulo",
        kind="type",
        visible=True,
        opacity=255,
        blend_mode="normal",
        bbox=(0, 0, 100, 50),
        depth=0,
        effects=["dropshadow"],
        colors=["#FF0000"],
        text=txt,
    )
    assert layer.text.text == "OFERTA"
    assert layer.effects == ["dropshadow"]


def test_psd_record_error_field_optional():
    rec = PSDRecord(
        path="a.psd", brand="marca-x", width=1080, height=1080,
        color_mode="RGB", layers=[], preview_path=None, error=None,
    )
    assert rec.error is None
    assert rec.brand == "marca-x"


def test_brand_and_global_style_shapes():
    brand = BrandStyle(
        brand="marca-x", piece_count=3,
        fonts=[("Montserrat-Bold", 5)], colors=[("#FF0000", 8)],
        canvas_sizes=[((1080, 1080), 3)], effects=[("dropshadow", 4)],
        layer_names=[("titulo", 3)],
    )
    glob = GlobalStyle(
        brands=["marca-x"], psd_count=3,
        fonts=[("Montserrat-Bold", 5)], colors=[("#FF0000", 8)],
        canvas_sizes=[((1080, 1080), 3)], effects=[("dropshadow", 4)],
    )
    assert brand.fonts[0][1] == 5
    assert glob.brands == ["marca-x"]
