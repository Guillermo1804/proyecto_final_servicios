from decimal import Decimal, ROUND_FLOOR

from django.db.models import Avg, Count, Max, Min, Sum

from apps.core.models import Actividad, Calificacion, Ponderacion


def _to_decimal(value):
    if isinstance(value, Decimal):
        return value
    return Decimal(str(value))


def redondear_institucional(promedio_real):
    promedio = _to_decimal(promedio_real)
    parte_entera = promedio.to_integral_value(rounding=ROUND_FLOOR)
    fraccion = promedio - parte_entera
    return int(parte_entera + 1 if fraccion >= Decimal('0.5') else parte_entera)


def _promedio_categoria(alumno_id, ponderacion):
    calificaciones = Calificacion.objects.filter(
        alumno_id=alumno_id,
        actividad__ponderacion=ponderacion,
    ).values_list('calificacion', flat=True)

    calificaciones = list(calificaciones)
    if not calificaciones:
        return Decimal('0.00')

    total = sum((Decimal(str(item)) for item in calificaciones), Decimal('0.00'))
    return total / Decimal(len(calificaciones))


def calcular_promedio_ponderado(alumno_id, materia_id):
    ponderaciones = list(
        Ponderacion.objects.filter(materia_id=materia_id).prefetch_related('actividades')
    )
    if not ponderaciones:
        return Decimal('0.00')

    promedio_real = Decimal('0.00')
    for ponderacion in ponderaciones:
        promedio_categoria = _promedio_categoria(alumno_id, ponderacion)
        proporcion = Decimal(str(ponderacion.porcentaje)) / Decimal('100')
        promedio_real += promedio_categoria * proporcion

    return promedio_real


def obtener_estadisticas_materia(materia_id):
    calificaciones = Calificacion.objects.filter(actividad__ponderacion__materia_id=materia_id)
    if not calificaciones.exists():
        return None

    promedios_por_alumno = []
    for alumno_id in calificaciones.values_list('alumno_id', flat=True).distinct():
        promedio_real = calcular_promedio_ponderado(alumno_id, materia_id)
        promedios_por_alumno.append(promedio_real)

    total_alumnos = len(promedios_por_alumno)
    promedio_grupal = (
        sum(promedios_por_alumno, Decimal('0.00')) / Decimal(total_alumnos)
        if total_alumnos
        else Decimal('0.00')
    )
    calificacion_maxima = max(promedios_por_alumno) if promedios_por_alumno else Decimal('0.00')
    calificacion_minima = min(promedios_por_alumno) if promedios_por_alumno else Decimal('0.00')
    aprobados = sum(1 for promedio in promedios_por_alumno if redondear_institucional(promedio) >= 6)

    return {
        'total_alumnos': total_alumnos,
        'aprobados': aprobados,
        'reprobados': total_alumnos - aprobados,
        'promedio_grupal': promedio_grupal,
        'calificacion_maxima': calificacion_maxima,
        'calificacion_minima': calificacion_minima,
    }


def obtener_concentrado_materia(materia_id):
    ponderaciones = list(
        Ponderacion.objects.filter(materia_id=materia_id).prefetch_related('actividades__calificaciones')
    )
    if not ponderaciones:
        return None

    actividades_por_categoria = []
    for ponderacion in ponderaciones:
        actividades = list(ponderacion.actividades.all().order_by('id'))
        actividades_por_categoria.append((ponderacion, actividades))

    calificaciones_qs = Calificacion.objects.filter(actividad__ponderacion__materia_id=materia_id)
    if not calificaciones_qs.exists():
        return {
            'categorias': actividades_por_categoria,
            'alumnos': [],
        }

    alumno_ids = list(calificaciones_qs.values_list('alumno_id', flat=True).distinct().order_by('alumno_id'))
    alumnos = []
    for alumno_id in alumno_ids:
        promedio_real = calcular_promedio_ponderado(alumno_id, materia_id)
        promedio_redondeado = redondear_institucional(promedio_real)
        calificaciones_alumno = calificaciones_qs.filter(alumno_id=alumno_id).select_related('actividad__ponderacion').order_by('actividad__ponderacion__id', 'actividad__id')
        actividades = []
        for calificacion in calificaciones_alumno:
            actividades.append({
                'actividad_id': calificacion.actividad_id,
                'actividad_nombre': calificacion.actividad.nombre,
                'categoria': calificacion.actividad.ponderacion.nombre_categoria,
                'calificacion': calificacion.calificacion,
            })

        alumnos.append({
            'alumno_id': alumno_id,
            'matricula': str(alumno_id),
            'nombre': '',
            'calificaciones': actividades,
            'promedio_real': promedio_real,
            'promedio_redondeado': promedio_redondeado,
        })

    return {
        'categorias': actividades_por_categoria,
        'alumnos': alumnos,
    }