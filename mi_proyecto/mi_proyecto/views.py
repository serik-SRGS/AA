import itertools
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

MOMENTOS = ("desayuno", "almuerzo", "cena")


def _p(nombre, precio, tipo, kcal=None, prot=None, momento=("almuerzo", "cena"), compartir=False):
    """Un plato. kcal/prot son por porción individual; None = sin dato.
    compartir=True: el precio es de un formato para varias personas (no entra al menú diario)."""
    return {"nombre": nombre, "precio": precio, "tipo": tipo, "kcal": kcal, "prot": prot,
            "momento": list(momento), "compartir": compartir}


# OJO: los valores de kcal y prot (proteínas en gramos) son ESTIMACIONES REFERENCIALES del equipo,
# no mediciones oficiales. Verifíquenlos (tablas nutricionales del local u Open Food Facts) antes
# de presentar, y si no pueden, díganlo en la presentación.
MENUS = {
    "littlecaesars": {"cat": "Pizzería", "alergenos": ["gluten", "lactosa"], "platos": [
        _p("Familiar Queso", 5500, "vegetariano", compartir=True),
        _p("Familiar Pepperoni", 5500, "", compartir=True),
        _p("Italian 3 Cheese", 6500, "vegetariano", compartir=True),
        _p("Extra Pepperoni", 7000, "", compartir=True),
        _p("Familiar Jamón", 8500, "", compartir=True),
        _p("Familiar Super Cheese", 9500, "", compartir=True),
        _p("Familiar Veggie", 9500, "vegetariano", compartir=True),
        _p("Familiar Ultimate Supreme", 10000, "", compartir=True),
        _p("Familiar 3 Meat Treat", 10000, "", compartir=True)]},
    "subway": {"cat": "Sándwiches", "alergenos": ["gluten"], "platos": [
        _p("Sub Vegetariano 15cm", 3200, "vegetariano", 230, 9)]},
    "doggis": {"cat": "Comida rápida", "alergenos": ["gluten", "lactosa"], "platos": [
        _p("Empanadas de Queso x3", 2500, "vegetariano", 750, 25)]},
    "starbucks": {"cat": "Cafetería", "alergenos": ["gluten"], "platos": [
        _p("Muffin Vegano de Arándanos", 3100, "vegano", 380, 5, ("desayuno",))]},
    "mcdonald": {"cat": "Comida rápida", "alergenos": [], "platos": [
        _p("McPapas Medianas + Ensalada Verde", 2900, "vegano", 380, 5)]},
    "pedrojuan": {"cat": "Comida rápida", "alergenos": [], "platos": [
        _p("Papas Fritas Familiar con Salsa Ajo", 3400, "vegetariano", compartir=True)]},
    "elfito": {"cat": "Restaurante", "alergenos": ["lactosa"], "platos": [
        _p("Plato Ejecutivo Vegetariano del Día", 3800, "vegetariano", 650, 20, ("almuerzo",))]},
}

# Locales SIN CONFIRMAR: no se usan en la app. Si verifican que existen (y sus platos/precios),
# muévanlos arriba a MENUS (usando _p(...) y con kcal/prot/momento) y agréguenlos a UBICACIONES.
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


def _entero(valor, defecto):
    try:
        return int(valor)
    except (TypeError, ValueError):
        return defecto


def _cumple_tipo(menu, plato, tipo):
    if not tipo:
        return True
    if tipo == 'sin_gluten':  # el local no declara gluten entre sus alérgenos
        return 'gluten' not in menu['alergenos']
    return plato['tipo'] == tipo


def _platos_filtrados(menu, presupuesto, tipo, alergeno, momento):
    """Platos de un local que cumplen presupuesto, dieta, alérgeno y momento del día."""
    if alergeno and alergeno in menu['alergenos']:
        return []
    return [p for p in menu['platos']
            if p['precio'] <= presupuesto
            and _cumple_tipo(menu, p, tipo)
            and (not momento or momento in p['momento'])]


