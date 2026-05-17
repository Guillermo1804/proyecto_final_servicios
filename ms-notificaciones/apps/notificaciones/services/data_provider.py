"""Proveedor de datos de otros MS (placeholder o gRPC real)."""

import logging
from dataclasses import dataclass
from typing import List, Optional

from grpc_clients import alumnos_client, periodos_client

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class AlumnoData:
    id: int
    nombre: str
    matricula: str
    email: str


@dataclass(frozen=True)
class MateriaData:
    id: int
    nombre: str
    nrc: str
    seccion: str
    periodo_nombre: str = ''


@dataclass(frozen=True)
class DocenteData:
    usuario_id: int
    nombre: str
    email: str


class NotificacionesDataProvider:
    """Contrato que implementarán los grpc_clients en Fase C."""

    def get_alumno(self, alumno_id: int) -> Optional[AlumnoData]:
        raise NotImplementedError

    def get_materia(self, materia_id: int) -> Optional[MateriaData]:
        raise NotImplementedError

    def get_docente_by_usuario_id(self, usuario_id: int) -> Optional[DocenteData]:
        raise NotImplementedError

    def get_alumnos_by_materia(self, materia_id: int) -> List[AlumnoData]:
        raise NotImplementedError


class PlaceholderDataProvider(NotificacionesDataProvider):
    """Datos simulados para desarrollo y tests unitarios (Fase B)."""

    def get_alumno(self, alumno_id: int) -> Optional[AlumnoData]:
        if alumno_id <= 0:
            return None
        return AlumnoData(
            id=alumno_id,
            nombre=f'Alumno Demo {alumno_id}',
            matricula=f'2024{alumno_id:04d}',
            email=f'alumno{alumno_id}@estudiantes.buap.mx',
        )

    def get_materia(self, materia_id: int) -> Optional[MateriaData]:
        if materia_id <= 0:
            return None
        return MateriaData(
            id=materia_id,
            nombre=f'Materia Demo {materia_id}',
            nrc=f'NRC{materia_id:05d}',
            seccion='A',
            periodo_nombre='Periodo Activo',
        )

    def get_docente_by_usuario_id(self, usuario_id: int) -> Optional[DocenteData]:
        if usuario_id <= 0:
            return None
        return DocenteData(
            usuario_id=usuario_id,
            nombre=f'Docente Demo {usuario_id}',
            email=f'docente{usuario_id}@buap.mx',
        )

    def get_alumnos_by_materia(self, materia_id: int) -> List[AlumnoData]:
        if materia_id <= 0:
            return []
        return [
            self.get_alumno(materia_id * 10 + i)
            for i in range(1, 4)
        ]


class GrpcDataProvider(NotificacionesDataProvider):
    """Datos reales vía gRPC a MS-2 y MS-3 (Fase C)."""

    def get_alumno(self, alumno_id: int) -> Optional[AlumnoData]:
        if alumno_id <= 0:
            return None
        info = alumnos_client.get_alumno_by_id(alumno_id)
        if not info.email:
            return None
        return AlumnoData(
            id=info.id,
            nombre=info.nombre,
            matricula=info.matricula,
            email=info.email,
        )

    def get_materia(self, materia_id: int) -> Optional[MateriaData]:
        if materia_id <= 0:
            return None
        info = periodos_client.get_materia_by_id(materia_id)
        if not info.nombre:
            return None
        return MateriaData(
            id=info.id,
            nombre=info.nombre,
            nrc=info.nrc,
            seccion=info.seccion,
            periodo_nombre=info.periodo_nombre or '',
        )

    def get_docente_by_usuario_id(self, usuario_id: int) -> Optional[DocenteData]:
        if usuario_id <= 0:
            return None
        info = alumnos_client.get_docente_by_usuario_id(usuario_id)
        email = info.email_institucional
        if not email:
            return None
        return DocenteData(
            usuario_id=info.usuario_id,
            nombre=info.nombre,
            email=email,
        )

    def get_alumnos_by_materia(self, materia_id: int) -> List[AlumnoData]:
        if materia_id <= 0:
            return []
        response = alumnos_client.get_alumnos_by_materia(materia_id)
        alumnos: List[AlumnoData] = []
        for info in response.alumnos:
            if not info.email:
                continue
            alumnos.append(
                AlumnoData(
                    id=info.id,
                    nombre=info.nombre,
                    matricula=info.matricula,
                    email=info.email,
                )
            )
        return alumnos
