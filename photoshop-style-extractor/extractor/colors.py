from PIL import Image


def rgb_to_hex(rgb: tuple[int, int, int]) -> str:
    r, g, b = rgb
    return "#{:02X}{:02X}{:02X}".format(int(r), int(g), int(b))


def dominant_colors(
    image: Image.Image,
    top_n: int = 3,
    min_ratio: float = 0.05,
    max_palette: int = 16,
) -> list[str]:
    """Colores hex dominantes de una imagen, ignorando píxeles transparentes.

    Reduce la imagen a una paleta de como mucho ``max_palette`` colores y
    devuelve hasta ``top_n`` ordenados por frecuencia, descartando los que
    ocupen menos de ``min_ratio`` de los píxeles opacos.
    """
    if image.mode != "RGBA":
        image = image.convert("RGBA")

    # Máscara de opacidad: recolectar solo píxeles con alpha > 0
    rgb = image.convert("RGB")
    alpha = image.getchannel("A")
    opaque_pixels = [
        rgb.getpixel((x, y))
        for y in range(image.height)
        for x in range(image.width)
        if alpha.getpixel((x, y)) > 0
    ]
    if not opaque_pixels:
        return []

    # Construir una imagen 1-D solo con los píxeles opacos y cuantizar
    flat = Image.new("RGB", (len(opaque_pixels), 1))
    flat.putdata(opaque_pixels)
    quantized = flat.quantize(colors=max_palette)
    palette = quantized.getpalette()  # [r,g,b, r,g,b, ...]
    counts = quantized.getcolors()    # list[(count, palette_index)]
    if not counts:
        return []

    total = sum(c for c, _ in counts)
    counts.sort(reverse=True)  # más frecuente primero
    result: list[str] = []
    for count, idx in counts:
        if count / total < min_ratio:
            continue
        base = idx * 3
        rgb_tuple = (palette[base], palette[base + 1], palette[base + 2])
        result.append(rgb_to_hex(rgb_tuple))
        if len(result) >= top_n:
            break
    return result
