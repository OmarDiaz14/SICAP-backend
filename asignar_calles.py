import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sicap_backend.settings')
django.setup()

from django.db import connection
from calles.models import Calle

print("=" * 50)
print("PASO 1: Leyendo calles de cuentahabientes...")
print("=" * 50)

with connection.cursor() as cursor:
    cursor.execute("""
        SELECT DISTINCT calle 
        FROM cuentahabientes_cuentahabiente 
        WHERE calle IS NOT NULL AND TRIM(calle) != ''
        ORDER BY calle;
    """)
    calles_encontradas = cursor.fetchall()

print(f"Calles únicas encontradas: {len(calles_encontradas)}")
for (nombre,) in calles_encontradas:
    print(f"  - {nombre}")

if not calles_encontradas:
    print("\n❌ No se encontraron calles. Verifica que restauraste el backup correctamente.")
    exit()

print("\n" + "=" * 50)
print("PASO 2: Insertando calles en tabla calles...")
print("=" * 50)

creadas = 0
existentes = 0

for (nombre_calle,) in calles_encontradas:
    nombre_calle = nombre_calle.strip()
    calle_obj, created = Calle.objects.get_or_create(
        nombre_calle=nombre_calle,
        defaults={'activo': True}
    )
    if created:
        print(f"  ✅ Creada: '{nombre_calle}' (id: {calle_obj.id_calle})")
        creadas += 1
    else:
        print(f"  ⚠️  Ya existía: '{nombre_calle}' (id: {calle_obj.id_calle})")
        existentes += 1

print(f"\nCreadas: {creadas} | Ya existían: {existentes}")
print(f"Total calles en BD: {Calle.objects.count()}")

print("\n" + "=" * 50)
print("PASO 3: Asignando FK de calle a cada cuentahabiente...")
print("=" * 50)

# Construir mapa nombre -> id para no hacer queries dentro del loop
calles_map = {
    c.nombre_calle.strip(): c.id_calle 
    for c in Calle.objects.all()
}

with connection.cursor() as cursor:
    cursor.execute("""
        SELECT id_cuentahabiente, calle 
        FROM cuentahabientes_cuentahabiente 
        WHERE calle IS NOT NULL AND TRIM(calle) != '';
    """)
    cuentahabientes = cursor.fetchall()

print(f"Cuentahabientes a procesar: {len(cuentahabientes)}")

actualizados = 0
errores = 0

with connection.cursor() as cursor:
    for id_ch, nombre_calle in cuentahabientes:
        nombre_calle = nombre_calle.strip()
        id_calle = calles_map.get(nombre_calle)

        if id_calle:
            cursor.execute("""
                UPDATE cuentahabientes_cuentahabiente 
                SET calle_fk_id = %s 
                WHERE id_cuentahabiente = %s;
            """, [id_calle, id_ch])
            actualizados += 1
        else:
            print(f"  ❌ Calle no encontrada: '{nombre_calle}' (cuentahabiente id: {id_ch})")
            errores += 1

print(f"\n✅ Actualizados: {actualizados}")
print(f"❌ Errores: {errores}")

print("\n" + "=" * 50)
print("VERIFICACIÓN FINAL")
print("=" * 50)

with connection.cursor() as cursor:
    cursor.execute("""
        SELECT COUNT(*) FROM cuentahabientes_cuentahabiente 
        WHERE calle_fk_id IS NULL AND calle IS NOT NULL AND TRIM(calle) != '';
    """)
    sin_fk = cursor.fetchone()[0]

if sin_fk == 0:
    print("✅ Todos los cuentahabientes tienen su FK asignada correctamente.")
else:
    print(f"⚠️  {sin_fk} cuentahabientes con calle en texto pero sin FK asignada.")

