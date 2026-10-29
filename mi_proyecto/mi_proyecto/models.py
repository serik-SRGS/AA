from django.db import models

class Lugar(models.Model):
    nombre = models.CharField(max_length=100)
    direccion = models.CharField(max_length=200)
    latitud = models.FloatField()
    longitud = models.FloatField()
    precio_promedio = models.IntegerField()

    def __str__(self):
        return self.nombre

class TipoAlimentacion(models.Model):
    nombre = models.CharField(max_length=50) # Ej: Vegano, Vegetariano, Omnívoro

    def __str__(self):
        return self.nombre

class Alergeno(models.Model):
    nombre = models.CharField(max_length=50) # Ej: Maní, Lactosa, Gluten

    def __str__(self):
        return self.nombre

class Plato(models.Model):
    lugar = models.ForeignKey(Lugar, on_delete=models.CASCADE, related_name='platos')
    nombre = models.CharField(max_length=100)
    precio = models.IntegerField()
    tipo_alimentacion = models.ForeignKey(TipoAlimentacion, on_delete=models.CASCADE)
    alergenos = models.ManyToManyField(Alergeno, blank=True)
    barcode = models.CharField(max_length=50, blank=True, null=True) # Código para Open Food Facts

    def __str__(self):
        return f"{self.nombre} - ${self.precio}"
