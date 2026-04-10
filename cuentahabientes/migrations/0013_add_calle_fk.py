from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('calles', '0001_initial'),
        ('cuentahabientes', '0012_alter_cierreanual_anio'),  # <- pon aquí tu última migración válida
    ]

    operations = [
        # Solo agrega la columna FK, no toca la columna calle existente
        migrations.AddField(
            model_name='cuentahabiente',
            name='calle_fk',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                to='calles.calle',
            ),
        ),
    ]