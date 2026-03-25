from rest_framework import serializers
from rest_framework.exceptions import ValidationError as DRFValidationError
from django.core.exceptions import ValidationError as DjangoValidationError
from .models import Cobrador


class CobradorPublicSerializer(serializers.ModelSerializer):
    class Meta:
        model  = Cobrador
        fields = ("id_cobrador", "nombre", "apellidos", "usuario", "email", "role", "is_active")
        read_only_fields = fields


class LoginSerializer(serializers.Serializer):
    usuario  = serializers.CharField()
    password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        usuario  = attrs.get("usuario", "").strip().lower()
        password = attrs.get("password", "").strip()
        if not usuario or not password:
            raise serializers.ValidationError("Usuario y contraseña son requeridos.")
        attrs["usuario"] = usuario
        return attrs


class SignupSerializer(serializers.ModelSerializer):
    password  = serializers.CharField(write_only=True, min_length=6)
    password2 = serializers.CharField(write_only=True, min_length=6)

    class Meta:
        model  = Cobrador
        fields = ["nombre", "apellidos", "email", "usuario", "password", "password2"]

    def validate(self, attrs):
        if attrs["password"] != attrs["password2"]:
            raise serializers.ValidationError({"password2": "Las contraseñas no coinciden."})
        return attrs

    def create(self, validated_data):
        validated_data.pop("password2")
        password = validated_data.pop("password")

        cobrador = Cobrador(**validated_data)
        cobrador.set_password(password)
        cobrador.save()
        return cobrador


class AdminCreateUserSerializer(SignupSerializer):
    """Permite que un Admin cree usuarios asignando el rol explícitamente."""

    role = serializers.ChoiceField(choices=Cobrador.ROLE_CHOICES)

    class Meta(SignupSerializer.Meta):
        fields = ["nombre", "apellidos", "email", "usuario", "password", "password2", "role"]

    def validate(self, attrs):
        # Primero valida passwords (hereda de SignupSerializer)
        attrs = super().validate(attrs)

        # Solo admin o presidente pueden asignar el rol tesorero_sr
        role_solicitado = attrs.get("role")
        if role_solicitado == Cobrador.ROLE_TESORERO_SR:
            request = self.context.get("request")
            usuario_activo = request.user  # el que está haciendo la petición

            if usuario_activo.role not in {Cobrador.ROLE_ADMIN, Cobrador.ROLE_PRESIDENTE}:
                raise serializers.ValidationError(
                    {"role": "Solo el Admin o el Presidente pueden asignar el rol de Tesorero Sr."}
                )

        return attrs

    def create(self, validated_data):
        validated_data.pop("password2")
        password = validated_data.pop("password")

        try:
            cobrador = Cobrador(**validated_data)
            cobrador.set_password(password)
            cobrador.save()  
        except DjangoValidationError as e:
            raise DRFValidationError(e.message_dict)

        return cobrador