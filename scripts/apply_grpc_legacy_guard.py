"""Aplica block_business_grpc a clientes gRPC legacy (Fase 9)."""

from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

HEADER = (
    '"""DEPRECATED (Fase 9): cliente gRPC de negocio. Bloqueado con USE_EVENT_BUS=true."""\n'
    'from agm_events.grpc_legacy import block_business_grpc\n\n'
)

TARGETS = [
    'ms-reportes/grpc_clients/periodos_client.py',
    'ms-reportes/grpc_clients/alumnos_client.py',
    'ms-reportes/grpc_clients/calificaciones_client.py',
    'ms-reportes/grpc_clients/asistencias_client.py',
    'ms-reportes/grpc_clients/auth_client.py',
    'ms-calificaciones/grpc_clients/__init__.py',
    'ms-asistencias/grpc_clients.py',
    'ms-periodos/grpc_clients/auth_client.py',
    'ms-notificaciones/grpc_clients/alumnos_client.py',
    'ms-notificaciones/grpc_clients/periodos_client.py',
    'ms-notificaciones/grpc_clients/auth_client.py',
    'ms-alumnos/grpc_clients/auth_client.py',
    'ms-alumnos/grpc_clients/periodos_client.py',
    'ms-alumnos/utils/auth_client.py',
    'ms-alumnos/utils/notificaciones_client.py',
    'ms-alumnos/utils/periodos_client.py',
    'ms-calificaciones/utils/notificaciones_client.py',
]


def guard_file(path: Path) -> None:
    text = path.read_text(encoding='utf-8')
    if 'block_business_grpc' in text:
        print('skip', path)
        return
    if text.startswith('"""'):
        end = text.find('"""', 3)
        insert_at = end + 3
        while insert_at < len(text) and text[insert_at] in '\r\n':
            insert_at += 1
        text = text[:insert_at] + '\n\n' + HEADER + text[insert_at:]
    else:
        lines = text.splitlines()
        last_imp = 0
        for i, line in enumerate(lines):
            if line.startswith('import ') or line.startswith('from '):
                last_imp = i
        lines.insert(last_imp + 1, '')
        lines.insert(last_imp + 2, HEADER.strip())
        text = '\n'.join(lines) + ('\n' if text.endswith('\n') else '')

    def repl(m: re.Match) -> str:
        name = m.group(1)
        args = m.group(2)
        ret = m.group(3) or ''
        return (
            f'def {name}({args}){ret}:\n'
            f"    block_business_grpc('{path.name}.{name}')"
        )

    text = re.sub(
        r'^def ([a-zA-Z0-9_]+)\(([^)]*)\)(\s*->[^:]+)?:',
        repl,
        text,
        flags=re.MULTILINE,
    )
    path.write_text(text, encoding='utf-8')
    print('patched', path)


def main() -> None:
    for rel in TARGETS:
        p = ROOT / rel
        if p.exists():
            guard_file(p)


if __name__ == '__main__':
    main()
