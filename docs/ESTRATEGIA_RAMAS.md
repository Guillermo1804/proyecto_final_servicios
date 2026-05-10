# 🌿 Estrategia de Ramas en GitHub

## Ramas Principales

| Rama | Propósito | Protección |
|------|-----------|------------|
| `main` | Producción estable. Solo código probado y funcional | Requiere Pull Request para fusionar |
| `develop` | Integración activa. Aquí se juntan las features antes de ir a main | Rama de trabajo principal |

## Ramas de Feature (por microservicio)

Cada persona trabaja en su propia rama y hace PR a `develop`:

```
develop
├── feature/ms-auth            ← P1 trabaja aquí
├── feature/ms-periodos        ← P2 trabaja aquí
├── feature/ms-alumnos         ← P2 trabaja aquí
├── feature/ms-calificaciones  ← P3 trabaja aquí
├── feature/ms-asistencias     ← P3 trabaja aquí
├── feature/ms-notificaciones  ← P4 trabaja aquí
├── feature/ms-reportes        ← P4 trabaja aquí
├── feature/frontend           ← Quien trabaje frontend
├── feature/docker             ← P1 (infra)
└── feature/docs               ← P4 (documentación)
```

## Flujo de Trabajo

```
1. Crear rama:      git checkout develop && git pull && git checkout -b feature/ms-auth
2. Trabajar:        git add . && git commit -m "feat(ms-auth): implementar login JWT"
3. Push:            git push origin feature/ms-auth
4. Pull Request:    En GitHub, crear PR de feature/ms-auth → develop
5. Review + Merge:  Revisar y fusionar a develop
6. Release:         Cuando develop está estable → PR de develop → main
```

## Convención de Commits

```
feat(ms-auth): implementar login con JWT
fix(ms-periodos): corregir validación de periodo único activo
docs(readme): actualizar URLs de producción
chore(docker): agregar healthcheck a MySQL
refactor(ms-calificaciones): separar lógica de promedio
```

## Comandos Iniciales para Configurar

```bash
# Crear repo (ya hecho)
git init
git remote add origin https://github.com/EQUIPO/agm-backend.git

# Crear rama develop
git checkout -b develop
git push -u origin develop

# Cada persona crea su feature branch
git checkout develop
git checkout -b feature/ms-auth
git push -u origin feature/ms-auth
```

## Regla Importante
- **NUNCA hacer push directo a `main`**
- **Hacer commits frecuentes** (mínimo 3-5 por día por persona)
- El repo necesita **más de 20 commits** para no perder 10 puntos
- 4 personas × 10 días × 3 commits/día = 120 commits ✅
