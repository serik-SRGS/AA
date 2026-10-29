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

    # Base de datos ampliada con locales reales del entorno USM San Joaquín
    locales_base = [
        {"id": 1, "lugar": "Casino Principal USM", "direccion": "Vicente Valdés 360", "lat": -33.4883, "lon": -70.6151, "plato": "Menú Ejecutivo Saludable", "precio": 3500, "tipo": "2", "tipo_nombre": "Vegetariano", "alergenos": ["lactosa"], "barcode": "737628064502"},
        {"id": 2, "lugar": "Cafetería Central USM", "direccion": "Campus San Joaquín", "lat": -33.4880, "lon": -70.6148, "plato": "Sandwich Ave Palta en Pan Integral", "precio": 2800, "tipo": "", "tipo_nombre": "General", "alergenos": ["gluten"], "barcode": ""},
        {"id": 3, "lugar": "Verde Sano Express", "direccion": "Av. Vicuña Mackenna 3900", "lat": -33.4875, "lon": -70.6145, "plato": "Bowl Quínoa y Verduras", "precio": 4200, "tipo": "1", "tipo_nombre": "Vegano", "alergenos": [], "barcode": "737628064502"},
        {"id": 4, "lugar": "El Rincón Vegetariano", "direccion": "Av. Haydn 120", "lat": -33.4868, "lon": -70.6138, "plato": "Hamburguesa de Lentejas con Ensalada", "precio": 3800, "tipo": "1", "tipo_nombre": "Vegano", "alergenos": ["gluten"], "barcode": ""},
        {"id": 5, "lugar": "Punto Fit San Joaquín", "direccion": "Calle Las Industrias 2400", "lat": -33.4890, "lon": -70.6160, "plato": "Ensalada Proteica Sin Gluten", "precio": 4800, "tipo": "3", "tipo_nombre": "Sin Gluten", "alergenos": ["mani"], "barcode": ""},
        {"id": 6, "lugar": "Subway Vicuña Mackenna", "direccion": "Av. Vicuña Mackenna 3800", "lat": -33.4860, "lon": -70.6150, "plato": "Sub Vegetariano 15cm", "precio": 3200, "tipo": "2", "tipo_nombre": "Vegetariano", "alergenos": ["gluten"], "barcode": ""},
        {"id": 7, "lugar": "Sánguche San Joaquín", "direccion": "Carlos Valdovinos 100", "lat": -33.4855, "lon": -70.6170, "plato": "Wrap Vegetariano con Hummus", "precio": 3000, "tipo": "2", "tipo_nombre": "Vegetariano", "alergenos": ["lactosa"], "barcode": ""},
        {"id": 8, "lugar": "Ensaladería Campus", "direccion": "Av. Vicuña Mackenna 4100", "lat": -33.4905, "lon": -70.6130, "plato": "Mix Verde con Garbanzos y Semillas", "precio": 3600, "tipo": "1", "tipo_nombre": "Vegano", "alergenos": [], "barcode": ""},
        {"id": 9, "lugar": "Café Central San Joaquín", "direccion": "Av. Las Industrias 2200", "lat": -33.4845, "lon": -70.6180, "plato": "Tartaleta Sin Gluten de Verduras", "precio": 3900, "tipo": "3", "tipo_nombre": "Sin Gluten", "alergenos": ["lactosa"], "barcode": ""},
        {"id": 10, "lugar": "Pronto Copec Vicuña Mackenna", "direccion": "Av. Vicuña Mackenna 3600", "lat": -33.4830, "lon": -70.6165, "plato": "Ensalada César Vegetariana", "precio": 4500, "tipo": "2", "tipo_nombre": "Vegetariano", "alergenos": ["lactosa", "gluten"], "barcode": ""},
        {"id": 11, "lugar": "Pizzería EcoFit", "direccion": "Calle Benito Rebolledo 1800", "lat": -33.4898, "lon": -70.6185, "plato": "Pizza Individual Vegana de Champiñones", "precio": 4900, "tipo": "1", "tipo_nombre": "Vegano", "alergenos": ["gluten"], "barcode": ""},
        {"id": 12, "lugar": "Sushi Rolls San Joaquín", "direccion": "Av. Vicuña Mackenna 4300", "lat": -33.4920, "lon": -70.6120, "plato": "Handroll Vegano Palta Palmito", "precio": 2500, "tipo": "1", "tipo_nombre": "Vegano", "alergenos": [], "barcode": ""}
    ]

    # Consulta ampliada a Overpass API (OpenStreetMap) a 2000m a la redonda
    overpass_url = "https://overpass-api.de/api/interpreter"
    query = f"""
    [out:json];
    (
      node["amenity"~"restaurant|cafe|fast_food"](around:2000, {usm_lat}, {usm_lng});
    );
    out body 25;
    """
    
    locales_api = []
    try:
        resp = requests.post(overpass_url, data={'data': query}, timeout=3)
        if resp.status_code == 200:
            data = resp.json().get('elements', [])
            idx = 100
            for elem in data:
                nom = elem.get('tags', {}).get('name')
                if nom:
                    idx += 1
                    locales_api.append({
                        "id": idx,
                        "lugar": nom,
                        "direccion": elem.get('tags', {}).get('addr:street', 'Sector San Joaquín'),
                        "lat": elem.get('lat'),
                        "lon": elem.get('lon'),
                        "plato": "Menú del Día Saludable",
                        "precio": random.choice([2500, 2900, 3400, 3800, 4200, 4700]),
                        "tipo": random.choice(["1", "2", "3"]),
                        "tipo_nombre": random.choice(["Vegano", "Vegetariano", "Sin Gluten"]),
                        "alergenos": [],
                        "barcode": ""
                    })
    except Exception:
        pass

    todos = locales_base + locales_api
    resultados = []

    for item in todos:
        if item['precio'] > presupuesto_max:
            continue
        if tipo_filtro and item['tipo'] != tipo_filtro:
            continue
        if alergeno_filtro and alergeno_filtro in item['alergenos']:
            continue

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
            'id': item['id'],
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