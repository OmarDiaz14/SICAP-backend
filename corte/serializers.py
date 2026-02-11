from rest_framework import serializers

class CorteSerializer(serializers.Serializer):
    #el frontend manda el string  "YYYY-MM-DD" y el backend lo convierte a datetime
    fecha_inicio = serializers.DateField(format="%Y-%m-%d", input_formats=["%Y-%m-%d"])
    fecha_fin = serializers.DateField(format="%Y-%m-%d", input_formats=["%Y-%m-%d"])

    