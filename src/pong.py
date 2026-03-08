import asyncio
import pygame
import sys
import random
import math
import json
import os
import time

# ─────────────────────────────────────────
#  CONFIGURACIÓN GENERAL
# ─────────────────────────────────────────
ANCHO, ALTO      = 800, 600
FPS              = 60
PUNTOS_SET       = 5           # Puntos necesarios para ganar un set
SETS_PARA_GANAR  = 2           # Sets necesarios para ganar la partida (mejor de 3)
ARCHIVO_RANKING  = os.path.join(os.path.dirname(__file__), "ranking.json")

# Tiempo en segundos entre apariciones de potenciadores
INTERVALO_POWERUP = 8
# Velocidad máxima absoluta de la pelota (evita que sea injugable)
VEL_MAX           = 22

# ── Paleta de colores arcade ────────────────
NEGRO      = (0,   0,   0)
BLANCO     = (255, 255, 255)
VERDE_NEON = (0,   255, 100)
CYAN_NEON  = (0,   220, 255)
ROJO_NEON  = (255,  50,  50)
GRIS_OSC   = (30,   30,  30)
GRIS_MED   = (100, 100, 100)
AMARILLO   = (255, 220,   0)
NARANJA    = (255, 140,   0)
AZUL_NEON  = (50,  120, 255)

# ── Dimensiones de las paletas ───────────────
PALETA_ANCHO = 12
PALETA_ALTO  = 90
PALETA_VEL   = 6

# ── Pelota ───────────────────────────────────
PELOTA_RADIO = 9
PELOTA_VEL   = 5

# ── Potenciador ──────────────────────────────
RADIO_POWERUP = 20


