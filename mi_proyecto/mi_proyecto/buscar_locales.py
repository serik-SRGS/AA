import csv
import io
import json
import re
import shutil
import sys
import urllib.parse
import urllib.request
from pathlib import Path

RAIZ = Path(__file__).resolve().parent
CARPETA = RAIZ if (RAIZ / 'views.py').exists() else RAIZ / 'mi_proyecto'
LOCALES = CARPETA / 'locales.csv'
MENUS = CARPETA / 'menus.csv'

CAMPUS = (-33.4985, -70.6165)           # USM San Joaquín (aproximado)
RADIO = int(sys.argv[1]) if len(sys.argv) > 1 else 1500   # metros
SERVIDORES = ["https://overpass-api.de/api/interpreter",
              "https://overpass.kumi.systems/api/interpreter"]

AMENITY = {"restaurant": "Restaurante", "cafe": "Cafetería",
           "fast_food": "Comida rápida", "food_court": "Patio de comidas"}
CUISINE = {"pizza": "Pizzería", "sushi": "Sushi", "burger": "Hamburguesas",
           "chicken": "Pollería", "sandwich": "Sándwiches", "coffee_shop": "Cafetería",
           "chilean": "Comida chilena", "chinese": "Comida china", "peruvian": "Comida peruana",
           "italian": "Comida italiana", "japanese": "Comida japonesa", "mexican": "Comida mexicana",
           "empanada": "Empanadas", "hot_dog": "Completos", "kebab": "Kebab",
           "ice_cream": "Heladería", "bakery": "Panadería", "vegetarian": "Comida vegetariana",
           "vegan": "Comida vegana"}


def _normal(s):
    s = (s or '').lower()
    for a, b in zip("áéíóúüñ", "aeiouun"):
        s = s.replace(a, b)
    return re.sub(r'[^a-z0-9]', '', s)


def nombres_de(ruta):
    """Nombres (primera columna) de un CSV, normalizados."""
    if not ruta.exists():
        return set()
    texto = ruta.read_text(encoding='utf-8-sig')
    if not texto.strip():
        return set()
    primera = texto.splitlines()[0]
    delim = ';' if primera.count(';') > primera.count(',') else ','
    filas = list(csv.reader(io.StringIO(texto), delimiter=delim))
    return {_normal(f[0]) for f in filas[1:] if f and f[0].strip()}


def consultar():
    lat, lon = CAMPUS
    consulta = f"""
    [out:json][timeout:30];
    (
      node["amenity"~"^(restaurant|cafe|fast_food|food_court)$"](around:{RADIO},{lat},{lon});
      way["amenity"~"^(restaurant|cafe|fast_food|food_court)$"](around:{RADIO},{lat},{lon});
    );
    out center tags;
    """
    for url in SERVIDORES:
        try:
            req = urllib.request.Request(
                url, data=urllib.parse.urlencode({"data": consulta}).encode(),
                headers={"User-Agent": "geofit-proyecto-universitario"})
            with urllib.request.urlopen(req, timeout=60) as r:
                return json.load(r).get("elements", [])
        except Exception as e:
            print(f"No respondió {url}: {e}")
    sys.exit("No se pudo consultar OpenStreetMap. Revisa la conexión y reintenta.")


def main():
    existentes = nombres_de(LOCALES)
    elementos = consultar()

    nuevos, vistos = [], set()
    for el in elementos:
        tags = el.get("tags", {})
        nombre = tags.get("name")
        if not nombre:
            continue
        n = _normal(nombre)
        if len(n) < 2 or any(x and (x in n or n in x) for x in existentes):
            continue  # ya lo tienes
        punto = (el.get("lat"), el.get("lon")) if el["type"] == "node" else (
            el.get("center", {}).get("lat"), el.get("center", {}).get("lon"))
        if punto[0] is None:
            continue
        clave = (n, round(punto[0], 4), round(punto[1], 4))
        if clave in vistos:
            continue
        vistos.add(clave)

        cocina = tags.get("cuisine", "").split(";")[0].strip()
        categoria = CUISINE.get(cocina) or AMENITY.get(tags.get("amenity"), "Comida")
        direccion = f"{tags.get('addr:street', '')} {tags.get('addr:housenumber', '')}".strip() or "Cerca del campus"
        dist = ((punto[0] - CAMPUS[0]) * 111) ** 2 + ((punto[1] - CAMPUS[1]) * 93) ** 2
        nuevos.append((dist, nombre, categoria, direccion, round(punto[0], 6), round(punto[1], 6)))

    nuevos.sort()
    if not nuevos:
        print("No hay locales nuevos dentro del radio.")
        return

    if LOCALES.exists():
        shutil.copy(LOCALES, str(LOCALES) + '.bak')   # copia de seguridad
        contenido = LOCALES.read_bytes()
        if contenido and not contenido.endswith(b'\n'):
            with open(LOCALES, 'ab') as f:
                f.write(b'\n')
    else:
        LOCALES.write_text("local,categoria,direccion,lat,lon\n", encoding='utf-8')

    with open(LOCALES, 'a', newline='', encoding='utf-8') as f:
        w = csv.writer(f)
        for _, nombre, categoria, direccion, lat, lon in nuevos:
            w.writerow([nombre, categoria, direccion, lat, lon])

    con_menu = nombres_de(MENUS)
    print(f"\nSe agregaron {len(nuevos)} locales a locales.csv (radio {RADIO} m).")
    print("Aparecen en la página cuando tengan menú en menus.csv.\n")
    print("Locales nuevos, del más cercano al más lejano (el enlace abre Google Maps para ver su carta):\n")
    for _, nombre, categoria, direccion, lat, lon in nuevos:
        marca = "" if _normal(nombre) not in con_menu else "  [ya tiene menú]"
        print(f"- {nombre} ({categoria}) · {direccion}{marca}")
        print(f"  https://www.google.com/maps/search/?api=1&query={lat},{lon}")


if __name__ == "__main__":
    main()