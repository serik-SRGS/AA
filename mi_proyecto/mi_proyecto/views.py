from django.shortcuts import render
from django.http import JsonResponse

def index(request):
    return render(request, 'index.html')

def buscar_alternativas(request):
    try:
        presupuesto_max = int(request.GET.get('presupuesto', 10000))
    except ValueError:
        presupuesto_max = 10000

    tipo_filtro = request.GET.get('tipo', '').strip()
    alergeno_filtro = request.GET.get('alergeno', '').strip()

    locales_reales = [
        {"id": 1, "lugar": "Subway - Vicuña Mackenna 4927", "direccion": "Av. Vicuña Mackenna 4927 (Metro Camino Agrícola)", "lat": -33.4892, "lon": -70.6152, "plato": "Sub Vegetariano 15cm", "precio": 3200, "tipo": "vegetariano", "tipo_nombre": "Vegetariano", "alergenos": ["gluten"], "nutri": {"calorias": 320, "proteinas": 12.5}},
        {"id": 2, "lugar": "Little Caesars Pizza - San Joaquín", "direccion": "Av. Vicuña Mackenna 4927C", "lat": -33.4890, "lon": -70.6150, "plato": "Pizza Cheese (Queso Individual)", "precio": 3900, "tipo": "vegetariano", "tipo_nombre": "Vegetariano", "alergenos": ["gluten", "lactosa"], "nutri": {"calorias": 450, "proteinas": 18.0}},
        {"id": 3, "lugar": "La Bicicleta Bar / Restaurant", "direccion": "Av. Vicuña Mackenna 4775", "lat": -33.4881, "lon": -70.6156, "plato": "Tabla Vegana de Hummus y Verduras", "precio": 4800, "tipo": "vegano", "tipo_nombre": "Vegano", "alergenos": [], "nutri": {"calorias": 280, "proteinas": 9.0}},
        {"id": 4, "lugar": "El Fito Restaurante", "direccion": "Av. Vicuña Mackenna 4779", "lat": -33.4883, "lon": -70.6155, "plato": "Plato Ejecutivo Vegetariano del Día", "precio": 3800, "tipo": "vegetariano", "tipo_nombre": "Vegetariano", "alergenos": ["lactosa"], "nutri": {"calorias": 390, "proteinas": 14.0}},
        {"id": 5, "lugar": "Fuente Mardoqueo - San Joaquín", "direccion": "Av. Vicuña Mackenna 3207", "lat": -33.4795, "lon": -70.6201, "plato": "Papas Fritas Grandes + Bebida", "precio": 4000, "tipo": "vegano", "tipo_nombre": "Vegano", "alergenos": [], "nutri": {"calorias": 520, "proteinas": 6.0}},
        {"id": 6, "lugar": "Casino Central USM San Joaquín", "direccion": "Inside Campus USM San Joaquín", "lat": -33.4883, "lon": -70.6151, "plato": "Menú Institucional Hipocalórico", "precio": 3500, "tipo": "sin_gluten", "tipo_nombre": "Sin Gluten", "alergenos": [], "nutri": {"calorias": 310, "proteinas": 15.0}},
        {"id": 7, "lugar": "Pastelería y Cafetería Dgustar", "direccion": "Av. Macul 3126", "lat": -33.4820, "lon": -70.6025, "plato": "Tarta de Avena y Frutas Sin Lactosa", "precio": 2900, "tipo": "sin_gluten", "tipo_nombre": "Sin Gluten", "alergenos": ["mani"], "nutri": {"calorias": 240, "proteinas": 7.0}},
        {"id": 8, "lugar": "Trujillo Restorant", "direccion": "Rotonda Pedro de Valdivia 1204", "lat": -33.4835, "lon": -70.6090, "plato": "Ceviche de Legumbres y Palta", "precio": 4500, "tipo": "vegano", "tipo_nombre": "Vegano", "alergenos": [], "nutri": {"calorias": 290, "proteinas": 11.0}},
        {"id": 9, "lugar": "Pame-Food", "direccion": "Av. Vicuña Mackenna 4927", "lat": -33.4893, "lon": -70.6153, "plato": "Ensalada Completa de Quínoa y Palta", "precio": 3600, "tipo": "vegano", "tipo_nombre": "Vegano", "alergenos": [], "nutri": {"calorias": 330, "proteinas": 10.5}},
        {"id": 10, "lugar": "La Piccola Italia - San Joaquín", "direccion": "Av. Vicuña Mackenna 4800", "lat": -33.4885, "lon": -70.6158, "plato": "Minestrone de Verduras Frescas", "precio": 4200, "tipo": "vegetariano", "tipo_nombre": "Vegetariano", "alergenos": ["gluten"], "nutri": {"calorias": 260, "proteinas": 8.0}},
        {"id": 11, "lugar": "McDonald's - Vicuña Mackenna", "direccion": "Av. Vicuña Mackenna 3885 (Metro Carlos Valdovinos)", "lat": -33.4838, "lon": -70.6180, "plato": "McPapas Medianas + Ensalada Verde", "precio": 2900, "tipo": "vegano", "tipo_nombre": "Vegano", "alergenos": [], "nutri": {"calorias": 340, "proteinas": 5.0}},
        {"id": 12, "lugar": "Doggis - Mall Paseo Quilín / Vicuña", "direccion": "Av. Vicuña Mackenna 4927", "lat": -33.4895, "lon": -70.6149, "plato": "Empanadas de Queso x3", "precio": 2500, "tipo": "vegetariano", "tipo_nombre": "Vegetariano", "alergenos": ["gluten", "lactosa"], "nutri": {"calorias": 410, "proteinas": 11.0}},
        {"id": 13, "lugar": "Pedro, Juan & Diego", "direccion": "Av. Vicuña Mackenna 4860", "lat": -33.4888, "lon": -70.6155, "plato": "Papas Fritas Familiar con Salsa Ajo", "precio": 3400, "tipo": "vegetariano", "tipo_nombre": "Vegetariano", "alergenos": [], "nutri": {"calorias": 580, "proteinas": 7.0}},
        {"id": 14, "lugar": "Sushilove San Joaquín", "direccion": "Av. Las Industrias 2320", "lat": -33.4870, "lon": -70.6185, "plato": "Handroll Vegano Palta Champiñón", "precio": 2800, "tipo": "vegano", "tipo_nombre": "Vegano", "alergenos": [], "nutri": {"calorias": 300, "proteinas": 8.5}},
        {"id": 15, "lugar": "KFC - Vicuña Mackenna", "direccion": "Av. Vicuña Mackenna 3950", "lat": -33.4842, "lon": -70.6178, "plato": "Papas Fritas Fanes + Choclo Dulce", "precio": 2700, "tipo": "vegetariano", "tipo_nombre": "Vegetariano", "alergenos": [], "nutri": {"calorias": 360, "proteinas": 6.0}},
        {"id": 16, "lugar": "Café Starbucks - Campus San Joaquín UC", "direccion": "Av. Vicuña Mackenna 4860", "lat": -33.4870, "lon": -70.6125, "plato": "Muffin Vegano de Arándanos", "precio": 3100, "tipo": "vegano", "tipo_nombre": "Vegano", "alergenos": ["gluten"], "nutri": {"calorias": 290, "proteinas": 5.0}},
        {"id": 17, "lugar": "Cafetería Punto Café USM", "direccion": "Patio de la Madera, Campus USM", "lat": -33.4886, "lon": -70.6148, "plato": "Galletón Integral Avena Miel Sin Lactosa", "precio": 1800, "tipo": "sin_gluten", "tipo_nombre": "Sin Gluten", "alergenos": ["mani"], "nutri": {"calorias": 210, "proteinas": 6.5}},
        {"id": 18, "lugar": "Pizzería Melt Pizzas - San Joaquín", "direccion": "Av. Vicuña Mackenna 4350", "lat": -33.4862, "lon": -70.6168, "plato": "Cheese Sticks Veganos con Dip de Tomate", "precio": 4500, "tipo": "vegano", "tipo_nombre": "Vegano", "alergenos": ["gluten"], "nutri": {"calorias": 420, "proteinas": 13.0}},
        {"id": 19, "lugar": "Telepizza - Carlos Valdovinos", "direccion": "Av. Vicuña Mackenna 3700", "lat": -33.4828, "lon": -70.6188, "plato": "Pizza Vegetariana Individual", "precio": 4200, "tipo": "vegetariano", "tipo_nombre": "Vegetariano", "alergenos": ["gluten", "lactosa"], "nutri": {"calorias": 480, "proteinas": 16.0}},
        {"id": 20, "lugar": "Restaurant China San Joaquín", "direccion": "Av. Vicuña Mackenna 4510", "lat": -33.4871, "lon": -70.6162, "plato": "Chapsui de Verduras Especial", "precio": 4600, "tipo": "vegano", "tipo_nombre": "Vegano", "alergenos": [], "nutri": {"calorias": 310, "proteinas": 9.0}},
        {"id": 21, "lugar": "Doner Kebab & Falafel", "direccion": "Av. Las Industrias 2510", "lat": -33.4898, "lon": -70.6172, "plato": "Wrap de Falafel con Salsa de Sésamo", "precio": 3900, "tipo": "vegano", "tipo_nombre": "Vegano", "alergenos": ["gluten"], "nutri": {"calorias": 370, "proteinas": 12.0}},
        {"id": 22, "lugar": "Ensaladería & Jugos Naturales", "direccion": "Av. Haydn 210", "lat": -33.4860, "lon": -70.6132, "plato": "Bowl Verde Antioxidante + Jugo Natural", "precio": 4900, "tipo": "vegano", "tipo_nombre": "Vegano", "alergenos": [], "nutri": {"calorias": 250, "proteinas": 8.0}},
        {"id": 23, "lugar": "Pronto Copec - Vicuña Mackenna", "direccion": "Av. Vicuña Mackenna 3600", "lat": -33.4820, "lon": -70.6190, "plato": "Wrap Vegano de Verduras Asadas", "precio": 3700, "tipo": "vegano", "tipo_nombre": "Vegano", "alergenos": [], "nutri": {"calorias": 320, "proteinas": 9.5}},
        {"id": 24, "lugar": "Sushi Niu Sushi - San Joaquín", "direccion": "Av. Vicuña Mackenna 4120", "lat": -33.4851, "lon": -70.6172, "plato": "Roll Vegano Palta Cevichado", "precio": 4950, "tipo": "vegano", "tipo_nombre": "Vegano", "alergenos": [], "nutri": {"calorias": 290, "proteinas": 7.0}},
        {"id": 25, "lugar": "Shawarma & Hummus Express", "direccion": "Benito Rebolledo 1910", "lat": -33.4902, "lon": -70.6180, "plato": "Plato de Hummus con Pan Pita e Insumos", "precio": 3600, "tipo": "vegano", "tipo_nombre": "Vegano", "alergenos": ["gluten"], "nutri": {"calorias": 380, "proteinas": 11.5}}
    ]

    resultados = []

    for item in locales_reales:
        if item['precio'] > presupuesto_max:
            continue
        if tipo_filtro and item['tipo'] != tipo_filtro:
            continue
        if alergeno_filtro and alergeno_filtro in item['alergenos']:
            continue

        resultados.append({
            'id': item['id'],
            'lugar': item['lugar'],
            'direccion': item['direccion'],
            'latitud': item['lat'],
            'longitud': item['lon'],
            'plato': item['plato'],
            'precio': item['precio'],
            'tipo_alimentacion': item['tipo_nombre'],
            'info_nutricional': item['nutri']
        })

    return JsonResponse({'status': 'ok', 'resultados': resultados})