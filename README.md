GEOFIT - Plataforma de Alimentación Saludable y Económica USM San Joaquín
GEOFIT es una aplicación web desarrollada en Django para la asignatura IWG400 - Proyecto Inicial (Equipo 4 - Pentabyte). Su objetivo es ayudar a los estudiantes de la Universidad Técnica Federico Santa María (Campus San Joaquín) a encontrar alternativas gastronómicas saludables, económicas y adaptadas a restricciones alimentarias (veganas, vegetarianas, sin gluten y alérgenos) en los alrededores del campus.
Requisitos previos
Asegúrate de tener instalado en tu equipo:
 * Python 3.10 o superior
 * Git
 * Navegador web moderno (Chrome, Edge, Firefox, etc.)
Instrucciones de Instalación y Ejecución Local
Sigue estos pasos en tu terminal para clonar y ejecutar el proyecto localmente:

1. Clonar el repositorio
git clone https://github.com/serik-SRGS/AA.git
cd AA

2. Crear y activar un entorno virtual (Recomendado)
 * En Windows (PowerShell / CMD):
   python -m venv venv
   venv\Scripts\activate
 * En Linux / macOS:
   python3 -m venv venv
   source venv/bin/activate

3. Instalar dependencias
pip install django

4. Realizar migraciones del sistema
python manage.py migrate

5. Iniciar el servidor de desarrollo
python manage.py runserver
Una vez iniciado el servidor, abre tu navegador e ingresa a:
http://127.0.0.1:8000/

Pruebas de la Funcionalidad Corazón
La funcionalidad corazón permite buscar y geolocalizar opciones gastronómicas reales en el eje de Av. Vicuña Mackenna y el entorno universitario.
Casos de prueba sugeridos para revisión:

 * Caso 1 (Búsqueda Estudiantil Estándar):
   * Ajusta el slider de Presupuesto Máximo a $3.500.
   * En Tipo de alimentación, selecciona Vegetariano.
   * En Excluir Alérgeno, selecciona Sin restricciones.
   * Presiona Buscar alternativas.
   * Resultado esperado: Despliegue de locales con opciones vegetarianas menores o iguales a $3.500 (ej. Subway Vegetariano, Doggis, Casino USM) tanto en la lista como con marcadores interactivos en el mapa.
 
 * Caso 2 (Restricción Estricta por Alérgenos):
   * Ajusta el Presupuesto Máximo a $4.000.
   * Selecciona Vegano y en Excluir Alérgeno selecciona Gluten.
   * Presiona Buscar alternativas.
   * Resultado esperado: Filtrado exclusivo de alternativas 100% veganas y libres de gluten (ej. Pame-Food, McDonald's McPapas), descartando ítems con gluten como muffins o wraps.

Equipo Pentabyte (USM San Joaquín - 2026)
 * Cristóbal González
 * Laura Guajardo
 * Leslie Guerra
 * Sebastián Guzmán
 * Vicente Henríquez
