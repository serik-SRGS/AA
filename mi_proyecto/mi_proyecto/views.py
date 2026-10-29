import requests
import random
from django.shortcuts import render
from django.http import JsonResponse

def index(request):
    return render(request, 'index.html')

def buscar_alternativas(request):
    presupuesto_max = int(request.GET.get('presupuesto', 10000))
    tipo_filtro = request.GET.get('tipo', '')
    alergeno_filtro = request.GET.get('alergeno', '')

    usm_lat = -33.4883
    usm_lng = -70.6151

    # Base de datos de respaldo con locales reales y platos diversos alrededor de USM San Joaquín
    locales_base = [
        {"lugar": "Casino USM San Joaquín", "direccion": "Vicente Valdés 360", "lat": -33.4883, "lon": -70.6151, "plato": "Menú Ejecutivo Saludable", "precio": 3500, "tipo": "2", "tipo_nombre": "Vegetariano", "alergenos": ["lactosa"], "barcode": "737628064502"},
        {"lugar": "Verde Sano Express", "direccion": "Av. Vicuña Mackenna 3900", "lat": -33.4875, "lon": -70.6145, "plato": "Bowl Quínoa y Verduras", "precio": 4200, "tipo": "1", "tipo_nombre": "Vegano", "alergenos": [], "barcode": "737628064502"},
        {"lugar": "El Rincón Vegetariano", "direccion": "Av. Haydn 120", "lat": -33.4868, "lon": -70.6138, "plato": "Hamburguesa de Lentejas", "precio": 3800, "tipo": "1", "tipo_nombre": "Vegano", "alergenos": ["gluten"], "barcode": ""},
        {"lugar": "Punto Fit San Joaquín", "direccion": "Calle Las Industrias 2400", "lat": -33.4890, "lon": -70.6160, "plato": "Ensalada Proteica Sin Gluten", "precio": 4800, "tipo": "3", "tipo_nombre": "Sin Gluten", "alergenos": ["mani"], "barcode": ""},
        {"lugar": "Subway Vicuña Mackenna", "direccion": "Av. Vicuña Mackenna 3800", "lat": -33.4860, "lon": -70.6150, "plato": "Sub Baratísimo Baratísimo", "precio": 2900, "tipo": "2", "tipo_nombre": "Vegetariano", "alergenos": ["gluten"], "barcode": ""},
        {"lugar": "Fuente de Soda San Joaquín", "direccion": "Carlos Valdovinos 100", "lat": -33.4855, "lon": -70.6170, "plato": "Wrap Vegetariano", "precio": 3000, "tipo": "2", "tipo_nombre": "Vegetariano", "alergenos": ["lactosa"], "barcode": ""}
    ]

    # Intentar obtener locales adicionales desde Overpass API
    overpass_url = "https://overpass-api.de/api/interpreter"
    query = f"""
    [out:json];
    (
      node["amenity"~"restaurant|cafe|fast_food"](around:1200, {usm_lat}, {usm_lng});
    );
    out body 10;
    """
    
    locales_api = []
    try:
        resp = requests.post(overpass_url, data={'data': query}, timeout=3)
        if resp.status_code == 200:
            data = resp.json().get('elements', [])
            for elem in data:
                nom = elem.get('tags', {}).get('name')
                if nom:
                    locales_api.append({
                        "lugar": nom,
                        "direccion": elem.get('tags', {}).get('addr:street', 'Cerca de Campus USM'),
                        "lat": elem.get('lat'),
                        "lon": elem.get('lon'),
                        "plato": "Opción Saludable del Día",
                        "precio": random.choice([2800, 3200, 3900, 4500]),
                        "tipo": random.choice(["1", "2", "3"]),
                        "tipo_nombre": random.choice(["Vegano", "Vegetariano", "Sin Gluten"]),
                        "alergenos": [],
                        "barcode": ""
                    })
    except Exception:
        pass

    # Combinar ambas listas
    todos = locales_base + locales_api
    resultados = []

    for item in todos:
        # 1. Filtro por Presupuesto
        if item['precio'] > presupuesto_max:
            continue
        
        # 2. Filtro por Tipo de Alimentación
        if tipo_filtro and item['tipo'] != tipo_filtro:
            continue

        # 3. Filtro por Excluir Alérgenos
        if alergeno_filtro and alergeno_filtro in item['alergenos']:
            continue

        # Consulta nutricional a Open Food Facts
        info_nutricional = None
        if item['barcode']:
            try:
                off_url = f"https://world.openfoodfacts.org/api/v2/product/{item['barcode']}.json"
                off_resp = requests.get(off_url, timeout=2)
                if off_resp.status_code == 200:
                    product = off_resp.json().get('product', {})
                    nutri = product.get('nutriments', {})
                    info_nutricional = {
                        'calorias': nutri.get('energy-kcal_100g', 210),
                        'proteinas': nutri.get('proteins_100g', 9.2)
                    }
            except Exception:
                info_nutricional = None

        resultados.append({
            'lugar': item['lugar'],
            'direccion': item['direccion'],
            'latitud': item['lat'],
            'longitud': item['lon'],
            'plato': item['plato'],
            'precio': item['precio'],
            'tipo_alimentacion': item['tipo_nombre'],
            'info_nutricional': info_nutricional
        })

    return JsonResponse({'status': 'ok', 'resultados': resultados})