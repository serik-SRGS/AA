import json
import re
import urllib.parse
import urllib.request
from pathlib import Path

from django.http import JsonResponse
from django.shortcuts import render

CACHE_OSM = Path(__file__).resolve().parent / 'osmcache.json'
CAMPUS = (-33.4985, -70.6165)  
RADIO_M = 1500                  

MENUS = {
    "littlecaesars": {"cat": "Pizzería", "alergenos": ["gluten", "lactosa"], "platos": [
        {"nombre": "Familiar Queso", "precio": 5500, "tipo": "vegetariano"},
        {"nombre": "Familiar Pepperoni", "precio": 5500, "tipo": ""},
        {"nombre": "Italian 3 Cheese", "precio": 6500, "tipo": "vegetariano"},
        {"nombre": "Extra Pepperoni", "precio": 7000, "tipo": ""},
        {"nombre": "Familiar Jamón", "precio": 8500, "tipo": ""},
        {"nombre": "Familiar Super Cheese", "precio": 9500, "tipo": ""},
        {"nombre": "Familiar Veggie", "precio": 9500, "tipo": "vegetariano"},
        {"nombre": "Familiar Ultimate Supreme", "precio": 10000, "tipo": ""},
        {"nombre": "Familiar 3 Meat Treat", "precio": 10000, "tipo": ""}]},
    "subway": {"cat": "Sándwiches", "alergenos": ["gluten"], "platos": [
        {"nombre": "Sub Vegetariano 15cm", "precio": 3200, "tipo": "vegetariano"}]},
    "doggis": {"cat": "Comida rápida", "alergenos": ["gluten", "lactosa"], "platos": [
        {"nombre": "Empanadas de Queso x3", "precio": 2500, "tipo": "vegetariano"}]},
    "starbucks": {"cat": "Cafetería", "alergenos": ["gluten"], "platos": [
        {"nombre": "Muffin Vegano de Arándanos", "precio": 3100, "tipo": "vegano"}]},
    "mcdonald": {"cat": "Comida rápida", "alergenos": [], "platos": [
        {"nombre": "McPapas Medianas + Ensalada Verde", "precio": 2900, "tipo": "vegano"}]},
    "pedrojuan": {"cat": "Comida rápida", "alergenos": [], "platos": [
        {"nombre": "Papas Fritas Familiar con Salsa Ajo", "precio": 3400, "tipo": "vegetariano"}]},
    "elfito": {"cat": "Restaurante", "alergenos": ["lactosa"], "platos": [
        {"nombre": "Plato Ejecutivo Vegetariano del Día", "precio": 3800, "tipo": "vegetariano"}]},
}

# Locales SIN CONFIRMAR: no se usan en la app. Si verifican que existen (y sus platos/precios),
# muévanlos arriba a MENUS y agréguenlos a UBICACIONES con sus coordenadas.
POR_VERIFICAR = {
    "donerkebab": {"cat": "Kebab", "alergenos": ["gluten"], "platos": [
        {"nombre": "Wrap de Falafel con Salsa de Sésamo", "precio": 3900, "tipo": "vegano"}]},
    "pamefood": {"cat": "Ensaladas", "alergenos": [], "platos": [
        {"nombre": "Ensalada Completa de Quínoa y Palta", "precio": 3600, "tipo": "vegano"}]},
    "bicicleta": {"cat": "Restaurante", "alergenos": [], "platos": [
        {"nombre": "Tabla Vegana de Hummus y Verduras", "precio": 4800, "tipo": "vegano"}]},
    "piccola": {"cat": "Restaurante italiano", "alergenos": ["gluten"], "platos": [
        {"nombre": "Minestrone de Verduras Frescas", "precio": 4200, "tipo": "vegetariano"}]},
    "mardoqueo": {"cat": "Fuente de soda", "alergenos": [], "platos": [
        {"nombre": "Papas Fritas Grandes + Bebida", "precio": 4000, "tipo": "vegano"}]},
    "dgustar": {"cat": "Pastelería", "alergenos": ["mani"], "platos": [
        {"nombre": "Tarta de Avena y Frutas Sin Lactosa", "precio": 2900, "tipo": "sin_gluten"}]},
}

# Locales que están en MENUS pero NO en OpenStreetMap (osmcache.json).
# Para que aparezcan en el mapa, completen lat y lon de cada uno:
#   Google Maps -> clic derecho sobre el local -> clic en las coordenadas (se copian).
# Mientras lat/lon estén en None, el local NO se muestra (es lo que pasaba antes).
UBICACIONES = {
    "doggis":     {"nombre": "Doggis",              "direccion": "Cerca del campus", "lat": -33.48662815087975, "lon": -70.61639128417969},
    "mcdonald":   {"nombre": "McDonald's",          "direccion": "Cerca del campus", "lat": -33.508703795950304, "lon": -70.61639128417969},
    "pedrojuan":  {"nombre": "Pedro, Juan y Diego", "direccion": "Cerca del campus", "lat": -33.516321810109865, "lon": -70.59782797343966},
}


