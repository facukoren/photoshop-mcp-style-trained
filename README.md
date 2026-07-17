# Photoshop MCP · Style-Trained

Sistema para que una AI diseñe en Adobe Photoshop **con tu estilo**: a partir de un
brief en lenguaje natural produce piezas de social media/marketing como las harías
vos, y funciona además como copiloto en vivo dentro de Photoshop.

La idea central: **no se hace fine-tuning de ningún modelo**. Tu estilo se captura
como una *capa de conocimiento* en archivos de texto que podés leer y corregir, y
que la AI consulta cada vez que diseña. Es entrenable con el uso, inspeccionable y
portable.

## Cómo funciona (3 componentes)

```
1. EXTRACTOR DE ESTILO  →  2. CAPA DE ESTILO  →  3. EJECUCIÓN
   (Python, esta repo)      (carpeta portable)     (Claude + MCP Photoshop)
   analiza tus PSDs         style-guide.md          brief → PSD en tu estilo
                            brands/*.md             o copiloto en vivo
                            recipes/*.md
                            references/*.jpg
```

## Estado del proyecto

| Fase | Qué | Estado |
|------|-----|--------|
| **1** | Extractor de estilo + capa de estilo | ✅ Implementado (27 tests en verde) |
| 2 | MCP de Photoshop + skill "diseñar como vos" | ⏳ Próximo |
| 3 | Instalador simple para colegas no técnicos | ⏳ Pendiente |
| 4 | Generación con IA (Firefly) + producción en lote | ⏳ Pendiente |

## Fase 1 — Extractor (ya usable)

Analiza tus PSDs y genera tu capa de estilo editable. Ver
[`photoshop-style-extractor/`](photoshop-style-extractor/README.md).

```bash
cd photoshop-style-extractor
pip install -r requirements.txt
python run.py --input "C:/ruta/a/tus/psds" --output "C:/salida/style-layer"
```

Poné cada marca en su subcarpeta (`psds/PizzeriaRoma/*.psd`); los sueltos quedan
como "sin-marca". Genera `style-guide.md`, `brands/*.md`, `recipes/*.md`,
`references/*.jpg` y un `report.md` con las fuentes a verificar instaladas.

## Documentación

- [Diseño del sistema completo](docs/superpowers/specs/2026-07-17-photoshop-style-ai-design.md)
- [Plan de implementación de la Fase 1](docs/superpowers/plans/2026-07-17-fase1-extractor-estilo.md)

## Stack

Python 3.14 · psd-tools · Pillow · pytest. El MCP candidato para la Fase 2 es
[alisaitteke/photoshop-mcp](https://github.com/alisaitteke/photoshop-mcp).
