"""Docente, alumnos e inscripciones demo."""

from django.core.management.base import BaseCommand
from django.db import transaction

from apps.core.models import Alumno, Docente, InscripcionMateria
from utils.periodos_ms2_client import get_materia_detail

# Sin cuenta MS-1; solo aparecen en listas del docente (IDs altos, no colisionan con auth).
LISTA_SOLO_USUARIO_IDS = (100004, 100005, 100006)


class Command(BaseCommand):
    help = 'Crea docente, alumnos e inscripciones demo (idempotente)'

    def add_arguments(self, parser):
        parser.add_argument('--docente-usuario-id', type=int, required=True)
        parser.add_argument('--alumno-usuario-id', type=int, required=True)
        parser.add_argument('--alumno2-usuario-id', type=int, default=0)
        parser.add_argument('--alumno3-usuario-id', type=int, default=0)
        parser.add_argument('--materia-ids', type=str, default='1,2,3')

    @transaction.atomic
    def handle(self, *args, **options):
        docente_uid = options['docente_usuario_id']
        materia_ids = [int(x) for x in options['materia_ids'].split(',') if x.strip()]

        docente, _ = Docente.objects.update_or_create(
            usuario_id=docente_uid,
            defaults={
                'nombre': 'María',
                'apellido': 'Docente Demo',
                'email': 'docente.demo@agm.buap.mx',
                'departamento': 'Facultad de Ciencias de la Computación',
            },
        )
        self.stdout.write(f'Docente MS-3 id={docente.id} usuario_id={docente_uid}')

        alumnos_spec = [
            (options['alumno_usuario_id'], '202600001', 'Ana', 'Alumno Demo', 'alumno.demo@agm.buap.mx'),
            (options['alumno2_usuario_id'], '202600002', 'Luis', 'Alumno Demo', 'alumno2.demo@agm.buap.mx'),
            (options['alumno3_usuario_id'], '202600003', 'Sofía', 'Alumno Demo', 'alumno3.demo@agm.buap.mx'),
            (LISTA_SOLO_USUARIO_IDS[0], '202600004', 'Carlos', 'Pérez', 'carlos.perez.demo@buap.mx'),
            (LISTA_SOLO_USUARIO_IDS[1], '202600005', 'Diana', 'López', 'diana.lopez.demo@buap.mx'),
            (LISTA_SOLO_USUARIO_IDS[2], '202600006', 'Elena', 'Martínez', 'elena.martinez.demo@buap.mx'),
        ]

        alumno_ms3_ids = []
        for usuario_id, matricula, nombre, apellido, email in alumnos_spec:
            if not matricula:
                continue
            defaults = {
                'usuario_id': usuario_id,
                'nombre': nombre,
                'apellido': apellido,
                'email': email,
                'carrera': 'Ingeniería en Ciencias de la Computación',
                'semestre': 5,
                'activo': True,
            }
            alumno, created = Alumno.objects.update_or_create(
                matricula=matricula,
                defaults=defaults,
            )
            alumno_ms3_ids.append(alumno.id)
            self.stdout.write(
                f'Alumno id={alumno.id} matricula={matricula} '
                f'({"login" if usuario_id < 100000 else "solo lista"})'
            )

        primary = Alumno.objects.get(matricula='202600001')
        login_matriculas = {'202600001', '202600002', '202600003'}

        for materia_id in materia_ids:
            detail = get_materia_detail(materia_id) or {}
            for alumno in Alumno.objects.filter(matricula__startswith='202600'):
                if materia_id == materia_ids[0]:
                    enroll = True
                elif materia_id == materia_ids[1] if len(materia_ids) > 1 else False:
                    enroll = alumno.matricula in login_matriculas
                else:
                    enroll = alumno.matricula == '202600001'
                if not enroll:
                    continue
                InscripcionMateria.objects.update_or_create(
                    alumno=alumno,
                    materia_id=materia_id,
                    defaults={
                        'nrc': detail.get('nrc', ''),
                        'nombre_materia': detail.get('nombre', f'Materia {materia_id}'),
                        'docente_nombre': detail.get('docente_nombre', 'María Docente Demo'),
                        'horario': detail.get('horario', ''),
                        'activa': True,
                        'fecha_baja': None,
                    },
                )
        self.stdout.write(self.style.SUCCESS('Inscripciones demo listas.'))
        self.stdout.write(f'SEED_DOCENTE_MS3_ID={docente.id}')
        self.stdout.write(f'SEED_ALUMNO_MS3_ID={primary.id}')
        self.stdout.write(f'SEED_ALUMNO_MS3_IDS={",".join(str(i) for i in alumno_ms3_ids)}')
