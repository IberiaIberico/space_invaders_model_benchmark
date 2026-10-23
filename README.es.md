# Invaders Bench

[🇬🇧 English](README.md) | 🇪🇸 Español

Un pequeño benchmark que pide a distintos modelos de IA construir el mismo juego, un clon de Space Invaders, en un único archivo HTML autocontenido. El resultado de cada modelo se guarda en su propia carpeta para poder jugarlos y comparar calidad, velocidad y coste.

## Cómo funciona

1. `invaders_bench.py` envía a un modelo un prompt fijo (una especificación detallada de Space Invaders: render con canvas, escudos, OVNI, sonidos con Web Audio, progresión de oleadas, etc.).
2. El HTML de la respuesta se extrae y se guarda en `<modelo>/invaders.html`, junto con la respuesta original (`response.md`) y los metadatos de la ejecución (`meta.json`).
3. `build_index.py` genera `index.html`, un panel que enlaza cada ejecución, muestra sus estadísticas y permite jugar cada juego.

## Estructura del proyecto

```
ai_invaders/
├── invaders_bench.py      # Ejecuta un modelo y guarda el resultado
├── build_index.py         # Genera el panel index.html
├── index.html             # Panel generado (ábrelo en el navegador)
└── <nombre-del-modelo>/
    ├── invaders.html      # El juego generado por el modelo
    ├── response.md        # Respuesta original del modelo (ejecuciones locales/API)
    ├── reasoning.md       # Cadena de razonamiento, si la API la devolvió
    └── meta.json          # Tiempos, tokens, coste, prompt y parámetros
```

Algunas carpetas (por ejemplo `sonnet-5.5`, `opus-5.5`, `haiku-5.5`, `fable-5.1` y las de `gemini-*`) provienen de ejecuciones con agentes y solo contienen `invaders.html` y, en algunos casos, `meta.json`.

## Requisitos

- Python 3.10+ (usa la sintaxis de tipos `X | None`). Sin paquetes de terceros, solo biblioteca estándar.
- Para ejecutar nuevos benchmarks: [LM Studio](https://lmstudio.ai/) con el servidor local activado (por defecto `http://localhost:1234/v1`), o una clave de API de DeepSeek.
- Un navegador moderno para jugar.

## Uso

### Ver los resultados

Abre `index.html` en un navegador. Puedes filtrar por nombre, ordenar por velocidad, tokens o tamaño, leer los prompts utilizados y pulsar **Play ▶** en cualquier tarjeta.

### Ejecutar un modelo con LM Studio

```bash
python invaders_bench.py --list                      # lista los modelos disponibles
python invaders_bench.py qwen/qwen3-coder-30b        # ejecuta un modelo
```

### Ejecutar con DeepSeek

```bash
python invaders_bench.py deepseek-chat --deepseek-key sk-...
# o toma la clave de la variable de entorno DEEPSEEK_API_KEY
python invaders_bench.py deepseek-reasoner --deepseek-key
```

### Opciones útiles

| Opción | Descripción |
| --- | --- |
| `--prompt "..."` / `--prompt-file ARCHIVO` | Usa un prompt propio en lugar del incluido |
| `--system "..."` | Prompt de sistema personalizado |
| `--url URL` | URL base de la API |
| `--folder NOMBRE` | Nombre de la carpeta de salida (por defecto se deriva del id del modelo) |
| `--out DIR` | Directorio raíz de salida |
| `--temperature N` | Temperatura de muestreo (por defecto `0.2`) |
| `--max-tokens N` | Máximo de tokens de salida (por defecto `32000`) |
| `--timeout SEGUNDOS` | Tiempo límite de la petición (por defecto `1800`) |
| `--no-index` | No regenera `index.html` tras la ejecución |

### Regenerar el panel manualmente

```bash
python build_index.py
```

Cualquier subcarpeta que contenga un `invaders.html` se detecta automáticamente. Para añadir una ejecución con agente (un modelo que no se sirve por API), crea una carpeta, coloca dentro `invaders.html` y, opcionalmente, un `meta.json`, y regenera el índice.

## El prompt

El prompt por defecto pide una reproducción fiel del arcade de 1978: cañón del jugador con un solo disparo en pantalla, alienígenas que se aceleran al ser destruidos, cuatro escudos destructibles, un OVNI, puntuación, vidas, progresión de oleadas, estética pixel-art con resolución fija escalada y efectos de sonido con Web Audio, todo en un único HTML sin dependencias externas. El prompt exacto puede verse en `invaders_bench.py` y en el panel.

## Notas

- Los resultados no son deterministas. El mismo modelo puede generar un juego distinto en cada ejecución.
- Los juegos los generan modelos de IA y no han sido auditados. Ábrelos en el navegador como cualquier HTML local no confiable.
