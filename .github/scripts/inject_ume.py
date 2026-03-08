"""
Inyecta el handler UME en docs/index.html después de cada build de pygbag.
pygbag espera que window.MM.UME sea true para arrancar el juego.
Sin este handler, el juego se queda en bucle esperando interacción.
"""

UME_HANDLER = (
    "    // MATEPONG: crear AudioContext en el mismo evento click (requisito del navegador)\n"
    "    // y activar MM.UME para que pygbag arranque\n"
    "    document.addEventListener('click', function handler() {\n"
    "        var ctx = new (window.AudioContext || window.webkitAudioContext)();\n"
    "        ctx.resume();\n"
    "        if (window.MM) {\n"
    "            window.MM.UME = true;\n"
    "            if (window.MM.audio) window.MM.audio = ctx;\n"
    "        }\n"
    "    }, false);\n\n"
    "    // También en el #infobox directamente (por si el evento no sube al document)\n"
    "    window.addEventListener('load', function() {\n"
    "        var infobox = document.getElementById('infobox');\n"
    "        if (infobox) {\n"
    "            infobox.onclick = function() {\n"
    "                var ctx = new (window.AudioContext || window.webkitAudioContext)();\n"
    "                ctx.resume();\n"
    "                if (window.MM) window.MM.UME = true;\n"
    "            };\n"
    "        }\n"
    "    });\n\n"
)

# Intentar el marcador de 0.9.3 primero, luego el de 0.9.2
MARKER = "globalThis.__canvas_resized"
MARKER_092 = "async function custom_onload"

with open("docs/index.html", "r") as f:
    html = f.read()

if "addEventListener('click'" not in html:
    if MARKER in html:
        marker = MARKER
    elif MARKER_092 in html:
        marker = MARKER_092
    else:
        print("ERROR: marcador no encontrado en index.html")
        raise SystemExit(1)
    html = html.replace(marker, UME_HANDLER + marker, 1)
    with open("docs/index.html", "w") as f:
        f.write(html)
    print(f"UME handler inyectado correctamente (marcador: {marker[:30]}...)")
else:
    print("UME handler ya presente, sin cambios")
