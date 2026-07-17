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
