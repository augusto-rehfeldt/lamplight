# Lamplight

Juego de escritura e investigación: una biblioteca en pixel art con 1.200 libros de
Project Gutenberg, una campaña de cartas entre 1630 y 1930 y el cliente nativo en
Godot. Antes vivía dentro de `article-writer`; se separó el 2026-09-23.

**Dependencia.** La generación de textos reutiliza el motor de `../article-writer`
(`llm`, `pipeline`, `research`, `style`): `game_server.py` lo agrega a `sys.path` y
carga su `.env` (un `.env` propio en esta carpeta tiene prioridad). Cambiar la API
pública de esos módulos exige correr también las pruebas de este proyecto.

```bash
python -B -m unittest test_game_campaign test_game_library test_game_native test_lamplight_ai
```

Las partidas, descargas y checkpoints quedan en `output/` (ignorado por git).

## Lamplight: biblioteca inglesa y cartas a través del tiempo

```bash
python game_server.py
```

Abrí `http://127.0.0.1:8765` y elegí **English book library**. Incluye **1.200
ediciones completas en inglés**, con al menos 150 títulos por estante: ciencias,
filosofía, literatura, historia, política y religión. Los estantes pueden solaparse.
El catálogo se construye desde los [metadatos oficiales de Project Gutenberg](https://www.gutenberg.org/ebooks/offline_catalogs.html)
y solo acepta ediciones cuyo registro declara dominio público en EE. UU. Esa
declaración no establece los derechos en otros países.

Buscá por título, autor o tema; llevá hasta 12 libros al ordenador. El texto completo
se descarga al abrirlo y queda en `output/lamplight/books/` para leer sin conexión.
El lector tiene búsqueda dentro del libro, capítulos detectados, posición guardada,
tipografía, tamaño y tema nocturno. La paginación del lector no corresponde a la de
la edición impresa. Las sinopsis del catálogo pueden ser generadas por Gutenberg;
el dossier de escritura recibe el texto completo descargado.

El ordenador conserva los siete formatos de `pipeline.py`, con escritura automática,
guiada o manual. La guía se detiene en los puntos de decisión del pipeline. El editor
guarda manuscritos localmente, admite Markdown y permite exportar `.md`. Los cinco
residentes ofrecen comentarios con un modelo compartido o uno por personaje. Sus
consultas reciben muestras de los libros y hasta 60.000 caracteres del manuscrito;
sus respuestas no sustituyen automáticamente tu texto.

En **Settings** podés ajustar proveedores, respaldos, modelos y un presupuesto local
mensual de llamadas. Los proveedores personalizados usan una API compatible con
chat completions: configurá su URL, modelos y el nombre de una variable de entorno
para su clave; agregá esa variable a `.env` y reiniciá el servidor. Las claves no se
envían al navegador. Las métricas cuentan llamadas lógicas locales y estiman tokens;
no representan el saldo ni la cuota de una suscripción externa. Los reintentos
del proveedor pueden sumar consumo adicional. Se ejecuta una tarea de IA por vez.

WASD/flechas para caminar, E para interactuar, o clic para desplazarse. También hay
accesos directos a cada función. El sonido ambiental es opcional; la cafetera tiene
un minijuego y Miso el gato tiene tres premios escondidos. Todo el pixel art se
dibuja localmente con canvas, sin descargar recursos visuales externos.

La biblioteca inglesa se usa fuera de la campaña histórica; cada colección conserva
su carrito de fuentes. Las ediciones del archivo no se suministran a los residentes
de una época ni cuentan para los encargos históricos. Tu campaña anterior se conserva.

```bash
python game_catalog.py                    # reconstruir catálogo inglés desde el RDF oficial
python -m unittest test_game_library test_game_campaign -v
python check_game_browser.py              # control visual opcional con Playwright instalado
```

Las comprobaciones de integración usan respuestas simuladas y partidas temporales;
no consumen las APIs configuradas. Los checkpoints de generación se conservan en
`output/lamplight/jobs/`. Si se reinicia el servidor durante una generación, su
estado queda interrumpido y los archivos permanecen disponibles para recuperación.

### Campaña histórica

```bash
python game_server.py --port 8765
```

Abrí `http://127.0.0.1:8765` y elegí **Letters across time** (atajo **6**).
La campaña tiene controles en inglés y español. Empieza en 1630 y avanza en
saltos de 50 años hasta 1930. El ordenador y su conexión a los modelos son la
excepción fantástica; las fuentes y los corresponsales se restringen en el servidor.

Estudiá las notas de la biblioteca, llevá fuentes al escritorio y escribí un
manuscrito. Los turnos de copista dan monedas y papel sin consumir una API. Cada
época exige textos más largos, más fuentes y, desde 1680, discutir una carta
recibida. Los marcadores `[B1]`, `[B2]`, etc. identifican las notas; el correo muestra
su marcador `[L…]`. Podés añadirlos desde la campaña y desarrollar el argumento
en el editor. Entregar un encargo da monedas y prestigio. Reuní los requisitos
de la máquina, recogé el correo pendiente y saltá a la siguiente época.

El correo cobra franqueo y papel. Las respuestas tardan entre uno y cuatro días
del juego, admiten réplicas y solo permiten escribir a corresponsales activos
en esa época. Son **debates ficticios con respuestas preparadas**, no cartas
auténticas. **Enviar con respuesta de IA** ofrece, además, una respuesta al
argumento concreto con el modelo configurado para los residentes. Recibe solo
notas de la época y cartas anteriores entregadas; conserva la demora postal y
no cobra franqueo si falla. Un filtro rechaza años futuros explícitos y respuestas
en el idioma equivocado, pero no puede detectar todos los anacronismos. Los habitantes ficticios y el
escritorio sí pueden usar los proveedores configurados; sus instrucciones y su
contexto se limitan a la época, aunque eso no garantiza que un modelo nunca
cometa un anacronismo. La campaña completa se puede jugar sin claves ni red.

El primer catálogo histórico contiene **14 notas de estudio bilingües originales**,
dos nuevas por época, no catorce libros completos. Cada una enlaza la obra o
documentación de referencia. Las páginas externas son referencias modernas,
fuera de la ficción; no se descargan ni se pasan a los personajes. Por ejemplo,
la ficha de [Frankenstein de 1818](https://www.gutenberg.org/ebooks/41445)
distingue esa edición de la de 1831, y la de
[Relativity](https://www.gutenberg.org/ebooks/5001) identifica la traducción de 1920.
El catálogo Gutenberg anterior y sus descargas se conservan en disco: sus
ediciones no entran en la campaña mientras no se hayan fechado individualmente.
Una etiqueta de dominio público en EE. UU. no significa disponibilidad histórica
ni permiso universal; [Gutenberg explica sus condiciones territoriales](https://www.gutenberg.org/policy/permission.html).

La economía, los plazos y los lugares son reglas ficticias. La aceptación de
encargos comprueba extensión, referencias, recursos y pagos duplicados: **no
certifica calidad literaria, exactitud histórica ni originalidad**. No publica
nada fuera del juego. Los avances se guardan de forma atómica en
`output/lamplight/campaign.json`, separados de manuscritos y preferencias anteriores.
Las pruebas usan directorios temporales y no modifican tu partida.

```bash
python -m unittest test_game_campaign -v  # campaña completa y límites HTTP, sin red externa
python check_game_browser.py            # interfaz; requiere Playwright y su Chromium ya instalados
```

## Lamplight en Godot

El desarrollo del juego continúa en el proyecto nativo `godot/project.godot`.
Desde esta carpeta, ejecutá `rtk python run_lamplight.py --editor` para abrir Godot
y presioná F5 para jugar. `rtk python run_lamplight.py` inicia el juego directamente.
El launcher mantiene el servicio local de Python y las partidas de cada modo.
Si falta el motor, usá `rtk python run_lamplight.py --setup`.

El inicio ya no consume llamadas para comprobar HyperCharm antes de abrir la
ventana: `--hyper` y `LAMPLIGHT_AUTO_HYPER=1` solo cargan la configuración. La prueba
se inicia desde **AI setup**, con actividad y tiempo transcurrido visibles.
El ordenador y el escritorio ofrecen cinco pasos guardados —pregunta, evidencia,
esquema, borrador y revisión— con comentarios de IA y aprobación del jugador entre
pasos. **AI usage** muestra solicitudes, errores, tiempos y tokens; separa los
datos informados por el proveedor de las estimaciones y no representa su saldo.

La primera base nativa tiene movimiento, colisiones, diálogos, lectura, escritura
y partidas separadas. Las partidas anteriores del navegador se conservan; su
migración todavía está pendiente. Consultá [el progreso nativo](docs/M1_NATIVE.md)
para ver lo implementado, las comprobaciones y los próximos pasos.
