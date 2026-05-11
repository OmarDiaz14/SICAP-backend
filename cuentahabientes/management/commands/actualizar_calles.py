# Ubicación: cuentahabientes/management/commands/actualizar_calles.py

import csv
from pathlib import Path
from django.core.management.base import BaseCommand, CommandError
from cuentahabientes.models import Cuentahabiente


class Command(BaseCommand):
    help = "Actualiza el campo 'calle' de los cuentahabientes desde un archivo CSV"

    def add_arguments(self, parser):
        parser.add_argument(
            "csv_file",
            type=str,
            help="Ruta del archivo CSV con las calles actualizadas",
        )

    def handle(self, *args, **options):
        csv_path = Path(options["csv_file"])

        if not csv_path.exists():
            raise CommandError(f"No se encontró el archivo: {csv_path}")

        actualizados    = 0
        no_encontrados  = 0
        errores         = 0

        with open(csv_path, encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)

            for row in reader:
                id_cuentahabiente = int(row["id_cuentahabiente"].strip())
                nueva_calle       = row["calle"].strip()

                try:
                    cuenta = Cuentahabiente.objects.get(id_cuentahabiente=id_cuentahabiente)
                    cuenta.calle = nueva_calle
                    cuenta.save(update_fields=["calle"])
                    actualizados += 1

                except Cuentahabiente.DoesNotExist:
                    self.stdout.write(
                        self.style.WARNING(
                            f"  ⚠ No encontrado: id_cuentahabiente = {id_cuentahabiente}"
                        )
                    )
                    no_encontrados += 1

                except Exception as e:
                    self.stdout.write(
                        self.style.ERROR(f"  ✗ Error en id {id_cuentahabiente}: {e}")
                    )
                    errores += 1

        self.stdout.write(self.style.SUCCESS(f"\n✔ Actualizados:    {actualizados}"))
        self.stdout.write(self.style.WARNING(f"⚠ No encontrados: {no_encontrados}"))
        if errores:
            self.stdout.write(self.style.ERROR(f"✗ Errores:         {errores}"))
        self.stdout.write("Proceso completado.")