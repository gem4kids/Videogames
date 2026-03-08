"""
Inyecta el handler UME en docs/index.html después de cada build de pygbag.
pygbag espera que window.MM.UME sea true para arrancar el juego.
Sin este handler, el juego se queda en bucle esperando interacción.
"""

UME_HANDLER = (
    "    // MATEPONG: activar UME al primer clic/toque para que pygbag arranque\n"
    "    document.addEventListener('click', function() {\n"
    "        if (window.MM) window.MM.UME = true;\n"
    "    }, {once: true});\n"
    "    document.addEventListener('touchstart', function() {\n"
    "        if (window.MM) window.MM.UME = true;\n"
    "    }, {once: true});\n\n"
)

MARKER = "globalThis.__canvas_resized"

with open("docs/index.html", "r") as f:
    html = f.read()

if "window.MM.UME" not in html:
    if MARKER not in html:
        print("ERROR: marcador no encontrado en index.html")
        raise SystemExit(1)
    html = html.replace(MARKER, UME_HANDLER + MARKER)
    with open("docs/index.html", "w") as f:
        f.write(html)
    print("UME handler inyectado correctamente")
else:
    print("UME handler ya presente, sin cambios")
