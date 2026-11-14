import csv
import io
import itertools
import json
import re
import time
import urllib.parse
import urllib.request
from pathlib import Path

from django.http import JsonResponse
from django.shortcuts import render

BASE = Path(__file__).resolve().parent
CSV_LOCALES = BASE / 'locales.csv'
CSV_MENUS = BASE / 'menus.csv'
CACHE_GEO = BASE / 'geocache.json'
VIEWBOX = "-70.75,-33.40,-70.50,-33.60"   # zona amplia de Santiago
MOMENTOS = ("desayuno", "almuerzo", "cena")


def _normal(s):
    s = (s or '').lower()
    for a, b in zip("áéíóúüñ", "aeiouun"):
        s = s.replace(a, b)
    return re.sub(r'[^a-z0-9]', '', s)


def _num(s):
    s = (s or '').strip().replace(',', '.')
    if not s:
        return None
    try:
        return float(s)
    except ValueError:
        return None


def _precio(p):
    return "$" + f"{p:,}".replace(",", ".")


def _lista(valor):
    return [x.strip().lower() for x in (valor or '').split('|') if x.strip()]


def _lista_param(valor):
    return [a.strip().lower() for a in (valor or '').split(',') if a.strip()]


def _entero(valor, defecto):
    try:
        return int(valor)
    except (TypeError, ValueError):
        return defecto


def _leer_csv(ruta):
    if not ruta.exists():
        return []
    texto = ruta.read_text(encoding='utf-8-sig')
    if not texto.strip():
        return []
    primera = texto.splitlines()[0]
    delim = ';' if primera.count(';') > primera.count(',') else ','
    filas = []
    for row in csv.DictReader(io.StringIO(texto), delimiter=delim):
        filas.append({(k or '').strip().lower(): (v or '').strip()
                      for k, v in row.items() if k is not None and isinstance(v, str)})
    return filas


def _coords_fila(row):
    lat, lon = _num(row.get('lat')), _num(row.get('lon'))
    if lat is None and lon is None:
        # permite pegar "-33.49, -70.61" completo en la columna lat
        partes = re.findall(r'-?\d+\.\d+', row.get('lat') or '')
        if len(partes) == 2:
            lat, lon = float(partes[0]), float(partes[1])
    return lat, lon


def cargar_menus():
    """menus.csv -> {nombre normalizado del local: [platos]}"""
    menus = {}
    for row in _leer_csv(CSV_MENUS):
        local, plato, precio = row.get('local'), row.get('plato'), _num(row.get('precio'))
        if not local or not plato or precio is None:
            continue
        cal, prot = _num(row.get('kcal')), _num(row.get('prot'))
        al = (row.get('alergenos') or '').lower()
        # vacío = alérgenos NO declarados; "ninguno" = declarado sin alérgenos
        alergenos = None if not al else ([] if al in ('ninguno', 'ninguna', 'no') else _lista(al))
        momento = [m for m in _lista(row.get('momento')) if m in MOMENTOS] or ['almuerzo', 'cena']
        menus.setdefault(_normal(local), []).append({
            'nombre': plato, 'precio': int(precio), 'tipo': (row.get('tipo') or '').lower(),
            'kcal': int(cal) if cal is not None else None, 'prot': prot,
            'momento': momento,
            'compartir': (row.get('compartir') or '').lower() in ('si', 'sí', '1', 'true', 'x', 'yes'),
            'alergenos': alergenos,
        })
    return menus


# ---------- Si una sucursal no trae lat/lon se busca por dirección (se guarda en caché) ----------
def _nominatim(q):
    params = urllib.parse.urlencode({
        "q": q + ", Santiago, Chile", "format": "json", "limit": 1,
        "viewbox": VIEWBOX, "bounded": 1,
    })
    req = urllib.request.Request(
        "https://nominatim.openstreetmap.org/search?" + params,
        headers={"User-Agent": "geofit-proyecto-universitario"},
    )
    with urllib.request.urlopen(req, timeout=15) as r:
        datos = json.load(r)
    time.sleep(1.1)
    if datos:
        return [round(float(datos[0]["lat"]), 6), round(float(datos[0]["lon"]), 6)]
    return None


def completar_coordenadas(locales):
    cache = json.loads(CACHE_GEO.read_text(encoding='utf-8')) if CACHE_GEO.exists() else {}
    cambio = False
    for e in locales:
        if e['lat'] is not None or not e['direccion'] or _normal(e['direccion']) == 'cercadelcampus':
            continue
        clave = _normal(e['lugar']) + '|' + _normal(e['direccion'])
        if clave not in cache:
            try:
                cache[clave] = _nominatim(f"{e['lugar']}, {e['direccion']}") or _nominatim(e['direccion'])
            except Exception:
                continue  # error de red: se reintenta la próxima vez
            cambio = True
        if cache.get(clave):
            e['lat'], e['lon'] = cache[clave]
    if cambio:
        CACHE_GEO.write_text(json.dumps(cache, ensure_ascii=False, indent=2), encoding='utf-8')


