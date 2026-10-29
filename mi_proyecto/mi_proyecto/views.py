import requests
from django.shortcuts import render
from django.http import JsonResponse
from .models import Lugar, Plato

# Vista para renderizar la página principal
def index(request):
    return render(request, 'index.html')

# Vista de la API para la búsqueda y filtrado (Funcionalidad Corazón)
def buscar_alternativas(request):
    presupuesto_max = request.GET.get('presupuesto', 10000)
    tipo_alimento_id = request.GET.get('tipo')
    alergeno_id = request.GET.get('alergeno')

    platos = Plato.objects.filter(precio__lte=presupuesto_max)

    if tipo_alimento_id:
        platos = platos.filter(tipo_alimentacion_id=tipo_alimento_id)
    
    if alergeno_id:
        platos = platos.exclude(alergenos__id=alergeno_id)

    resultados = []
    for plato in platos.order_by('precio'):
        info_nutricional = None
        
        # Consulta a API externa de información nutricional
        if plato.barcode:
            api_url = f"https://world.openfoodfacts.org/api/v2/product/{plato.barcode}.json"
            try:
                response = requests.get(api_url, timeout=3)
                if response.status_code == 200:
                    data = response.json().get('product', {})
                    nutriments = data.get('nutriments', {})
                    info_nutricional = {
                        'calorias': nutriments.get('energy-kcal_100g', 'N/I'),
                        'proteinas': nutriments.get('proteins_100g', 'N/I'),
                        'carbohidratos': nutriments.get('carbohydrates_100g', 'N/I'),
                    }
            except requests.RequestException:
                info_nutricional = None

        resultados.append({
            'lugar': plato.lugar.nombre,
            'direccion': plato.lugar.direccion,
            'latitud': plato.lugar.latitud,
            'longitud': plato.lugar.longitud,
            'plato': plato.nombre,
            'precio': plato.precio,
            'tipo_alimentacion': plato.tipo_alimentacion.nombre,
            'info_nutricional': info_nutricional
        })

    return JsonResponse({'status': 'ok', 'resultados': resultados})
