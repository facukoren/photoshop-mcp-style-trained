from PIL import Image
from extractor.colors import dominant_colors, rgb_to_hex


def test_rgb_to_hex_uppercase():
    assert rgb_to_hex((255, 0, 0)) == "#FF0000"
    assert rgb_to_hex((18, 52, 86)) == "#123456"


def test_solid_image_returns_its_color():
    img = Image.new("RGB", (20, 20), (200, 30, 40))
    assert dominant_colors(img, top_n=1) == ["#C81E28"]


def test_transparent_pixels_are_ignored():
    # Mitad roja opaca, mitad totalmente transparente
    img = Image.new("RGBA", (20, 20), (0, 0, 0, 0))
    for x in range(10):
        for y in range(20):
            img.putpixel((x, y), (200, 30, 40, 255))
    assert dominant_colors(img, top_n=1) == ["#C81E28"]


def test_fully_transparent_image_returns_empty():
    img = Image.new("RGBA", (20, 20), (0, 0, 0, 0))
    assert dominant_colors(img) == []


def test_minor_colors_filtered_by_min_ratio():
    # 99% azul, 1% verde: con min_ratio 0.05 el verde se descarta
    img = Image.new("RGB", (10, 10), (0, 0, 255))
    img.putpixel((0, 0), (0, 255, 0))
    result = dominant_colors(img, top_n=5, min_ratio=0.05)
    assert result == ["#0000FF"]
