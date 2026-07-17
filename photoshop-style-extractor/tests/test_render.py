from extractor.model import GlobalStyle, BrandStyle
from extractor.render import (
    render_style_guide, render_brand, render_recipe, render_report,
)


def _brand():
    return BrandStyle(
        brand="roma", piece_count=3,
        fonts=[("Montserrat-Bold", 5)], colors=[("#FF0000", 8), ("#FFFFFF", 6)],
        canvas_sizes=[((1080, 1080), 3)], effects=[("dropshadoweffect", 4)],
        layer_names=[("titulo", 3), ("logo", 3)], text_bands=[("arriba", 3)],
    )


def test_style_guide_has_fonts_and_colors():
    glob = GlobalStyle(
        brands=["roma"], psd_count=3,
        fonts=[("Montserrat-Bold", 5)], colors=[("#FF0000", 8)],
        canvas_sizes=[((1080, 1080), 3)], effects=[("dropshadoweffect", 4)],
    )
    md = render_style_guide(glob)
    assert "Montserrat-Bold" in md
    assert "#FF0000" in md
    assert "1080" in md
    assert "Corregí" in md


def test_brand_md_has_name_and_palette():
    md = render_brand(_brand())
    assert "roma" in md
    assert "#FF0000" in md
    assert "titulo" in md
    assert "arriba" in md  # sección de composición


def test_recipe_scaffold_mentions_canvas_and_layers():
    md = render_recipe(_brand())
    assert "1080" in md
    assert "titulo" in md
    assert "punto de partida" in md.lower()


def test_report_lists_fonts_and_unreadable():
    md = render_report(
        fonts=["Arial", "Montserrat-Bold"],
        unreadable=[("c:/x/roto.psd", "ValueError: boom")],
        psd_count=10,
    )
    assert "Arial" in md
    assert "Montserrat-Bold" in md
    assert "roto.psd" in md
    assert "10" in md
