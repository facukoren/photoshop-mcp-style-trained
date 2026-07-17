# Extractor de Estilo (Fase 1) — Plan de Implementación

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Construir un extractor en Python que lea 20+ archivos PSD y genere una "capa de estilo" corregible (style-guide.md global, brands/*.md por marca, recipes/*.md, references/*.jpg) más un reporte de fuentes a verificar y PSDs no legibles.

**Architecture:** Un pipeline de una sola pasada: `reader` abre cada PSD de forma tolerante a fallos y produce un `PSDRecord` (recorriendo el árbol de capas); `aggregate` combina los records en estadísticas de frecuencia globales y por marca; `render` escribe los archivos markdown y el reporte; `cli` orquesta apuntando a una carpeta de entrada. El color se extrae componiendo píxeles con Pillow (robusto), no parseando el motor de texto. Las fuentes se extraen con la API confiable `layer.font_names`.

**Tech Stack:** Python 3.14, psd-tools 1.17.4, Pillow 12.3, pytest. Windows (sin Photoshop requerido).

## Global Constraints

- Python 3.14.x; dependencias: `psd-tools>=1.17,<2`, `Pillow>=12,<13`, `pytest`. Nada más.
- El extractor NUNCA modifica los PSD de entrada — solo los abre en modo lectura.
- Tolerancia a fallos: un PSD ilegible se saltea y se reporta; nunca frena el proceso.
- Salida en español (los .md los lee y corrige Facu, diseñador no técnico).
- Convención de marca: la marca de un PSD es el nombre de su carpeta padre inmediata dentro de la carpeta de entrada; si el PSD está suelto en la raíz, marca = `"sin-marca"`.
- Colores en formato hex `#RRGGBB` en mayúsculas.
- Todo el código y los nombres de símbolos en inglés; el texto de salida para el usuario en español.
- Estructura del paquete bajo `photoshop-style-extractor/`.

---

### Task 1: Scaffolding del proyecto y modelo de datos

**Files:**
- Create: `photoshop-style-extractor/requirements.txt`
- Create: `photoshop-style-extractor/extractor/__init__.py`
- Create: `photoshop-style-extractor/extractor/model.py`
- Create: `photoshop-style-extractor/tests/__init__.py`
- Test: `photoshop-style-extractor/tests/test_model.py`

**Interfaces:**
- Consumes: nada (primera tarea).
- Produces: las dataclasses que usan todas las tareas siguientes:
  - `TextInfo(text: str, fonts: list[str], sizes_px: list[float], colors: list[str])`
  - `LayerRecord(name: str, kind: str, visible: bool, opacity: int, blend_mode: str, bbox: tuple[int,int,int,int], depth: int, effects: list[str], colors: list[str], text: TextInfo | None)`
  - `PSDRecord(path: str, brand: str, width: int, height: int, color_mode: str, layers: list[LayerRecord], preview_path: str | None, error: str | None)`
  - `BrandStyle(brand: str, piece_count: int, fonts: list[tuple[str,int]], colors: list[tuple[str,int]], canvas_sizes: list[tuple[tuple[int,int],int]], effects: list[tuple[str,int]], layer_names: list[tuple[str,int]], text_bands: list[tuple[str,int]])` — `text_bands` cuenta la banda vertical (`"arriba"`/`"centro"`/`"abajo"`) donde caen las capas de texto, cubriendo el patrón de composición del spec.
  - `GlobalStyle(brands: list[str], psd_count: int, fonts: list[tuple[str,int]], colors: list[tuple[str,int]], canvas_sizes: list[tuple[tuple[int,int],int]], effects: list[tuple[str,int]])`

- [ ] **Step 1: Escribir el test que falla**

```python
# photoshop-style-extractor/tests/test_model.py
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
```

- [ ] **Step 2: Correr el test para verificar que falla**

Run: `cd photoshop-style-extractor && python -m pytest tests/test_model.py -v`
Expected: FAIL con `ModuleNotFoundError: No module named 'extractor'`

- [ ] **Step 3: Escribir requirements y el modelo**

```
# photoshop-style-extractor/requirements.txt
psd-tools>=1.17,<2
Pillow>=12,<13
pytest
```

```python
# photoshop-style-extractor/extractor/__init__.py
```

```python
# photoshop-style-extractor/extractor/model.py
from dataclasses import dataclass, field


@dataclass
class TextInfo:
    text: str
    fonts: list[str] = field(default_factory=list)
    sizes_px: list[float] = field(default_factory=list)
    colors: list[str] = field(default_factory=list)


@dataclass
class LayerRecord:
    name: str
    kind: str
    visible: bool
    opacity: int
    blend_mode: str
    bbox: tuple[int, int, int, int]
    depth: int
    effects: list[str] = field(default_factory=list)
    colors: list[str] = field(default_factory=list)
    text: TextInfo | None = None


@dataclass
class PSDRecord:
    path: str
    brand: str
    width: int
    height: int
    color_mode: str
    layers: list[LayerRecord] = field(default_factory=list)
    preview_path: str | None = None
    error: str | None = None


@dataclass
class BrandStyle:
    brand: str
    piece_count: int
    fonts: list[tuple[str, int]] = field(default_factory=list)
    colors: list[tuple[str, int]] = field(default_factory=list)
    canvas_sizes: list[tuple[tuple[int, int], int]] = field(default_factory=list)
    effects: list[tuple[str, int]] = field(default_factory=list)
    layer_names: list[tuple[str, int]] = field(default_factory=list)
    text_bands: list[tuple[str, int]] = field(default_factory=list)


@dataclass
class GlobalStyle:
    brands: list[str]
    psd_count: int
    fonts: list[tuple[str, int]] = field(default_factory=list)
    colors: list[tuple[str, int]] = field(default_factory=list)
    canvas_sizes: list[tuple[tuple[int, int], int]] = field(default_factory=list)
    effects: list[tuple[str, int]] = field(default_factory=list)
```

Create empty file `photoshop-style-extractor/tests/__init__.py`.

- [ ] **Step 4: Correr el test para verificar que pasa**

Run: `cd photoshop-style-extractor && python -m pytest tests/test_model.py -v`
Expected: PASS (3 passed)

- [ ] **Step 5: Commit**

```bash
git add photoshop-style-extractor/requirements.txt photoshop-style-extractor/extractor/ photoshop-style-extractor/tests/
git commit -m "feat: scaffolding y modelo de datos del extractor de estilo"
```

---

### Task 2: Extracción de colores dominantes por composición de píxeles

**Files:**
- Create: `photoshop-style-extractor/extractor/colors.py`
- Test: `photoshop-style-extractor/tests/test_colors.py`

**Interfaces:**
- Consumes: nada del proyecto (usa solo Pillow).
- Produces:
  - `dominant_colors(image, top_n: int = 3, min_ratio: float = 0.05, max_palette: int = 16) -> list[str]` — recibe un `PIL.Image.Image`, devuelve hasta `top_n` colores hex `#RRGGBB` ordenados por frecuencia, ignorando píxeles totalmente transparentes y descartando colores que ocupen menos de `min_ratio` del total de píxeles opacos.
  - `rgb_to_hex(rgb: tuple[int, int, int]) -> str`

- [ ] **Step 1: Escribir el test que falla**

```python
# photoshop-style-extractor/tests/test_colors.py
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
```

- [ ] **Step 2: Correr el test para verificar que falla**

Run: `cd photoshop-style-extractor && python -m pytest tests/test_colors.py -v`
Expected: FAIL con `ModuleNotFoundError: No module named 'extractor.colors'`

- [ ] **Step 3: Implementar colors.py**

```python
# photoshop-style-extractor/extractor/colors.py
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
```

- [ ] **Step 4: Correr el test para verificar que pasa**

Run: `cd photoshop-style-extractor && python -m pytest tests/test_colors.py -v`
Expected: PASS (5 passed)

- [ ] **Step 5: Commit**

```bash
git add photoshop-style-extractor/extractor/colors.py photoshop-style-extractor/tests/test_colors.py
git commit -m "feat: extraccion de colores dominantes por composicion de pixeles"
```

---

### Task 3: Recorrido del árbol de capas (función pura, testeable con fakes)

**Files:**
- Create: `photoshop-style-extractor/extractor/reader.py`
- Test: `photoshop-style-extractor/tests/test_reader_walk.py`

**Interfaces:**
- Consumes: `LayerRecord`, `TextInfo` (Task 1); `dominant_colors` (Task 2).
- Produces:
  - `layer_to_record(layer, depth: int) -> LayerRecord` — convierte un objeto capa de psd-tools (o un fake con la misma interfaz) en `LayerRecord`. Lee `.name`, `.kind`, `.visible`, `.opacity`, `.blend_mode.name`, `.bbox`, `.has_effects`/`.effects`, y si `.kind == "type"` extrae `TextInfo` con `.text` y `.font_names`. Colores vía `dominant_colors(layer.composite())`.
  - `walk_layers(layers, depth: int = 0) -> list[LayerRecord]` — recorre recursivamente; para grupos (`.is_group` True) emite el `LayerRecord` del grupo y luego desciende a los hijos con `depth+1`. Cualquier excepción al procesar UNA capa se captura: se emite un `LayerRecord` con `kind="error"` y el nombre de la capa, sin frenar el recorrido.

- [ ] **Step 1: Escribir el test que falla**

```python
# photoshop-style-extractor/tests/test_reader_walk.py
from PIL import Image
from extractor.reader import walk_layers, layer_to_record


class FakeBlend:
    def __init__(self, name):
        self.name = name


class FakeLayer:
    """Duck-type de una capa de psd-tools para tests."""
    def __init__(self, name, kind="pixel", children=None, text=None,
                 fonts=None, effects=None, color=(10, 20, 30)):
        self.name = name
        self.kind = kind
        self.visible = True
        self.opacity = 255
        self.blend_mode = FakeBlend("normal")
        self.bbox = (0, 0, 10, 10)
        self.is_group = children is not None
        self._children = children or []
        self.has_effects = bool(effects)
        self._effects = effects or []
        self._text = text
        self.font_names = fonts or []
        self._color = color

    def __iter__(self):
        return iter(self._children)

    @property
    def effects(self):
        return self._effects

    @property
    def text(self):
        return self._text

    def composite(self):
        return Image.new("RGB", (10, 10), self._color)


def test_single_pixel_layer_record():
    layer = FakeLayer("fondo", kind="pixel", color=(200, 30, 40))
    rec = layer_to_record(layer, depth=0)
    assert rec.name == "fondo"
    assert rec.kind == "pixel"
    assert rec.blend_mode == "normal"
    assert rec.colors == ["#C81E28"]
    assert rec.text is None


def test_type_layer_extracts_text_and_fonts():
    layer = FakeLayer("titulo", kind="type", text="OFERTA",
                      fonts=["Montserrat-Bold"], color=(255, 0, 0))
    rec = layer_to_record(layer, depth=1)
    assert rec.text is not None
    assert rec.text.text == "OFERTA"
    assert rec.text.fonts == ["Montserrat-Bold"]
    assert rec.depth == 1


def test_walk_descends_into_groups_with_depth():
    child = FakeLayer("hijo", kind="pixel")
    group = FakeLayer("grupo", kind="group", children=[child])
    records = walk_layers([group])
    assert [r.name for r in records] == ["grupo", "hijo"]
    assert records[0].depth == 0
    assert records[1].depth == 1


def test_walk_captures_error_on_bad_layer():
    # `kind` como property que revienta: layer_to_record no lo captura
    # (solo protege la extracción de color), así que walk_layers debe
    # atrapar la excepción y emitir un registro kind="error".
    class Broken:
        name = "rota"
        is_group = False

        @property
        def kind(self):
            raise ValueError("boom")

    records = walk_layers([Broken()])
    assert len(records) == 1
    assert records[0].kind == "error"
    assert records[0].name == "rota"
```

- [ ] **Step 2: Correr el test para verificar que falla**

Run: `cd photoshop-style-extractor && python -m pytest tests/test_reader_walk.py -v`
Expected: FAIL con `ModuleNotFoundError: No module named 'extractor.reader'`

- [ ] **Step 3: Implementar reader.py (parte de recorrido)**

```python
# photoshop-style-extractor/extractor/reader.py
from extractor.model import LayerRecord, TextInfo
from extractor.colors import dominant_colors


def _effect_names(layer) -> list[str]:
    if not getattr(layer, "has_effects", False):
        return []
    names: list[str] = []
    try:
        for effect in layer.effects:
            names.append(type(effect).__name__.lower())
    except Exception:
        pass
    return names


def _text_info(layer) -> TextInfo | None:
    if getattr(layer, "kind", None) != "type":
        return None
    try:
        text_value = layer.text or ""
    except Exception:
        text_value = ""
    fonts = list(getattr(layer, "font_names", []) or [])
    return TextInfo(text=text_value, fonts=fonts, sizes_px=[], colors=[])


def layer_to_record(layer, depth: int) -> LayerRecord:
    try:
        colors = dominant_colors(layer.composite())
    except Exception:
        colors = []
    text = _text_info(layer)
    if text is not None:
        text.colors = colors
    return LayerRecord(
        name=getattr(layer, "name", "?"),
        kind=getattr(layer, "kind", "unknown"),
        visible=bool(getattr(layer, "visible", True)),
        opacity=int(getattr(layer, "opacity", 255)),
        blend_mode=getattr(getattr(layer, "blend_mode", None), "name", "normal"),
        bbox=tuple(getattr(layer, "bbox", (0, 0, 0, 0))),
        depth=depth,
        effects=_effect_names(layer),
        colors=colors,
        text=text,
    )


def walk_layers(layers, depth: int = 0) -> list[LayerRecord]:
    records: list[LayerRecord] = []
    for layer in layers:
        try:
            record = layer_to_record(layer, depth)
        except Exception as exc:
            records.append(LayerRecord(
                name=getattr(layer, "name", "?"), kind="error", visible=False,
                opacity=0, blend_mode="normal", bbox=(0, 0, 0, 0), depth=depth,
                effects=[], colors=[], text=None,
            ))
            continue
        records.append(record)
        if getattr(layer, "is_group", False):
            records.extend(walk_layers(layer, depth + 1))
    return records
```

- [ ] **Step 4: Correr el test para verificar que pasa**

Run: `cd photoshop-style-extractor && python -m pytest tests/test_reader_walk.py -v`
Expected: PASS (4 passed)

- [ ] **Step 5: Commit**

```bash
git add photoshop-style-extractor/extractor/reader.py photoshop-style-extractor/tests/test_reader_walk.py
git commit -m "feat: recorrido tolerante a fallos del arbol de capas"
```

---

### Task 4: Apertura de PSD y generación de preview

**Files:**
- Modify: `photoshop-style-extractor/extractor/reader.py`
- Create: `photoshop-style-extractor/extractor/preview.py`
- Test: `photoshop-style-extractor/tests/test_reader_open.py`

**Interfaces:**
- Consumes: `PSDRecord` (Task 1); `walk_layers` (Task 3).
- Produces:
  - `save_preview(psd, out_path: str, max_side: int = 1200) -> str | None` (en `preview.py`) — compone el documento entero (`psd.composite()`), lo reescala para que el lado mayor no supere `max_side`, lo guarda como JPG en `out_path` y devuelve la ruta; si falla devuelve `None`.
  - `read_psd(path: str, brand: str, preview_dir: str | None = None) -> PSDRecord` (en `reader.py`) — abre el PSD con `PSDImage.open`; si falla devuelve un `PSDRecord` con `error` seteado y `layers=[]`. Si abre bien, llena width/height/color_mode, recorre capas con `walk_layers`, y si `preview_dir` no es None genera el preview.

- [ ] **Step 1: Escribir el test que falla**

```python
# photoshop-style-extractor/tests/test_reader_open.py
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
```

- [ ] **Step 2: Correr el test para verificar que falla**

Run: `cd photoshop-style-extractor && python -m pytest tests/test_reader_open.py -v`
Expected: FAIL con `ImportError: cannot import name 'read_psd'` / `No module named 'extractor.preview'`

- [ ] **Step 3: Implementar preview.py y read_psd**

```python
# photoshop-style-extractor/extractor/preview.py
from PIL import Image


def save_preview(psd, out_path: str, max_side: int = 1200) -> str | None:
    try:
        image = psd.composite()
        if image is None:
            return None
        if image.mode not in ("RGB", "RGBA"):
            image = image.convert("RGB")
        if image.mode == "RGBA":
            background = Image.new("RGB", image.size, (255, 255, 255))
            background.paste(image, mask=image.getchannel("A"))
            image = background
        longest = max(image.size)
        if longest > max_side:
            scale = max_side / longest
            new_size = (int(image.width * scale), int(image.height * scale))
            image = image.resize(new_size, Image.LANCZOS)
        image.save(out_path, "JPEG", quality=85)
        return out_path
    except Exception:
        return None
```

Agregar a `reader.py` (imports arriba y función nueva):

```python
# añadir al inicio de reader.py
import os
from psd_tools import PSDImage
from extractor.model import PSDRecord
from extractor.preview import save_preview
```

```python
# añadir al final de reader.py
def read_psd(path: str, brand: str, preview_dir: str | None = None) -> PSDRecord:
    try:
        psd = PSDImage.open(path)
    except Exception as exc:
        return PSDRecord(
            path=path, brand=brand, width=0, height=0, color_mode="?",
            layers=[], preview_path=None, error=f"{type(exc).__name__}: {exc}",
        )
    record = PSDRecord(
        path=path, brand=brand,
        width=int(psd.width), height=int(psd.height),
        color_mode=getattr(psd.color_mode, "name", str(psd.color_mode)),
        layers=walk_layers(psd), preview_path=None, error=None,
    )
    if preview_dir is not None:
        os.makedirs(preview_dir, exist_ok=True)
        base = os.path.splitext(os.path.basename(path))[0]
        out = os.path.join(preview_dir, f"{base}.jpg")
        record.preview_path = save_preview(psd, out)
    return record
```

- [ ] **Step 4: Correr el test para verificar que pasa**

Run: `cd photoshop-style-extractor && python -m pytest tests/test_reader_open.py -v`
Expected: PASS (3 passed)

- [ ] **Step 5: Commit**

```bash
git add photoshop-style-extractor/extractor/reader.py photoshop-style-extractor/extractor/preview.py photoshop-style-extractor/tests/test_reader_open.py
git commit -m "feat: apertura tolerante de PSD y generacion de preview JPG"
```

---

### Task 5: Descubrimiento de PSDs y asignación de marca

**Files:**
- Create: `photoshop-style-extractor/extractor/discover.py`
- Test: `photoshop-style-extractor/tests/test_discover.py`

**Interfaces:**
- Consumes: nada del proyecto.
- Produces:
  - `discover_psds(root: str) -> list[tuple[str, str]]` — recorre `root` recursivamente y devuelve `(ruta_absoluta, marca)` para cada `.psd` (case-insensitive). Marca = nombre de la carpeta padre inmediata si esa carpeta NO es `root`; si el PSD está directo en `root`, marca = `"sin-marca"`. Ignora archivos que no terminan en `.psd`. Orden estable (alfabético por ruta).

- [ ] **Step 1: Escribir el test que falla**

```python
# photoshop-style-extractor/tests/test_discover.py
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
```

- [ ] **Step 2: Correr el test para verificar que falla**

Run: `cd photoshop-style-extractor && python -m pytest tests/test_discover.py -v`
Expected: FAIL con `ModuleNotFoundError: No module named 'extractor.discover'`

- [ ] **Step 3: Implementar discover.py**

```python
# photoshop-style-extractor/extractor/discover.py
import os


def discover_psds(root: str) -> list[tuple[str, str]]:
    root = os.path.abspath(root)
    found: list[tuple[str, str]] = []
    for dirpath, _dirnames, filenames in os.walk(root):
        for name in filenames:
            if not name.lower().endswith(".psd"):
                continue
            full = os.path.join(dirpath, name)
            parent = os.path.abspath(dirpath)
            if parent == root:
                brand = "sin-marca"
            else:
                brand = os.path.basename(parent)
            found.append((full, brand))
    found.sort(key=lambda pair: pair[0].lower())
    return found
```

- [ ] **Step 4: Correr el test para verificar que pasa**

Run: `cd photoshop-style-extractor && python -m pytest tests/test_discover.py -v`
Expected: PASS (3 passed)

- [ ] **Step 5: Commit**

```bash
git add photoshop-style-extractor/extractor/discover.py photoshop-style-extractor/tests/test_discover.py
git commit -m "feat: descubrimiento de PSDs y asignacion de marca por carpeta"
```

---

### Task 6: Agregación en estadísticas globales y por marca

**Files:**
- Create: `photoshop-style-extractor/extractor/aggregate.py`
- Test: `photoshop-style-extractor/tests/test_aggregate.py`

**Interfaces:**
- Consumes: `PSDRecord`, `LayerRecord`, `TextInfo`, `BrandStyle`, `GlobalStyle` (Task 1).
- Produces:
  - `aggregate(records: list[PSDRecord]) -> tuple[GlobalStyle, list[BrandStyle]]` — cuenta frecuencias de fuentes (de `layer.text.fonts`), colores (de `layer.colors`), tamaños de lienzo (`(width,height)`), efectos (`layer.effects`) y nombres de capa (`layer.name`, excluyendo `kind in {"error"}`), agrupando por marca y en global. Solo cuenta PSDs sin `error`. Cada lista sale ordenada por frecuencia descendente y, a igualdad, alfabética. `piece_count` por marca = cantidad de PSDs legibles de esa marca. Además calcula `text_bands` por marca (banda vertical arriba/centro/abajo de las capas de texto, ordenada arriba→abajo).
  - `list_fonts(records: list[PSDRecord]) -> list[str]` — lista única y ordenada de todas las fuentes vistas (para el reporte de verificación).
  - `list_unreadable(records: list[PSDRecord]) -> list[tuple[str, str]]` — `(ruta, error)` de los PSDs con `error`.

- [ ] **Step 1: Escribir el test que falla**

```python
# photoshop-style-extractor/tests/test_aggregate.py
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
```

- [ ] **Step 2: Correr el test para verificar que falla**

Run: `cd photoshop-style-extractor && python -m pytest tests/test_aggregate.py -v`
Expected: FAIL con `ModuleNotFoundError: No module named 'extractor.aggregate'`

- [ ] **Step 3: Implementar aggregate.py**

```python
# photoshop-style-extractor/extractor/aggregate.py
from collections import Counter
from extractor.model import PSDRecord, BrandStyle, GlobalStyle

_BAND_ORDER = {"arriba": 0, "centro": 1, "abajo": 2}


def _ranked_list(counter: Counter):
    return sorted(counter.items(), key=lambda kv: (-kv[1], str(kv[0])))


def _band_of(bbox: tuple[int, int, int, int], canvas_height: int) -> str:
    if canvas_height <= 0:
        return "centro"
    center_y = (bbox[1] + bbox[3]) / 2
    if center_y < canvas_height / 3:
        return "arriba"
    if center_y < canvas_height * 2 / 3:
        return "centro"
    return "abajo"


def _text_bands(records: list[PSDRecord]) -> list[tuple[str, int]]:
    bands: Counter = Counter()
    for rec in records:
        if rec.error is not None:
            continue
        for layer in rec.layers:
            if layer.text is not None:
                bands[_band_of(layer.bbox, rec.height)] += 1
    # orden lógico arriba→abajo, no por frecuencia
    return sorted(bands.items(), key=lambda kv: _BAND_ORDER.get(kv[0], 9))


def _collect(records: list[PSDRecord]):
    fonts, colors, canvases, effects, names = (
        Counter(), Counter(), Counter(), Counter(), Counter())
    for rec in records:
        if rec.error is not None:
            continue
        canvases[(rec.width, rec.height)] += 1
        for layer in rec.layers:
            if layer.kind == "error":
                continue
            names[layer.name] += 1
            for effect in layer.effects:
                effects[effect] += 1
            for color in layer.colors:
                colors[color] += 1
            if layer.text is not None:
                for font in layer.text.fonts:
                    fonts[font] += 1
    return fonts, colors, canvases, effects, names


def aggregate(records: list[PSDRecord]) -> tuple[GlobalStyle, list[BrandStyle]]:
    readable = [r for r in records if r.error is None]
    brands_seen: list[str] = []
    for rec in readable:
        if rec.brand not in brands_seen:
            brands_seen.append(rec.brand)

    brand_styles: list[BrandStyle] = []
    for brand in brands_seen:
        subset = [r for r in readable if r.brand == brand]
        fonts, colors, canvases, effects, names = _collect(subset)
        brand_styles.append(BrandStyle(
            brand=brand, piece_count=len(subset),
            fonts=_ranked_list(fonts), colors=_ranked_list(colors),
            canvas_sizes=_ranked_list(canvases), effects=_ranked_list(effects),
            layer_names=_ranked_list(names), text_bands=_text_bands(subset),
        ))

    g_fonts, g_colors, g_canvases, g_effects, _g_names = _collect(readable)
    glob = GlobalStyle(
        brands=brands_seen, psd_count=len(readable),
        fonts=_ranked_list(g_fonts), colors=_ranked_list(g_colors),
        canvas_sizes=_ranked_list(g_canvases), effects=_ranked_list(g_effects),
    )
    return glob, brand_styles


def list_fonts(records: list[PSDRecord]) -> list[str]:
    seen = set()
    for rec in records:
        if rec.error is not None:
            continue
        for layer in rec.layers:
            if layer.text is not None:
                seen.update(layer.text.fonts)
    return sorted(seen)


def list_unreadable(records: list[PSDRecord]) -> list[tuple[str, str]]:
    return [(r.path, r.error) for r in records if r.error is not None]
```

- [ ] **Step 4: Correr el test para verificar que pasa**

Run: `cd photoshop-style-extractor && python -m pytest tests/test_aggregate.py -v`
Expected: PASS (4 passed)

- [ ] **Step 5: Commit**

```bash
git add photoshop-style-extractor/extractor/aggregate.py photoshop-style-extractor/tests/test_aggregate.py
git commit -m "feat: agregacion de estadisticas globales y por marca"
```

---

### Task 7: Renderizado de la capa de estilo en Markdown

**Files:**
- Create: `photoshop-style-extractor/extractor/render.py`
- Test: `photoshop-style-extractor/tests/test_render.py`

**Interfaces:**
- Consumes: `GlobalStyle`, `BrandStyle` (Task 1); salidas de `aggregate` (Task 6).
- Produces:
  - `render_style_guide(glob: GlobalStyle) -> str` — markdown del ADN global (fuentes top, paleta global, tamaños de lienzo, efectos). Incluye una sección "✍️ Corregí esto" invitando a editar.
  - `render_brand(brand: BrandStyle) -> str` — markdown del kit de una marca (paleta, fuentes, lienzos, efectos, nombres de capa típicos, y composición vertical de textos desde `text_bands`).
  - `render_recipe(brand: BrandStyle) -> str` — un scaffold de receta por marca: describe el tamaño de lienzo más común y los nombres de capa más frecuentes como "estructura típica", marcado como punto de partida editable.
  - `render_report(fonts: list[str], unreadable: list[tuple[str,str]], psd_count: int) -> str` — reporte: lista de fuentes a verificar instaladas + PSDs no legibles.

- [ ] **Step 1: Escribir el test que falla**

```python
# photoshop-style-extractor/tests/test_render.py
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
```

- [ ] **Step 2: Correr el test para verificar que falla**

Run: `cd photoshop-style-extractor && python -m pytest tests/test_render.py -v`
Expected: FAIL con `ModuleNotFoundError: No module named 'extractor.render'`

- [ ] **Step 3: Implementar render.py**

```python
# photoshop-style-extractor/extractor/render.py
from extractor.model import GlobalStyle, BrandStyle


def _fmt_counts(items, unit="veces"):
    return "\n".join(f"- `{item}` — {count} {unit}" for item, count in items) or "- (nada detectado)"


def _fmt_canvases(items):
    lines = []
    for (w, h), count in items:
        lines.append(f"- {w}×{h} px — {count} piezas")
    return "\n".join(lines) or "- (nada detectado)"


def render_style_guide(glob: GlobalStyle) -> str:
    return f"""# Guía de estilo — ADN de diseño global

> Generado automáticamente a partir de {glob.psd_count} PSDs.
> Marcas detectadas: {", ".join(glob.brands) or "(ninguna)"}.

## ✍️ Corregí esto
Este archivo es un punto de partida. Editá lo que no te represente:
si una fuente o color aparece por casualidad, borralo; si falta tu
criterio (ej. "los titulares siempre van arriba"), agregalo en prosa.

## Tipografías más usadas
{_fmt_counts(glob.fonts, "capas de texto")}

## Paleta global
{_fmt_counts(glob.colors, "capas")}

## Tamaños de lienzo
{_fmt_canvases(glob.canvas_sizes)}

## Efectos de capa frecuentes
{_fmt_counts(glob.effects, "capas")}
"""


def render_brand(brand: BrandStyle) -> str:
    return f"""# Kit de marca — {brand.brand}

> {brand.piece_count} piezas analizadas.

## Paleta
{_fmt_counts(brand.colors, "capas")}

## Tipografías
{_fmt_counts(brand.fonts, "capas de texto")}

## Tamaños de lienzo
{_fmt_canvases(brand.canvas_sizes)}

## Efectos frecuentes
{_fmt_counts(brand.effects, "capas")}

## Nombres de capa típicos
{_fmt_counts(brand.layer_names, "piezas")}

## Composición (posición vertical de los textos)
{_fmt_counts(brand.text_bands, "capas de texto")}
"""


def render_recipe(brand: BrandStyle) -> str:
    top_canvas = brand.canvas_sizes[0][0] if brand.canvas_sizes else (1080, 1080)
    layers = "\n".join(f"   - {name}" for name, _ in brand.layer_names[:8]) or "   - (sin datos)"
    return f"""# Receta — pieza típica de {brand.brand}

> Punto de partida editable, derivado de las piezas analizadas.

**Lienzo sugerido:** {top_canvas[0]}×{top_canvas[1]} px

**Estructura típica de capas (de abajo hacia arriba):**
{layers}

**Pasos sugeridos:**
1. Crear el lienzo en el tamaño sugerido.
2. Colocar el fondo / imagen base.
3. Aplicar el tratamiento de color de la marca.
4. Montar los textos con la tipografía y paleta de la marca.
5. Agregar logo y CTA.
6. Revisar contra las referencias visuales de la marca.
"""


def render_report(fonts: list[str], unreadable: list[tuple[str, str]], psd_count: int) -> str:
    font_lines = "\n".join(f"- [ ] {f}" for f in fonts) or "- (ninguna detectada)"
    if unreadable:
        bad_lines = "\n".join(f"- `{path}` — {err}" for path, err in unreadable)
    else:
        bad_lines = "- (todos los PSDs se leyeron correctamente)"
    return f"""# Reporte de extracción

PSDs analizados con éxito: **{psd_count}**

## Fuentes a verificar instaladas en la PC con Photoshop
Marcá cada una cuando confirmes que está instalada:

{font_lines}

## PSDs no legibles (salteados)
{bad_lines}
"""
```

- [ ] **Step 4: Correr el test para verificar que pasa**

Run: `cd photoshop-style-extractor && python -m pytest tests/test_render.py -v`
Expected: PASS (4 passed)

- [ ] **Step 5: Commit**

```bash
git add photoshop-style-extractor/extractor/render.py photoshop-style-extractor/tests/test_render.py
git commit -m "feat: renderizado de la capa de estilo en markdown"
```

---

### Task 8: CLI orquestadora y test de integración end-to-end

**Files:**
- Create: `photoshop-style-extractor/extractor/cli.py`
- Create: `photoshop-style-extractor/run.py`
- Create: `photoshop-style-extractor/README.md`
- Test: `photoshop-style-extractor/tests/test_cli_e2e.py`

**Interfaces:**
- Consumes: `discover_psds` (Task 5), `read_psd` (Task 4), `aggregate`/`list_fonts`/`list_unreadable` (Task 6), `render_*` (Task 7).
- Produces:
  - `run_extraction(input_dir: str, output_dir: str) -> dict` — orquesta todo: descubre PSDs, los lee (con previews en `output_dir/references/`), agrega, y escribe `output_dir/style-guide.md`, `output_dir/brands/<marca>.md`, `output_dir/recipes/<marca>.md`, `output_dir/report.md`. Devuelve un dict resumen `{"psd_count", "brands", "unreadable", "output_dir"}`. Crea las carpetas necesarias.
  - `main(argv: list[str] | None = None) -> int` — parsea `--input` y `--output` y llama a `run_extraction`. `run.py` es el envoltorio ejecutable (`python run.py --input ... --output ...`).

- [ ] **Step 1: Escribir el test que falla**

```python
# photoshop-style-extractor/tests/test_cli_e2e.py
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
```

- [ ] **Step 2: Correr el test para verificar que falla**

Run: `cd photoshop-style-extractor && python -m pytest tests/test_cli_e2e.py -v`
Expected: FAIL con `ModuleNotFoundError: No module named 'extractor.cli'`

- [ ] **Step 3: Implementar cli.py, run.py y README**

```python
# photoshop-style-extractor/extractor/cli.py
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
```

```python
# photoshop-style-extractor/run.py
import sys
from extractor.cli import main

if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
```

```markdown
<!-- photoshop-style-extractor/README.md -->
# Extractor de estilo (Fase 1)

Analiza tus PSDs y genera una "capa de estilo" editable.

## Instalar (una vez)
```
pip install -r requirements.txt
```

## Usar
```
python run.py --input "C:/ruta/a/tus/psds" --output "C:/ruta/salida/style-layer"
```

- `--input`: carpeta con tus `.psd`. Poné cada marca en su subcarpeta
  (ej. `psds/PizzeriaRoma/*.psd`); los sueltos quedan como "sin-marca".
- `--output`: donde se escribe la capa de estilo.

## Qué genera
- `style-guide.md` — tu ADN de diseño global (editalo a gusto).
- `brands/<marca>.md` — kit por marca.
- `recipes/<marca>.md` — receta de pieza típica por marca.
- `references/*.jpg` — preview de cada PSD.
- `report.md` — fuentes a verificar + PSDs no legibles.
```

- [ ] **Step 4: Correr el test para verificar que pasa**

Run: `cd photoshop-style-extractor && python -m pytest tests/test_cli_e2e.py -v`
Expected: PASS (1 passed)

- [ ] **Step 5: Correr toda la suite y commit**

Run: `cd photoshop-style-extractor && python -m pytest -v`
Expected: PASS (todos los tests de las 8 tareas)

```bash
git add photoshop-style-extractor/extractor/cli.py photoshop-style-extractor/run.py photoshop-style-extractor/README.md photoshop-style-extractor/tests/test_cli_e2e.py
git commit -m "feat: CLI orquestadora y test end-to-end del extractor"
```

---

## Cierre de la Fase 1

Al terminar las 8 tareas tenés una herramienta ejecutable con `python run.py --input <psds> --output <style-layer>` que produce tu capa de estilo real. El siguiente paso (fuera de este plan) es que Facu corra el extractor sobre sus 20+ PSDs, revise y corrija `style-guide.md` y los `brands/*.md`, y verifique el `report.md` de fuentes. Recién entonces se pasa a la Fase 2 (MCP + skill en la PC con Photoshop).