def buscar_alternativas(request):
    presupuesto_max = _entero(request.GET.get('presupuesto', 10000), 10000)
    tipo_filtro = request.GET.get('tipo', '').strip().lower()
    alergeno_filtro = request.GET.get('alergeno', '').strip().lower()
    momento_filtro = request.GET.get('momento', '').strip().lower()

    resultados = []
    for item in obtener_locales():
        menu = _menu_de(item['lugar'])
        if not menu:
            continue  # sin menú y precio cargados no se muestra
        platos = _platos_filtrados(menu, presupuesto_max, tipo_filtro, alergeno_filtro, momento_filtro)
        if not platos:
            continue
        platos.sort(key=lambda p: p['precio'])
        con_dato = next((p for p in platos if p['kcal'] is not None), None)

        resultados.append({
            'id': item['id'], 'lugar': item['lugar'], 'direccion': item['direccion'],
            'latitud': item['lat'], 'longitud': item['lon'],
            'plato': " · ".join(f"{p['nombre']} {_precio(p['precio'])}" for p in platos[:3]),
            'platos': [{'nombre': p['nombre'], 'precio': p['precio'], 'kcal': p['kcal'],
                        'prot': p['prot'], 'compartir': p['compartir']} for p in platos[:3]],
            'precio': platos[0]['precio'], 'tipo_alimentacion': menu['cat'],
            'info_nutricional': ({'calorias': con_dato['kcal'], 'proteinas': con_dato['prot']}
                                 if con_dato else None),
        })

    return JsonResponse({'status': 'ok', 'resultados': resultados})


def menu_diario(request):
    """Calculadora de menú diario: elige un plato para desayuno, almuerzo y cena que cumpla
    presupuesto y dieta, y que deje las calorías totales lo más cerca posible del objetivo."""
    presupuesto = _entero(request.GET.get('presupuesto', 10000), 10000)
    objetivo = _entero(request.GET.get('kcal', 2000), 2000)
    tipo = request.GET.get('tipo', '').strip().lower()
    alergeno = request.GET.get('alergeno', '').strip().lower()

    candidatos = {m: [] for m in MOMENTOS}
    for item in obtener_locales():
        menu = _menu_de(item['lugar'])
        if not menu:
            continue
        for p in _platos_filtrados(menu, presupuesto, tipo, alergeno, ''):
            if p['compartir'] or p['kcal'] is None:
                continue  # sin porción individual o sin dato nutricional no se puede sumar
            for m in p['momento']:
                if m in candidatos:
                    candidatos[m].append({
                        'lugar': item['lugar'], 'direccion': item['direccion'],
                        'plato': p['nombre'], 'precio': p['precio'], 'kcal': p['kcal'], 'prot': p['prot']})

    disponibles = [m for m in MOMENTOS if candidatos[m]]
    faltan = [m for m in MOMENTOS if not candidatos[m]]

    # presupuesto mínimo para armar el día: el plato más barato de cada momento disponible
    minimo = sum(min(c['precio'] for c in candidatos[m]) for m in disponibles)

    mejor = None
    if disponibles:
        for combo in itertools.product(*(candidatos[m] for m in disponibles)):
            precio = sum(c['precio'] for c in combo)
            if precio > presupuesto:
                continue
            kcal = sum(c['kcal'] for c in combo)
            repetidos = len(combo) - len({c['plato'] for c in combo})  # prefiere platos distintos
            clave = (repetidos, abs(objetivo - kcal), precio)
            if mejor is None or clave < mejor[0]:
                mejor = (clave, combo)

    comidas = {m: None for m in MOMENTOS}
    totales = {'precio': 0, 'kcal': 0, 'prot': 0}
    if mejor:
        for m, c in zip(disponibles, mejor[1]):
            comidas[m] = c
        totales = {'precio': sum(c['precio'] for c in mejor[1]),
                   'kcal': sum(c['kcal'] for c in mejor[1]),
                   'prot': sum(c['prot'] or 0 for c in mejor[1])}

    return JsonResponse({
        'status': 'ok', 'comidas': comidas, 'totales': totales, 'objetivo_kcal': objetivo,
        'diferencia_kcal': objetivo - totales['kcal'], 'presupuesto': presupuesto,
        'sin_opciones': faltan, 'hay_menu': mejor is not None, 'presupuesto_minimo': minimo,
    })
