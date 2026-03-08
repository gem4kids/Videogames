# CLAUDE.md — MATEPONG

## 1. Qué es este proyecto
MATEPONG es un juego arcade 2D para dos jugadores construido con Pygame.
Es una versión custom de Pong con estética neón, sistema de sets (mejor de 3),
potenciadores especiales (relámpago ⚡) y ranking persistente de partidas más rápidas.
El objetivo del proyecto es ir añadiendo nuevas mecánicas y personalizaciones custom.

## 2. Estado actual
- ✅ Game loop completo con sistema de sets (mejor de 3, 5 puntos por set)
- ✅ Dos jugadores locales (W/S y UP/DOWN)
- ✅ Potenciador relámpago ⚡ (duplica velocidad al golpear, aparece cada 8s)
- ✅ Estética arcade neón con estela en pelota, halos y efectos visuales
- ✅ Ranking persistente en ranking.json (top 8 partidas más rápidas)
- ✅ Pantallas: inicio, pedir nombre, fin de set, fin de partida
- ✅ Cronómetro y marcador con indicador de sets ganados
- ✅ Publicado en web via pygbag (WebAssembly) + GitHub Pages
- 📋 Pendiente: nuevos potenciadores, nuevos modos de juego

## 3. Stack técnico
- **Python:** 3.11
- **Librería principal:** pygame
- **Entorno virtual:** `venv` (activar con `source venv/bin/activate`)
- **Persistencia:** `ranking.json` — top 8 victorias ordenadas por tiempo
- **Variables de entorno:** ninguna

## 4. Estructura del proyecto
```
src/
  __init__.py
  pong.py          # Todo el juego en un único archivo (~720 líneas)
  ranking.json     # Puntuaciones persistentes ⚠️ nunca borrar
tests/
  test_main.py
venv/
.gitignore
CLAUDE.md
requirements.txt
```

## 5. Arquitectura interna de pong.py
El archivo está organizado en estas secciones, en este orden:

1. **Constantes** — ANCHO, ALTO, FPS, colores, dimensiones, física
2. **Ranking** — `cargar_ranking()`, `guardar_ranking()`, `registrar_victoria()`
3. **Clase Paleta** — movimiento, límites, dibujo con efecto neón
4. **Clase Pelota** — movimiento, rebote en bordes, `rebotar_paleta()`, estela
5. **Clase PowerupRelampago** — spawn, colisión, recogida, dibujo con pulso animado
6. **Funciones de dibujo** — `dibujar_fondo()`, `dibujar_controles()`, `dibujar_marcador()`
7. **Pantallas** — `pedir_nombre()`, `pantalla_inicio()`, `pantalla_fin_set()`, `pantalla_fin_partida()`
8. **Game loop del set** — `jugar_set()` con lógica completa de potenciadores
9. **Main** — `main()` con bucle de partida completa

## 6. Convenciones del código
1. **Idioma:** Python 3 con type hints siempre
2. **Nomenclatura:** `snake_case` para variables/funciones, `PascalCase` para clases
3. **Comentarios:** En español
4. **Constantes:** En MAYÚSCULAS al inicio del archivo. Nunca magic numbers en el código
5. **Docstrings:** En todas las funciones y métodos públicos (formato Google style)
6. **Colores:** Siempre como tuplas RGB definidas en la sección de constantes
7. **Game loop:** Siempre sigue el patrón eventos → update → draw
8. **Nuevos potenciadores:** Deben ser nuevas clases con los métodos:
   `intentar_spawn()`, `comprobar_colision()`, `recoger()`, `dibujar()`, `dibujar_icono_hud()`
   (seguir exactamente el patrón de PowerupRelampago como referencia)

## 7. Física y jugabilidad — valores clave
- `PELOTA_VEL = 5` — velocidad inicial
- `VEL_MAX = 22` — límite absoluto (no superar, hace el juego injugable)
- La velocidad aumenta +0.3 en cada rebote con paleta
- El ángulo de rebote depende del punto de impacto en la paleta (±60°)
- `INTERVALO_POWERUP = 8` — segundos entre apariciones del potenciador
- El potenciador solo se recoge si la pelota está en el campo RIVAL al tocarlo

## 8. Reglas de comportamiento para Claude
- ✅ Puedes editar libremente `src/pong.py` y `tests/test_main.py`
- ✅ Puedes ejecutar el juego: `python src/pong.py`
- ✅ Al añadir un potenciador nuevo, sigue el patrón de `PowerupRelampago`
- ✅ Al añadir una pantalla nueva, sígue el patrón de `pantalla_fin_set()`
- ⚠️ Respeta siempre VEL_MAX — no crear mecánicas que lo superen
- ⚠️ Pregúntame antes de dividir pong.py en múltiples archivos
- ⚠️ Pregúntame antes de añadir dependencias nuevas a requirements.txt
- 🚫 Nunca borres ni sobreescribas ranking.json con datos vacíos
- 🚫 Nunca hagas commits sin mi confirmación explícita
- 🚫 No cambies los controles (W/S e UP/DOWN) sin pedírmelo

## 9. Git — formato de commits
- `feat: añadir potenciador de escudo`
- `feat: nueva pantalla de pausa`
- `fix: corregir colisión doble en esquina`
- `refactor: extraer dibujo del marcador a función`
- `balance: ajustar velocidad inicial a 6`

## 10. Comandos del proyecto
- **Ejecutar:** `python src/pong.py`
- **Tests:** `pytest tests/`
- **Instalar dependencias:** `pip install -r requirements.txt`
- **Activar entorno:** `source venv/bin/activate`
- **Build web local:** `python3 -m pygbag --build src` (output en `src/build/web/`)

## 11. URLs del proyecto
- **Web (producción):** `https://gem4kids.github.io/Videogames/`
- **Repositorio:** `https://github.com/gem4kids/Videogames`

## 12. Lecciones WASM (pygbag) aprendidas
- `__file__` no existe en WASM al importar → proteger con `try/except` en constantes globales
- `pygame.init()` completo puede bloquear → usar `pygame.display.init()` + `pygame.font.init()`
- `ume_block` debe ser `0` en `docs/index.html` para arranque sin bloqueo de audio
- `data-os` sin `snd` (ej. `vtx,fs,gui`) para evitar AudioContext blocking en Firefox/Chrome
- `git push --force` necesario porque GitHub Actions hace commits automáticos en cada deploy