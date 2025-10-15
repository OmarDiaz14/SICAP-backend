from django.db import models
from django.contrib.auth.hashers import make_password, check_password
# Create your models here.
class Cobrador(models.Model):
    ROLE_ADMIN = "admin"
    ROLE_SUPERVISOR = "supervisor"
    ROLE_COBRADOR = "cobrador"
    ROLE_CHOICES = [
        (ROLE_ADMIN, "Admin"),
        (ROLE_SUPERVISOR, "Supervisor"),
        (ROLE_COBRADOR, "Cobrador"),
    ]

    id_cobrador = models.AutoField(primary_key=True)
    nombre = models.CharField(max_length=25)
    apellidos = models.CharField(max_length=50)
    email = models.EmailField(max_length=256, unique=True)
    usuario = models.CharField(max_length=25, unique=True)
    password = models.CharField(max_length=256)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default=ROLE_COBRADOR)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    

    @property
    def is_authenticated(self) -> bool:
        return True  # DRF/permissions.IsAuthenticated lo usa

    @property
    def is_anonymous(self) -> bool:
        return False
    
    def set_password(self, raw_password: str):
        self.password = make_password(raw_password)

    def check_password(self, raw_password: str) -> bool:
        return check_password(raw_password, self.password)

    def save(self, *args, **kwargs):
        # normaliza usuario
        if self.usuario:
            self.usuario = self.usuario.strip().lower()

        # si la password no parece hash de Django, hashearla
        if self.password and not self.password.startswith('pbkdf2_'):
            self.password = make_password(self.password)

        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.nombre} {self.apellidos} ({self.usuario})"

    class Meta:
        ordering = ["id_cobrador"]
        verbose_name = "Cobrador"
        verbose_name_plural = "Cobradores"