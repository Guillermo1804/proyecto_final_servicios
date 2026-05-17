import os
from concurrent import futures
from io import BytesIO
from unittest.mock import MagicMock, patch

import grpc
from django.test import SimpleTestCase

from apps.reportes.dto.report_dto import (
    AlumnoCalificacionRowDTO,
    CalificacionesReportDTO,
    MateriaEncabezadoDTO,
    StatsPeriodoDTO,
)
from grpc_server.servicer import ReportesServicer
from grpc_clients.exceptions import MateriaNotFound
from proto_generated import reportes_pb2, reportes_pb2_grpc


def _materia_dto() -> MateriaEncabezadoDTO:
    return MateriaEncabezadoDTO(
        materia_id=1,
        nrc='12345',
        nombre='Servicios Web',
        seccion='001',
        clave='COMP-456',
        docente_nombre='Dr. Pérez',
        docente_id=10,
        periodo_id=2,
        periodo_nombre='2026-1',
        horario='Lun',
    )


def _calif_dto() -> CalificacionesReportDTO:
    return CalificacionesReportDTO(
        materia=_materia_dto(),
        categorias=(),
        alumnos=(
            AlumnoCalificacionRowDTO(
                alumno_id=1,
                matricula='20240001',
                nombre='Ana',
                calificaciones=(),
                promedio_real=8.0,
                promedio_redondeado=8,
            ),
        ),
    )


class ReportesGrpcServicerTests(SimpleTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls._report_data = MagicMock()
        cls._estadisticas = MagicMock()
        cls._grpc_server = grpc.server(futures.ThreadPoolExecutor(max_workers=2))
        reportes_pb2_grpc.add_ReportesServiceServicer_to_server(
            ReportesServicer(
                report_data_service=cls._report_data,
                estadisticas_service=cls._estadisticas,
            ),
            cls._grpc_server,
        )
        cls._port = cls._grpc_server.add_insecure_port('[::]:0')
        cls._grpc_server.start()
        cls._channel = grpc.insecure_channel(f'localhost:{cls._port}')
        cls.stub = reportes_pb2_grpc.ReportesServiceStub(cls._channel)

    @classmethod
    def tearDownClass(cls):
        cls._channel.close()
        cls._grpc_server.stop(0)
        super().tearDownClass()

    @patch('apps.reportes.services.report_export.excel_generator.build_calificaciones_xlsx')
    def test_generate_report_calificaciones_xlsx(self, mock_xlsx):
        mock_xlsx.return_value = BytesIO(b'PK-fake-xlsx')
        self._report_data.fetch_calificaciones.return_value = _calif_dto()

        response = self.stub.GenerateReport(
            reportes_pb2.GenerateReportRequest(
                tipo='calificaciones',
                materia_id=1,
                formato='xlsx',
            )
        )

        self.assertTrue(response.success)
        self.assertTrue(response.archivo.startswith(b'PK'))
        self.assertIn('calificaciones_12345.xlsx', response.filename)
        self._report_data.fetch_calificaciones.assert_called_once_with(1)

    def test_generate_report_invalid_tipo(self):
        with self.assertRaises(grpc.RpcError) as ctx:
            self.stub.GenerateReport(
                reportes_pb2.GenerateReportRequest(
                    tipo='invalido',
                    materia_id=1,
                    formato='pdf',
                )
            )
        self.assertEqual(ctx.exception.code(), grpc.StatusCode.INVALID_ARGUMENT)

    def test_generate_report_materia_not_found(self):
        self._report_data.fetch_calificaciones.side_effect = MateriaNotFound(99)
        with self.assertRaises(grpc.RpcError) as ctx:
            self.stub.GenerateReport(
                reportes_pb2.GenerateReportRequest(
                    tipo='calificaciones',
                    materia_id=99,
                    formato='pdf',
                )
            )
        self.assertEqual(ctx.exception.code(), grpc.StatusCode.NOT_FOUND)

    def test_generate_report_sin_datos_not_found(self):
        dto = _calif_dto()
        dto = CalificacionesReportDTO(materia=dto.materia, categorias=(), alumnos=())
        self._report_data.fetch_calificaciones.return_value = dto
        with self.assertRaises(grpc.RpcError) as ctx:
            self.stub.GenerateReport(
                reportes_pb2.GenerateReportRequest(
                    tipo='calificaciones',
                    materia_id=1,
                    formato='xlsx',
                )
            )
        self.assertEqual(ctx.exception.code(), grpc.StatusCode.NOT_FOUND)

    def test_get_historial_docente_ok(self):
        self._estadisticas.historial_docente.return_value = (
            StatsPeriodoDTO(
                periodo_nombre='2026-1',
                periodo_id=2,
                materia_nombre='SW',
                materia_id=1,
                total_alumnos=20,
                aprobados=15,
                reprobados=5,
                promedio_grupal=7.5,
                porcentaje_asistencia=80.0,
            ),
        )

        response = self.stub.GetHistorialDocente(
            reportes_pb2.GetHistorialDocenteRequest(docente_id=10)
        )

        self.assertEqual(response.docente_id, 10)
        self.assertEqual(len(response.periodos), 1)
        self.assertEqual(response.periodos[0].aprobados, 15)
        self._estadisticas.historial_docente.assert_called_once_with(10)

    def test_get_historial_docente_invalid_id(self):
        with self.assertRaises(grpc.RpcError) as ctx:
            self.stub.GetHistorialDocente(
                reportes_pb2.GetHistorialDocenteRequest(docente_id=0)
            )
        self.assertEqual(ctx.exception.code(), grpc.StatusCode.INVALID_ARGUMENT)
