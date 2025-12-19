from django import template

register = template.Library()

@register.filter
def abreviar_depto(nombre_departamento):
    # 1. TU DICCIONARIO DE ABREVIACIONES
    # Aquí defines las excepciones largas
    diccionario = {
        "Dirección desarrollo Económico y Cooperación Internacional": "DDE",
        "Dirección de Obras Municipales": "DOM",
        "SECPLA": "SECPLA",
        "Administración y Finanzas": "DAF",
        # Agrega todos los que quieras aquí...
    }
    
    # Aseguramos que sea string
    nombre = str(nombre_departamento)

    # 2. LÓGICA
    # Si el nombre está en el diccionario, usa la abreviación.
    # Si no está, usa la primera letra por defecto.
    return diccionario.get(nombre, nombre[:1].upper())