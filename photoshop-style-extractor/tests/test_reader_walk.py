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