def _normal(s):
    s = s.lower()
    for a, b in zip("áéíóúüñ", "aeiouun"):
        s = s.replace(a, b)
    return re.sub(r'[^a-z0-9]', '', s)


def _precio(p):
    return "$" + f"{p:,}".replace(",", ".")


def obtener_cercanos():
    if CACHE_OSM.exists():
        return json.loads(CACHE_OSM.read_text(encoding='utf-8'))
    lat, lon = CAMPUS
    consulta = f"""
    [out:json][timeout:25];
    (
      node["amenity"~"^(restaurant|cafe|fast_food|food_court)$"](around:{RADIO_M},{lat},{lon});
      way["amenity"~"^(restaurant|cafe|fast_food|food_court)$"](around:{RADIO_M},{lat},{lon});
    );
    out center tags;
    """
    try:
        req = urllib.request.Request(
            "https://overpass-api.de/api/interpreter",
            data=urllib.parse.urlencode({"data": consulta}).encode(),
            headers={"User-Agent": "geofit-proyecto-universitario"},
        )
        with urllib.request.urlopen(req, timeout=40) as r:
            elementos = json.load(r).get("elements", [])
    except Exception:
        return []  

    lugares, vistos = [], set()
    for el in elementos:
        tags = el.get("tags", {})
        nombre = tags.get("name")
        if not nombre:
            continue
        punto = (el.get("lat"), el.get("lon")) if el["type"] == "node" else (
            el.get("center", {}).get("lat"), el.get("center", {}).get("lon"))
        if punto[0] is None:
            continue
        clave = (nombre.lower(), round(punto[0], 4), round(punto[1], 4))
        if clave in vistos:
            continue
        vistos.add(clave)
        lugares.append({
            "id": 1000 + len(lugares), "lugar": nombre,
            "direccion": f"{tags.get('addr:street', '')} {tags.get('addr:housenumber', '')}".strip() or "Cerca del campus",
            "lat": round(punto[0], 6), "lon": round(punto[1], 6),
        })
    CACHE_OSM.write_text(json.dumps(lugares, ensure_ascii=False, indent=2), encoding='utf-8')
    return lugares


def obtener_locales():
    """Locales de OpenStreetMap + los de UBICACIONES que tengan coordenadas."""
    lugares = list(obtener_cercanos())
    nombres = [_normal(l['lugar']) for l in lugares]
    for i, (clave, u) in enumerate(UBICACIONES.items()):
        if u['lat'] is None or u['lon'] is None:
            continue  # sin coordenadas no se puede dibujar
        if any(clave in n for n in nombres):
            continue  # ya vino desde OpenStreetMap
        lugares.append({"id": 2000 + i, "lugar": u['nombre'],
                        "direccion": u['direccion'], "lat": u['lat'], "lon": u['lon']})
    return lugares


def _menu_de(nombre):
    n = _normal(nombre)
    for clave, menu in MENUS.items():
        if clave in n:
            return menu
    return None


def index(request):
    return render(request, 'index.html')


def buscar_alternativas(request):
    try:
        presupuesto_max = int(request.GET.get('presupuesto', 10000))
    except ValueError:
        presupuesto_max = 10000
    tipo_filtro = request.GET.get('tipo', '').strip().lower()
    alergeno_filtro = request.GET.get('alergeno', '').strip().lower()

    resultados = []
    for item in obtener_locales():
        menu = _menu_de(item['lugar'])
        if not menu:
            continue  # sin menú y precio cargados no se muestra
        if alergeno_filtro and alergeno_filtro in menu['alergenos']:
            continue
        platos = [p for p in menu['platos']
                  if p['precio'] <= presupuesto_max and (not tipo_filtro or p['tipo'] == tipo_filtro)]
        if not platos:
            continue
        platos.sort(key=lambda p: p['precio'])

        resultados.append({
            'id': item['id'], 'lugar': item['lugar'], 'direccion': item['direccion'],
            'latitud': item['lat'], 'longitud': item['lon'],
            'plato': " · ".join(f"{p['nombre']} {_precio(p['precio'])}" for p in platos[:3]),
            'precio': platos[0]['precio'], 'tipo_alimentacion': menu['cat'],
            'info_nutricional': None,
        })

    return JsonResponse({'status': 'ok', 'resultados': resultados})