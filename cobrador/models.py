from django.db import models
from django.core.exceptions import ValidationError
from django.contrib.auth.hashers import make_password, check_password
# Create your models here.
class Cobrador(models.Model):
    #------ ROLES DE USUARIOS ------
    ROLE_ADMIN = "admin"
    ROLE_PRESIDENTE = "presidente"
    ROLE_COBRADOR = "cobrador"
    ROLE_SECRETARIO = "secretario"
    ROLE_TESORERO_JR = "tesorero_jr"
    ROLE_TESORERO_SR = "tesorero_sr"
    ROLE_CHOICES = [
        (ROLE_ADMIN, "Admin"),
        (ROLE_PRESIDENTE, "Presidente"),
        (ROLE_COBRADOR, "Cobrador"),
        (ROLE_SECRETARIO, "Secretario"),
        (ROLE_TESORERO_JR, "Tesorero Jr"), 
        (ROLE_TESORERO_SR, "Tesorero Sr"),
    ]

    UNIQUE_ROLES = {ROLE_PRESIDENTE, ROLE_TESORERO_SR}

    id_cobrador = models.AutoField(primary_key=True)
    nombre = models.CharField(max_length=25)
    apellidos = models.CharField(max_length=50)
    email = models.EmailField(max_length=256, unique=True)
    usuario = models.CharField(max_length=25, unique=True)
    password = models.CharField(max_length=256)
    role = models.CharField(
        max_length=20, 
        choices=ROLE_CHOICES, 
        default=ROLE_COBRADOR)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    # ─── Auth helpers (DRF)
    @property
    def is_authenticated(self) -> bool:
        return True  # DRF/permissions.IsAuthenticated lo usa

    @property
    def is_anonymous(self) -> bool:
        return False
    
    # ─── Password ────────
    def set_password(self, raw_password: str):
        self.password = make_password(raw_password)

    def check_password(self, raw_password: str) -> bool:
        return check_password(raw_password, self.password)
    
     # ─── Role helpers ────
    @property
    def is_admin(self) -> bool:
        return self.role == self.ROLE_ADMIN
    
    @property
    def is_presidente(self) -> bool:
        return self.role == self.ROLE_PRESIDENTE
    
    @property
    def is_cobrador(self) -> bool:
        return self.role == self.ROLE_COBRADOR
    
    @property
    def is_secretario(self) -> bool:
        return self.role == self.ROLE_SECRETARIO
    
    @property
    def is_tesorero_jr(self) -> bool:
        return self.role == self.ROLE_TESORERO_JR
    
    @property   
    def is_tesorero_sr(self) -> bool:
        return self.role == self.ROLE_TESORERO_SR
    
    def save(self, *args, **kwargs):
        if self.usuario:
            self.usuario = self.usuario.strip().lower()

        if self.password and not self.password.startswith("pbkdf2_"):
            self.password = make_password(self.password)

        
        self.full_clean()

        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.nombre} {self.apellidos} ({self.usuario}) [{self.get_role_display()}]"


        # ─── Validación roles únicos ──────────────────────────────────────────────
    def _validate_unique_role(self):
        """Impide crear un segundo registro con un rol de instancia única."""
        if self.role not in self.UNIQUE_ROLES:
            return

        qs = Cobrador.objects.filter(role=self.role, is_active=True)

        if self.pk:                    # al editar, excluirse a sí mismo
            qs = qs.exclude(pk=self.pk)

        if qs.exists():
            rol_display = dict(self.ROLE_CHOICES).get(self.role, self.role)
            raise ValidationError(
                {"role": f"Ya existe un '{rol_display}' activo. Solo puede haber uno."}
            )

    def clean(self):
        """Punto central de validaciones de negocio."""
        self._validate_unique_role()
    
    #------ Guardar y mostrar ------
    def save(self, *args, **kwargs):
        if self.usuario:
            self.usuario = self.usuario.strip().lower()

        if self.password and not self.password.startswith("pbkdf2_"):
            self.password = make_password(self.password)

        self.full_clean()   # ← dispara clean() → _validate_unique_role()

        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.nombre} {self.apellidos} ({self.usuario}) [{self.get_role_display()}]"

    class Meta:
        ordering            = ["id_cobrador"]
        verbose_name        = "Cobrador"
        verbose_name_plural = "Cobradores"