from rest_framework.permissions import BasePermission


class IsAdminRole(BasePermission):
    message = 'Se requiere rol admin.'

    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and getattr(request.user, 'rol', None) == 'admin')


class IsDocenteRole(BasePermission):
    message = 'Se requiere rol docente.'

    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and getattr(request.user, 'rol', None) == 'docente')


class IsAlumnoRole(BasePermission):
    message = 'Se requiere rol alumno.'

    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and getattr(request.user, 'rol', None) == 'alumno')