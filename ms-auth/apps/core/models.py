from django.db import models
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, BaseUserManager
from uuid import uuid4

class UserManager(BaseUserManager):
    def create_user(self, email, nombre, rol, password=None):
        if not email:
            raise ValueError('El email es obligatorio')
        user = self.model(email=email, nombre=nombre, rol=rol)
        user.set_password(password)
        user.save(using=self._db)
        return user
    
    def create_superuser(self, email, nombre, password):
        user = self.create_user(email, nombre, 'admin', password)
        user.is_staff = True
        user.is_superuser = True
        user.save(using=self._db)
        return user


class User(AbstractBaseUser, PermissionsMixin):
    ROLE_CHOICES = [
        ('admin', 'Administrador'),
        ('docente', 'Docente'),
        ('alumno', 'Alumno'),
    ]
    
    id = models.AutoField(primary_key=True)
    email = models.EmailField(unique=True, max_length=255)
    nombre = models.CharField(max_length=255)
    rol = models.CharField(max_length=20, choices=ROLE_CHOICES)
    activo = models.BooleanField(default=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)
    
    # Campos necesarios para Django admin
    is_staff = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    is_superuser = models.BooleanField(default=False)
    
    objects = UserManager()
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['nombre', 'rol']
    
    class Meta:
        db_table = 'core_user'
        verbose_name = 'Usuario'
        verbose_name_plural = 'Usuarios'
    
    def __str__(self):
        return self.email


class PasswordResetToken(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    token = models.UUIDField(default=uuid4, unique=True)
    expira_en = models.DateTimeField()
    usado = models.BooleanField(default=False)
    creado_en = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'core_password_reset_token'
        verbose_name = 'Token de Reset'
        verbose_name_plural = 'Tokens de Reset'
    
    def __str__(self):
        return f"{self.user.email} - {self.token}"


class EventOutbox(models.Model):
    """Transactional Outbox — publicacion asincrona a RabbitMQ."""

    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        PUBLISHED = "published", "Published"
        FAILED = "failed", "Failed"

    event_id = models.UUIDField(primary_key=True, editable=False)
    event_name = models.CharField(max_length=128)
    event_version = models.PositiveIntegerField(default=1)
    aggregate_type = models.CharField(max_length=64)
    aggregate_id = models.CharField(max_length=64)
    payload = models.JSONField()
    status = models.CharField(
        max_length=16,
        choices=Status.choices,
        default=Status.PENDING,
        db_index=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    processed_at = models.DateTimeField(null=True, blank=True)
    retry_count = models.PositiveIntegerField(default=0)
    last_error = models.TextField(null=True, blank=True)

    class Meta:
        db_table = "event_outbox"
        indexes = [
            models.Index(fields=["status", "created_at"], name="idx_outbox_status_created"),
        ]
        verbose_name = "Evento outbox"
        verbose_name_plural = "Eventos outbox"

    def __str__(self) -> str:
        return f"{self.event_name} ({self.event_id}) — {self.status}"


class EventInbox(models.Model):
    """Inbox — idempotencia de consumo de eventos."""

    event_id = models.UUIDField(primary_key=True, editable=False)
    event_name = models.CharField(max_length=128)
    processed_at = models.DateTimeField(auto_now_add=True)
    handler = models.CharField(max_length=128)

    class Meta:
        db_table = "event_inbox"
        verbose_name = "Evento inbox"
        verbose_name_plural = "Eventos inbox"

    def __str__(self) -> str:
        return f"{self.event_name} ({self.event_id})"