# ─────────────────────────────────────────
#  RANKING: carga y guardado en JSON
# ─────────────────────────────────────────
def cargar_ranking() -> list:
    """Lee el archivo de ranking y devuelve la lista ordenada por tiempo.
    Devuelve lista vacía si el archivo no existe o no se puede leer (ej. entorno web)."""
    try:
        if not os.path.exists(ARCHIVO_RANKING):
            return []
        with open(ARCHIVO_RANKING, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return []

def guardar_ranking(ranking: list) -> None:
    """Guarda la lista de ranking en el archivo JSON.
    Silencia errores de escritura en entorno web (sistema de archivos WASM)."""
    try:
        with open(ARCHIVO_RANKING, "w", encoding="utf-8") as f:
            json.dump(ranking, f, ensure_ascii=False, indent=2)
    except Exception:
        pass

def registrar_victoria(ganador: str, rival: str, segundos: float) -> None:
    """Añade una nueva entrada al ranking y mantiene solo las 8 mejores."""
    ranking = cargar_ranking()
    ranking.append({"ganador": ganador, "rival": rival, "tiempo": round(segundos, 1)})
    ranking.sort(key=lambda r: r["tiempo"])
    guardar_ranking(ranking[:8])


# ─────────────────────────────────────────
#  CLASE PALETA
# ─────────────────────────────────────────
class Paleta:
    def __init__(self, x: int, color: tuple):
        # Posición inicial centrada verticalmente
        self.rect  = pygame.Rect(x, ALTO // 2 - PALETA_ALTO // 2, PALETA_ANCHO, PALETA_ALTO)
        self.color = color
        self.vel   = 0

    def reiniciar(self):
        """Devuelve la paleta al centro."""
        self.rect.y = ALTO // 2 - PALETA_ALTO // 2

    def mover(self):
        # Mover y limitar dentro de los bordes verticales
        self.rect.y += self.vel
        self.rect.y  = max(0, min(ALTO - PALETA_ALTO, self.rect.y))

    def dibujar(self, pantalla: pygame.Surface):
        # Sombra tipo neón
        sombra = self.rect.inflate(6, 6)
        pygame.draw.rect(pantalla,
                         (self.color[0] // 4, self.color[1] // 4, self.color[2] // 4),
                         sombra, border_radius=4)
        # Paleta principal
        pygame.draw.rect(pantalla, self.color, self.rect, border_radius=4)
        # Brillo central
        brillo = pygame.Rect(self.rect.x + 2, self.rect.y + 6,
                             PALETA_ANCHO - 4, PALETA_ALTO - 12)
        pygame.draw.rect(pantalla, BLANCO, brillo, border_radius=2)


# ─────────────────────────────────────────
#  CLASE PELOTA
# ─────────────────────────────────────────
class Pelota:
    def __init__(self):
        self.reiniciar()

    def reiniciar(self):
        # Colocar la pelota en el centro con dirección aleatoria
        self.x    = float(ANCHO // 2)
        self.y    = float(ALTO  // 2)
        angulo    = random.uniform(-40, 40)
        dir_x     = random.choice([-1, 1])
        rad       = math.radians(angulo)
        self.vx   = dir_x * PELOTA_VEL * math.cos(rad)
        self.vy   = PELOTA_VEL * math.sin(rad)
        self.trail = []

    def mover(self):
        # Guardar posición en la estela
        self.trail.append((int(self.x), int(self.y)))
        if len(self.trail) > 10:
            self.trail.pop(0)
        self.x += self.vx
        self.y += self.vy
        # Rebotar en bordes superior e inferior
        if self.y - PELOTA_RADIO <= 0:
            self.y   = PELOTA_RADIO
            self.vy *= -1
        elif self.y + PELOTA_RADIO >= ALTO:
            self.y   = ALTO - PELOTA_RADIO
            self.vy *= -1

    def rebotar_paleta(self, paleta: Paleta, con_powerup: bool = False) -> bool:
        """
        Comprueba si la pelota choca con la paleta y aplica el rebote.
        Si con_powerup es True, la velocidad se duplica al rebotar.
        Devuelve True si hubo colisión.
        """
        rect_pelota = pygame.Rect(self.x - PELOTA_RADIO, self.y - PELOTA_RADIO,
                                  PELOTA_RADIO * 2, PELOTA_RADIO * 2)
        if not rect_pelota.colliderect(paleta.rect):
            return False

        # Calcular ángulo según el punto de impacto en la paleta
        centro_paleta = paleta.rect.centery
        diferencia    = (self.y - centro_paleta) / (PALETA_ALTO / 2)
        angulo        = diferencia * 60
        velocidad     = math.hypot(self.vx, self.vy) + 0.3

        # Si el jugador tiene el potenciador relámpago, duplicar velocidad
        if con_powerup:
            velocidad *= 2

        # Aplicar límite máximo para que sea jugable
        velocidad = min(velocidad, VEL_MAX)
        rad       = math.radians(angulo)
        nueva_dir = 1 if self.vx < 0 else -1
        self.vx   = nueva_dir * velocidad * math.cos(rad)
        self.vy   = velocidad * math.sin(rad)

        # Sacar la pelota de la paleta para evitar colisión doble
        if nueva_dir == 1:
            self.x = paleta.rect.right + PELOTA_RADIO + 1
        else:
            self.x = paleta.rect.left  - PELOTA_RADIO - 1
        return True

    def dibujar(self, pantalla: pygame.Surface):
        # Estela con opacidad decreciente
        for i, (tx, ty) in enumerate(self.trail):
            alpha       = int(200 * (i / len(self.trail))) if self.trail else 0
            radio_trail = max(2, PELOTA_RADIO - (len(self.trail) - i))
            surf        = pygame.Surface((radio_trail * 2, radio_trail * 2), pygame.SRCALPHA)
            pygame.draw.circle(surf, (*CYAN_NEON, alpha), (radio_trail, radio_trail), radio_trail)
            pantalla.blit(surf, (tx - radio_trail, ty - radio_trail))
        # Halo
        pygame.draw.circle(pantalla, (0, 80, 100), (int(self.x), int(self.y)), PELOTA_RADIO + 5)
        # Pelota
        pygame.draw.circle(pantalla, BLANCO,    (int(self.x), int(self.y)), PELOTA_RADIO)
        # Brillo
        pygame.draw.circle(pantalla, CYAN_NEON, (int(self.x) - 3, int(self.y) - 3), 3)


# ─────────────────────────────────────────
#  CLASE POTENCIADOR RELÁMPAGO
# ─────────────────────────────────────────
class PowerupRelampago:
    def __init__(self):
        self.activo      = False
        self.x           = 0
        self.y           = 0
        self.radio       = RADIO_POWERUP
        self.ultimo_spawn = 0.0   # tiempo (time.time()) del último spawn o recogida

    def intentar_spawn(self, ahora: float):
        """Spawnea el potenciador si ha pasado suficiente tiempo y no está activo."""
        if not self.activo and (ahora - self.ultimo_spawn) >= INTERVALO_POWERUP:
            margen_x = 100
            margen_y = 100
            # Elegir campo izquierdo o derecho aleatoriamente
            if random.random() < 0.5:
                self.x = random.randint(margen_x, ANCHO // 2 - margen_x)
            else:
                self.x = random.randint(ANCHO // 2 + margen_x, ANCHO - margen_x)
            self.y      = random.randint(margen_y, ALTO - margen_y)
            self.activo = True

    def comprobar_colision(self, pelota_x: float, pelota_y: float) -> bool:
        """Devuelve True si la pelota toca el potenciador."""
        if not self.activo:
            return False
        return math.hypot(pelota_x - self.x, pelota_y - self.y) < self.radio + PELOTA_RADIO

    def recoger(self, ahora: float):
        """Desactiva el potenciador y registra el momento de recogida."""
        self.activo      = False
        self.ultimo_spawn = ahora

    def dibujar(self, pantalla: pygame.Surface):
        if not self.activo:
            return

        t   = pygame.time.get_ticks() / 1000.0
        cx  = int(self.x)
        cy  = int(self.y)
        pulso = int(6 * math.sin(t * 5))   # efecto pulsante

        # ── Halos exteriores translúcidos ────────────
        for radio_halo, alpha in [(self.radio + 16 + pulso, 35), (self.radio + 9 + pulso // 2, 70)]:
            surf_halo = pygame.Surface((radio_halo * 2, radio_halo * 2), pygame.SRCALPHA)
            pygame.draw.circle(surf_halo, (*AZUL_NEON, alpha), (radio_halo, radio_halo), radio_halo)
            pantalla.blit(surf_halo, (cx - radio_halo, cy - radio_halo))

        # ── Esfera principal ─────────────────────────
        pygame.draw.circle(pantalla, (8, 18, 55),    (cx, cy), self.radio)          # interior oscuro
        pygame.draw.circle(pantalla, AZUL_NEON,      (cx, cy), self.radio, 2)       # borde neón
        pygame.draw.circle(pantalla, (100, 160, 255), (cx - 5, cy - 5), 5)          # brillo

        # ── Rayo / relámpago dentro de la esfera ─────
        # Se dibuja como un polígono en zigzag (forma ⚡)
        s = 11   # escala del rayo
        pts_rayo = [
            (cx - 3,  cy - s),      # punta superior izquierda
            (cx + 5,  cy - 2),      # vértice derecho superior
            (cx + 0,  cy - 2),      # entrada al codo
            (cx + 3,  cy + s),      # punta inferior derecha
            (cx - 5,  cy + 2),      # vértice izquierdo inferior
            (cx - 0,  cy + 2),      # salida del codo
        ]
        pygame.draw.polygon(pantalla, AZUL_NEON, pts_rayo)
        # Brillo interior blanco del rayo
        pts_brillo = [
            (cx - 1, cy - s + 3),
            (cx + 3, cy - 2),
            (cx + 1, cy - 2),
            (cx + 1, cy + s - 5),
        ]
        pygame.draw.polygon(pantalla, (200, 230, 255), pts_brillo)

    def dibujar_icono_hud(self, pantalla: pygame.Surface, cx: int, cy: int, escala: float = 0.55):
        """Dibuja un icono pequeño del relámpago en el HUD del jugador."""
        r = int(RADIO_POWERUP * escala)
        pygame.draw.circle(pantalla, (8, 18, 55),   (cx, cy), r)
        pygame.draw.circle(pantalla, AZUL_NEON,     (cx, cy), r, 2)
        s = int(11 * escala)
        pts = [
            (cx - 2, cy - s),
            (cx + 3, cy - 1),
            (cx + 0, cy - 1),
            (cx + 2, cy + s),
            (cx - 3, cy + 1),
            (cx + 0, cy + 1),
        ]
        pygame.draw.polygon(pantalla, AZUL_NEON, pts)


# ─────────────────────────────────────────
#  FUNCIONES DE DIBUJO COMUNES
# ─────────────────────────────────────────
def dibujar_fondo(pantalla: pygame.Surface):
    # Fondo negro con línea central punteada
    pantalla.fill(NEGRO)
    for y in range(0, ALTO, 30):
        pygame.draw.rect(pantalla, (40, 40, 40), (ANCHO // 2 - 2, y, 4, 18))


def dibujar_controles(pantalla: pygame.Surface, fuente_small: pygame.font.Font):
    # Leyenda de controles en la parte inferior
    izq = fuente_small.render("W / S", True, VERDE_NEON)
    der = fuente_small.render("UP / DOWN", True, ROJO_NEON)
    pantalla.blit(izq, (30, ALTO - 22))
    pantalla.blit(der, (ANCHO - der.get_width() - 30, ALTO - 22))


def dibujar_marcador(pantalla, fuente, fuente_small, fuente_titulo,
                     nombre_izq, nombre_der,
                     pts_izq, pts_der,
                     sets_izq, sets_der,
                     segundos_transcurridos,
                     powerup_izq: bool = False,
                     powerup_der: bool = False):
    # ── Título MATEPONG ──────────────────────────
    titulo = fuente_titulo.render("MATEPONG", True, AMARILLO)
    pantalla.blit(titulo, (ANCHO // 2 - titulo.get_width() // 2, 4))

    # ── Puntos del set actual ────────────────────
    t_izq = fuente.render(str(pts_izq), True, VERDE_NEON)
    t_der = fuente.render(str(pts_der), True, ROJO_NEON)
    pantalla.blit(t_izq, (ANCHO // 4     - t_izq.get_width() // 2, 8))
    pantalla.blit(t_der, (3 * ANCHO // 4 - t_der.get_width() // 2, 8))

    # ── Sets ganados (bolitas) ───────────────────
    for i in range(SETS_PARA_GANAR):
        color_izq = VERDE_NEON if i < sets_izq else GRIS_OSC
        color_der = ROJO_NEON  if i < sets_der else GRIS_OSC
        pygame.draw.circle(pantalla, color_izq, (ANCHO // 4     - 15 + i * 20, 56), 7)
        pygame.draw.circle(pantalla, color_der, (3 * ANCHO // 4 - 15 + i * 20, 56), 7)

    # ── Nombres de los jugadores ─────────────────
    n_izq = fuente_small.render(nombre_izq[:10], True, VERDE_NEON)
    n_der = fuente_small.render(nombre_der[:10], True, ROJO_NEON)
    pantalla.blit(n_izq, (30, 8))
    pantalla.blit(n_der, (ANCHO - n_der.get_width() - 30, 8))

    # ── Icono de potenciador activo junto al nombre ──
    _icono = PowerupRelampago()   # objeto auxiliar solo para dibujar el icono
    if powerup_izq:
        _icono.dibujar_icono_hud(pantalla, 30 + n_izq.get_width() + 16, 16)
    if powerup_der:
        _icono.dibujar_icono_hud(pantalla, ANCHO - n_der.get_width() - 50, 16)

    # ── Cronómetro ───────────────────────────────
    mins  = int(segundos_transcurridos) // 60
    segs  = int(segundos_transcurridos) % 60
    crono = fuente_small.render(f"{mins:02d}:{segs:02d}", True, GRIS_MED)
    pantalla.blit(crono, (ANCHO // 2 - crono.get_width() // 2, 56))


# ─────────────────────────────────────────
#  PANTALLA: INTRODUCIR NOMBRE
# ─────────────────────────────────────────
async def pedir_nombre(pantalla, reloj, fuente_titulo, fuente, fuente_small,
                       num_jugador: int, color: tuple) -> str:
    """Muestra una pantalla para que el jugador escriba su nombre (máx. 12 caracteres)."""
    nombre = ""
    while True:
        for evento in pygame.event.get():
            if evento.type == pygame.QUIT:
                pygame.quit(); sys.exit()
            if evento.type == pygame.KEYDOWN:
                if evento.key == pygame.K_ESCAPE:
                    pygame.quit(); sys.exit()
                elif evento.key == pygame.K_RETURN and nombre.strip():
                    return nombre.strip()
                elif evento.key == pygame.K_BACKSPACE:
                    nombre = nombre[:-1]
                elif len(nombre) < 12 and evento.unicode.isprintable():
                    nombre += evento.unicode

        pantalla.fill(NEGRO)
        t = fuente_titulo.render("MATEPONG", True, AMARILLO)
        pantalla.blit(t, (ANCHO // 2 - t.get_width() // 2, 60))

        label = fuente.render(f"JUGADOR {num_jugador}", True, color)
        pantalla.blit(label, (ANCHO // 2 - label.get_width() // 2, ALTO // 2 - 80))

        instr = fuente_small.render("Escribe tu nombre y pulsa ENTER", True, GRIS_MED)
        pantalla.blit(instr, (ANCHO // 2 - instr.get_width() // 2, ALTO // 2 - 40))

        # Caja de texto con cursor parpadeante
        cursor  = "_" if (pygame.time.get_ticks() // 500) % 2 == 0 else " "
        caja    = fuente.render(nombre + cursor, True, BLANCO)
        pygame.draw.rect(pantalla, GRIS_OSC, (ANCHO // 2 - 150, ALTO // 2, 300, 50), border_radius=6)
        pygame.draw.rect(pantalla, color,    (ANCHO // 2 - 150, ALTO // 2, 300, 50), 2, border_radius=6)
        pantalla.blit(caja, (ANCHO // 2 - caja.get_width() // 2, ALTO // 2 + 8))

        pygame.display.flip()
        await asyncio.sleep(0)
        reloj.tick(FPS)


# ─────────────────────────────────────────
#  PANTALLA: INICIO + RANKING
# ─────────────────────────────────────────
async def pantalla_inicio(pantalla, reloj, fuente_titulo, fuente, fuente_small):
    """Muestra la pantalla de inicio con el ranking de partidas más rápidas."""
    ranking = cargar_ranking()
    while True:
        for evento in pygame.event.get():
            if evento.type == pygame.QUIT:
                pygame.quit(); sys.exit()
            if evento.type == pygame.KEYDOWN:
                if evento.key == pygame.K_ESCAPE:
                    pygame.quit(); sys.exit()
                if evento.key == pygame.K_SPACE:
                    return

        pantalla.fill(NEGRO)
        titulo = fuente_titulo.render("MATEPONG", True, AMARILLO)
        pantalla.blit(titulo, (ANCHO // 2 - titulo.get_width() // 2, 40))

        sub = fuente_small.render(
            f"Mejor de {SETS_PARA_GANAR * 2 - 1} sets  |  {PUNTOS_SET} puntos por set  |  ⚡ Potenciadores activos",
            True, GRIS_MED)
        pantalla.blit(sub, (ANCHO // 2 - sub.get_width() // 2, 112))

        # ── Tabla de clasificación ──────────────────
        if ranking:
            pygame.draw.rect(pantalla, GRIS_OSC, (80, 150, ANCHO - 160, 345), border_radius=8)
            pygame.draw.rect(pantalla, AMARILLO,  (80, 150, ANCHO - 160, 345), 1, border_radius=8)

            cab = fuente_small.render("★  RANKING DE PARTIDAS MÁS RÁPIDAS  ★", True, AMARILLO)
            pantalla.blit(cab, (ANCHO // 2 - cab.get_width() // 2, 160))

            col_pos    = [110, 250, 450, 620]
            cabeceras  = ["#", "GANADOR", "vs RIVAL", "TIEMPO"]
            col_col    = [GRIS_MED, VERDE_NEON, ROJO_NEON, CYAN_NEON]
            for texto, x, color in zip(cabeceras, col_pos, col_col):
                pantalla.blit(fuente_small.render(texto, True, color), (x, 187))

            pygame.draw.line(pantalla, GRIS_MED, (90, 210), (ANCHO - 90, 210))

            medallas = ["1st", "2nd", "3rd"] + [f"{n+1}th" for n in range(3, 8)]
            for i, entrada in enumerate(ranking):
                y_f    = 218 + i * 35
                c_fila = AMARILLO if i == 0 else BLANCO
                mins   = int(entrada["tiempo"]) // 60
                segs   = int(entrada["tiempo"]) % 60
                pantalla.blit(fuente_small.render(medallas[i],               True, c_fila),    (col_pos[0], y_f))
                pantalla.blit(fuente_small.render(entrada["ganador"][:12],   True, VERDE_NEON), (col_pos[1], y_f))
                pantalla.blit(fuente_small.render(entrada["rival"][:12],     True, ROJO_NEON),  (col_pos[2], y_f))
                pantalla.blit(fuente_small.render(f"{mins:02d}:{segs:02d}",  True, CYAN_NEON),  (col_pos[3], y_f))
        else:
            sin_datos = fuente.render("¡Sé el primero en el ranking!", True, GRIS_MED)
            pantalla.blit(sin_datos, (ANCHO // 2 - sin_datos.get_width() // 2, 260))

        # Texto parpadeante para empezar
        if (pygame.time.get_ticks() // 600) % 2 == 0:
            play = fuente.render("PULSA ESPACIO PARA JUGAR", True, BLANCO)
            pantalla.blit(play, (ANCHO // 2 - play.get_width() // 2, ALTO - 60))

        pygame.display.flip()
        await asyncio.sleep(0)
        reloj.tick(FPS)


# ─────────────────────────────────────────
#  PANTALLA: FIN DE SET
# ─────────────────────────────────────────
async def pantalla_fin_set(pantalla, reloj, fuente_titulo, fuente, fuente_small,
                           ganador_set: str, color_ganador: tuple,
                           sets_izq: int, sets_der: int,
                           nombre_izq: str, nombre_der: str):
    """Muestra el resultado del set y espera ESPACIO para continuar."""
    while True:
        for evento in pygame.event.get():
            if evento.type == pygame.QUIT:
                pygame.quit(); sys.exit()
            if evento.type == pygame.KEYDOWN:
                if evento.key == pygame.K_SPACE:
                    return
                if evento.key == pygame.K_ESCAPE:
                    pygame.quit(); sys.exit()

        pantalla.fill(NEGRO)
        t1       = fuente_titulo.render(ganador_set,                                   True, color_ganador)
        t2       = fuente.render("GANA EL SET",                                        True, BLANCO)
        sets_txt = fuente.render(f"{nombre_izq}  {sets_izq} - {sets_der}  {nombre_der}", True, AMARILLO)
        t3       = fuente_small.render("ESPACIO para continuar",                        True, GRIS_MED)

        pantalla.blit(t1,       (ANCHO // 2 - t1.get_width()       // 2, ALTO // 2 - 100))
        pantalla.blit(t2,       (ANCHO // 2 - t2.get_width()       // 2, ALTO // 2 - 20))
        pantalla.blit(sets_txt, (ANCHO // 2 - sets_txt.get_width() // 2, ALTO // 2 + 50))
        if (pygame.time.get_ticks() // 500) % 2 == 0:
            pantalla.blit(t3,   (ANCHO // 2 - t3.get_width()       // 2, ALTO // 2 + 110))

        pygame.display.flip()
        await asyncio.sleep(0)
        reloj.tick(FPS)


# ─────────────────────────────────────────
#  PANTALLA: FIN DE PARTIDA
# ─────────────────────────────────────────
async def pantalla_fin_partida(pantalla, reloj, fuente_titulo, fuente, fuente_small,
                               ganador: str, color_ganador: tuple,
                               rival: str, segundos: float):
    """Muestra al ganador de la partida y guarda el ranking."""
    registrar_victoria(ganador, rival, segundos)
    mins = int(segundos) // 60
    segs = int(segundos) % 60
    while True:
        for evento in pygame.event.get():
            if evento.type == pygame.QUIT:
                pygame.quit(); sys.exit()
            if evento.type == pygame.KEYDOWN:
                if evento.key in (pygame.K_SPACE, pygame.K_ESCAPE):
                    return

        pantalla.fill(NEGRO)
        pantalla.blit(fuente_titulo.render("MATEPONG",               True, AMARILLO),
                      (ANCHO // 2 - fuente_titulo.size("MATEPONG")[0]               // 2, 50))
        pantalla.blit(fuente_titulo.render(ganador,                  True, color_ganador),
                      (ANCHO // 2 - fuente_titulo.size(ganador)[0]                  // 2, 150))
        pantalla.blit(fuente.render("¡CAMPEÓN DE LA PARTIDA!",       True, BLANCO),
                      (ANCHO // 2 - fuente.size("¡CAMPEÓN DE LA PARTIDA!")[0]       // 2, 255))
        pantalla.blit(fuente_small.render(f"Tiempo total: {mins:02d}:{segs:02d}", True, CYAN_NEON),
                      (ANCHO // 2 - fuente_small.size(f"Tiempo total: {mins:02d}:{segs:02d}")[0] // 2, 320))
        pantalla.blit(fuente_small.render("¡Resultado guardado en el ranking!", True, VERDE_NEON),
                      (ANCHO // 2 - fuente_small.size("¡Resultado guardado en el ranking!")[0]   // 2, 360))
        if (pygame.time.get_ticks() // 600) % 2 == 0:
            pantalla.blit(fuente_small.render("ESPACIO / ESC para volver al inicio", True, GRIS_MED),
                          (ANCHO // 2 - fuente_small.size("ESPACIO / ESC para volver al inicio")[0] // 2, 430))

        pygame.display.flip()
        await asyncio.sleep(0)
        reloj.tick(FPS)


# ─────────────────────────────────────────
#  JUGAR UN SET  (incluye lógica de potenciadores)
# ─────────────────────────────────────────
async def jugar_set(pantalla, reloj, fuente, fuente_small, fuente_titulo,
              nombre_izq, nombre_der,
              sets_izq, sets_der,
              tiempo_inicio_partida: float) -> str:
    """
    Juega un set completo hasta que alguien alcance PUNTOS_SET.
    Devuelve "izq" o "der" según quién gane el set.

    Sistema de potenciadores:
    - Un relámpago aparece en el campo cada INTERVALO_POWERUP segundos.
    - Si la pelota toca el potenciador en el campo RIVAL, el jugador que
      golpeó la pelota por última vez lo recoge.
    - Al golpear la pelota con el potenciador activo, la velocidad se duplica
      y el potenciador se consume.
    """
    paleta_izq  = Paleta(20,                        VERDE_NEON)
    paleta_der  = Paleta(ANCHO - 20 - PALETA_ANCHO, ROJO_NEON)
    pelota      = Pelota()
    pts_izq     = 0
    pts_der     = 0

    # Estado de potenciadores
    powerup     = PowerupRelampago()
    powerup_izq = False   # el jugador izquierdo tiene el relámpago
    powerup_der = False   # el jugador derecho tiene el relámpago
    ultimo_golpe = None   # "izq" o "der": quién tocó la pelota por última vez

    # Cuenta atrás de 3 antes de empezar
    for cuenta in range(3, 0, -1):
        dibujar_fondo(pantalla)
        dibujar_marcador(pantalla, fuente, fuente_small, fuente_titulo,
                         nombre_izq, nombre_der,
                         pts_izq, pts_der, sets_izq, sets_der,
                         time.time() - tiempo_inicio_partida)
        t = fuente_titulo.render(str(cuenta), True, AMARILLO)
        pantalla.blit(t, (ANCHO // 2 - t.get_width() // 2, ALTO // 2 - 50))
        pygame.display.flip()
        pygame.time.wait(800)

    while True:
        ahora = time.time()

        # ── Eventos ──────────────────────────────────
        for evento in pygame.event.get():
            if evento.type == pygame.QUIT:
                pygame.quit(); sys.exit()
            if evento.type == pygame.KEYDOWN and evento.key == pygame.K_ESCAPE:
                pygame.quit(); sys.exit()

        # ── Controles de paletas ──────────────────────
        teclas = pygame.key.get_pressed()
        paleta_izq.vel = (-PALETA_VEL if teclas[pygame.K_w]
                          else (PALETA_VEL if teclas[pygame.K_s]    else 0))
        paleta_der.vel = (-PALETA_VEL if teclas[pygame.K_UP]
                          else (PALETA_VEL if teclas[pygame.K_DOWN] else 0))

        # ── Mover objetos ─────────────────────────────
        paleta_izq.mover()
        paleta_der.mover()
        pelota.mover()

        # ── Intentar spawnear potenciador ─────────────
        powerup.intentar_spawn(ahora)

        # ── Colisión pelota–paleta izquierda ──────────
        if pelota.rebotar_paleta(paleta_izq, con_powerup=powerup_izq):
            ultimo_golpe = "izq"
            if powerup_izq:
                powerup_izq = False   # el potenciador se consume al usarlo

        # ── Colisión pelota–paleta derecha ────────────
        if pelota.rebotar_paleta(paleta_der, con_powerup=powerup_der):
            ultimo_golpe = "der"
            if powerup_der:
                powerup_der = False   # el potenciador se consume al usarlo

        # ── Colisión pelota–potenciador ───────────────
        if powerup.comprobar_colision(pelota.x, pelota.y) and ultimo_golpe:
            # El potenciador se recoge solo si está en el campo del RIVAL
            pelota_en_campo_izq = pelota.x < ANCHO // 2
            pelota_en_campo_der = pelota.x >= ANCHO // 2

            recoger = False
            if ultimo_golpe == "izq" and pelota_en_campo_der:
                # La pelota lanzada por izquierda golpea el potenciador en el campo derecho
                powerup_izq = True
                recoger     = True
            elif ultimo_golpe == "der" and pelota_en_campo_izq:
                # La pelota lanzada por derecha golpea el potenciador en el campo izquierdo
                powerup_der = True
                recoger     = True

            if recoger:
                powerup.recoger(ahora)

        # ── Comprobar punto ───────────────────────────
        punto = None
        if pelota.x - PELOTA_RADIO < 0:
            pts_der += 1
            punto    = "der"
        elif pelota.x + PELOTA_RADIO > ANCHO:
            pts_izq += 1
            punto    = "izq"

        if punto:
            if pts_izq >= PUNTOS_SET:
                return "izq"
            if pts_der >= PUNTOS_SET:
                return "der"
            # Reinicio entre punto y punto
            pygame.time.wait(500)
            pelota.reiniciar()
            paleta_izq.reiniciar()
            paleta_der.reiniciar()
            ultimo_golpe = None

        # ── Dibujar ───────────────────────────────────
        dibujar_fondo(pantalla)
        dibujar_marcador(pantalla, fuente, fuente_small, fuente_titulo,
                         nombre_izq, nombre_der,
                         pts_izq, pts_der, sets_izq, sets_der,
                         ahora - tiempo_inicio_partida,
                         powerup_izq, powerup_der)
        dibujar_controles(pantalla, fuente_small)
        powerup.dibujar(pantalla)
        paleta_izq.dibujar(pantalla)
        paleta_der.dibujar(pantalla)
        pelota.dibujar(pantalla)

        pygame.display.flip()
        await asyncio.sleep(0)
        reloj.tick(FPS)


# ─────────────────────────────────────────
#  BUCLE PRINCIPAL
# ─────────────────────────────────────────
async def main():
    try:
        # Inicializar solo los módulos necesarios — mixer y joystick no se usan
        # y causan errores NS_ERROR_NOT_AVAILABLE en Firefox/WASM antes de interacción de usuario
        pygame.display.init()
        pygame.font.init()
        pantalla = pygame.display.set_mode((ANCHO, ALTO))
        pygame.display.set_caption("MATEPONG")
        reloj = pygame.time.Clock()

        # Fuentes monospace para aspecto retro arcade
        fuente_titulo = pygame.font.SysFont("Courier New", 60, bold=True)
        fuente        = pygame.font.SysFont("Courier New", 36, bold=True)
        fuente_small  = pygame.font.SysFont("Courier New", 18)

        while True:
            # Pantalla de inicio con ranking
            await pantalla_inicio(pantalla, reloj, fuente_titulo, fuente, fuente_small)

            # Pedir nombres de los jugadores
            nombre_izq = await pedir_nombre(pantalla, reloj, fuente_titulo, fuente, fuente_small, 1, VERDE_NEON)
            nombre_der = await pedir_nombre(pantalla, reloj, fuente_titulo, fuente, fuente_small, 2, ROJO_NEON)

            # Partida: mejor de 3 sets
            sets_izq      = 0
            sets_der      = 0
            tiempo_inicio = time.time()

            while sets_izq < SETS_PARA_GANAR and sets_der < SETS_PARA_GANAR:
                ganador_set = await jugar_set(
                    pantalla, reloj, fuente, fuente_small, fuente_titulo,
                    nombre_izq, nombre_der,
                    sets_izq, sets_der,
                    tiempo_inicio
                )
                if ganador_set == "izq":
                    sets_izq      += 1
                    nombre_gan_set = nombre_izq
                    color_gan_set  = VERDE_NEON
                else:
                    sets_der      += 1
                    nombre_gan_set = nombre_der
                    color_gan_set  = ROJO_NEON

                # Pantalla de fin de set solo si la partida continúa
                if sets_izq < SETS_PARA_GANAR and sets_der < SETS_PARA_GANAR:
                    await pantalla_fin_set(
                        pantalla, reloj, fuente_titulo, fuente, fuente_small,
                        nombre_gan_set, color_gan_set,
                        sets_izq, sets_der, nombre_izq, nombre_der
                    )

            # Fin de la partida
            segundos_totales = time.time() - tiempo_inicio
            if sets_izq >= SETS_PARA_GANAR:
                ganador_final, rival_final, color_final = nombre_izq, nombre_der, VERDE_NEON
            else:
                ganador_final, rival_final, color_final = nombre_der, nombre_izq, ROJO_NEON

            await pantalla_fin_partida(
                pantalla, reloj, fuente_titulo, fuente, fuente_small,
                ganador_final, color_final, rival_final, segundos_totales
            )
            await asyncio.sleep(0)

    except Exception as e:
        import traceback
        print("ERROR EN MATEPONG:", e)
        traceback.print_exc()
        # Mantener vivo el loop para que el error sea visible en el terminal de pygbag
        while True:
            await asyncio.sleep(1)


if __name__ == "__main__":
    asyncio.run(main())