def cargar_locales():
    menus = cargar_menus()
    locales = []
    for row in _leer_csv(CSV_LOCALES):
        local = row.get('local')
        if not local or _normal(local) not in menus:
            continue  # sin menú cargado no se muestra
        lat, lon = _coords_fila(row)
        locales.append({
            'lugar': local, 'categoria': row.get('categoria') or 'Comida',
            'direccion': row.get('direccion', ''), 'lat': lat, 'lon': lon,
            'platos': menus[_normal(local)],
        })
    completar_coordenadas(locales)
    locales = [e for e in locales if e['lat'] is not None and e['lon'] is not None]
    for i, e in enumerate(locales, start=1):
        e['id'] = i
    return locales


def _cumple_tipo(p, tipo):
    if not tipo:
        return True
    if tipo == 'vegetariano':
        return p['tipo'] in ('vegetariano', 'vegano')
    return p['tipo'] == tipo   # vegano y sin_gluten: solo si el plato está marcado así


def _platos_filtrados(e, presupuesto, tipo, alergenos, momento):
    res = []
    for p in e['platos']:
        if p['precio'] > presupuesto or not _cumple_tipo(p, tipo):
            continue
        # sin alérgenos declarados no se puede garantizar que el plato sea seguro
        if alergenos and (p['alergenos'] is None or any(a in p['alergenos'] for a in alergenos)):
            continue
        if momento and momento not in p['momento']:
            continue
        res.append(p)
    return res


def index(request):
    return render(request, 'index.html')


def buscar_alternativas(request):
    presupuesto_max = _entero(request.GET.get('presupuesto', 10000), 10000)
    tipo_filtro = request.GET.get('tipo', '').strip().lower()
    alergeno_filtro = _lista_param(request.GET.get('alergeno', ''))
    momento_filtro = request.GET.get('momento', '').strip().lower()

    resultados = []
    for e in cargar_locales():
        platos = _platos_filtrados(e, presupuesto_max, tipo_filtro, alergeno_filtro, momento_filtro)
        if not platos:
            continue
        platos.sort(key=lambda p: p['precio'])
        con_dato = next((p for p in platos if p['kcal'] is not None and p['prot'] is not None), None)

        resultados.append({
            'id': e['id'], 'lugar': e['lugar'], 'direccion': e['direccion'] or 'Ver mapa',
            'latitud': e['lat'], 'longitud': e['lon'],
            'plato': " · ".join(f"{p['nombre']} {_precio(p['precio'])}" for p in platos),
            'platos': [{'nombre': p['nombre'], 'precio': p['precio'], 'kcal': p['kcal'],
                        'prot': p['prot'], 'compartir': p['compartir']} for p in platos],
            'precio': platos[0]['precio'], 'tipo_alimentacion': e['categoria'],
            'info_nutricional': ({'calorias': con_dato['kcal'], 'proteinas': con_dato['prot']}
                                 if con_dato else None),
        })

    return JsonResponse({'status': 'ok', 'resultados': resultados})


def menu_diario(request):
    """Elige un plato para desayuno, almuerzo y cena que cumpla presupuesto y dieta,
    dejando las calorías totales lo más cerca posible del objetivo."""
    presupuesto = _entero(request.GET.get('presupuesto', 10000), 10000)
    objetivo = _entero(request.GET.get('kcal', 2000), 2000)
    tipo = request.GET.get('tipo', '').strip().lower()
    alergeno = _lista_param(request.GET.get('alergeno', ''))

    candidatos = {m: [] for m in MOMENTOS}
    for e in cargar_locales():
        for p in _platos_filtrados(e, presupuesto, tipo, alergeno, ''):
            if p['compartir'] or p['kcal'] is None:
                continue  # sin porción individual o sin dato nutricional no se puede sumar
            for m in p['momento']:
                candidatos[m].append({
                    'lugar': e['lugar'], 'direccion': e['direccion'], 'plato': p['nombre'],
                    'precio': p['precio'], 'kcal': p['kcal'], 'prot': p['prot']})

    # con muchos locales se limita la búsqueda para que siga siendo rápida
    for m in MOMENTOS:
        c = sorted(candidatos[m], key=lambda x: x['kcal'])
        if len(c) > 40:
            paso = len(c) / 40
            c = [c[int(i * paso)] for i in range(40)]
        candidatos[m] = c

    disponibles = [m for m in MOMENTOS if candidatos[m]]
    faltan = [m for m in MOMENTOS if not candidatos[m]]
    minimo = sum(min(c['precio'] for c in candidatos[m]) for m in disponibles)

    mejor = None
    if disponibles:
        for combo in itertools.product(*(candidatos[m] for m in disponibles)):
            precio = sum(c['precio'] for c in combo)
            if precio > presupuesto:
                continue
            kcal = sum(c['kcal'] for c in combo)
            repetidos = len(combo) - len({c['plato'] for c in combo})
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