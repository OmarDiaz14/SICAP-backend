from rest_framework import serializers
from .models import Cobrador


class CobradorPublicSerializer(serializers.ModelSerializer):
    class Meta:
        model = Cobrador
        fields = ("id_cobrador", "nombre", "apellidos", "usuario", "email")
        read_only_fields = fields


class LoginSerializer(serializers.Serializer):
    usuario = serializers.CharField()
    password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        usuario = attrs.get("usuario", "").strip()
        password = attrs.get("password", "").strip()
        if not usuario or not password:
            raise serializers.ValidationError("Usuario y contraseña son requeridos.")
        attrs["usuario"] = usuario
        return attrs
    
class SignupSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True,min_length=6)
    password2 = serializers.CharField(write_only=True,min_length=6)

    class Meta: 
        model = Cobrador
        fields = ['nombre','apellidos','email','usuario','password','password2']

    def validate(self, attrs):
        if attrs['password'] != attrs['password2']:
            raise serializers.ValidationError("Las contraseñas no coinciden.")
        return attrs
    
    def create (self, validated_data):
        validated_data.pop('password2')
        #Normmiza el usuario (opcional si asi lo decidimos)
        usuario = validated_data.get('usuario','').strip().lower()
        validated_data['usuario'] = usuario
        #crea y hashea usanndo set_password / save ()
        password = validated_data.pop('password')
        cobrador = Cobrador(**validated_data)
        cobrador.set_password(password)
        cobrador.save()
        return cobrador