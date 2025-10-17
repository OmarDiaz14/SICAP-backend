# cuentahabientes/management/commands/import_base_excel.py
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from pathlib import Path
import datetime as dt
from decimal import Decimal

try:
    import openpyxl
except ImportError:
    raise CommandError("Falta openpyxl. Instala con: pip install openpyxl")

from cuentahabientes.models import Cuentahabiente
from colonia.models import Colonia
from servicio.models import Servicio
from pagos.models import Pago
from descuento.models import Descuento
from cobrador.models import Cobrador


# Variantes de encabezados aceptados
COLUMNAS = {
    "numero_contrato": {"Numero_contrato", "Contrato", "NumContrato", "NumeroContrato"},
    "nombres": {"Nombres", "Nombre"},
    "ap": {"Apellido paterno", "AP", "Apellido_paterno"},
    "am": {"Apellido materno", "AM", "Apellido_materno"},
    "calle": {"Calle"},
    "numero": {"Numero", "No", "Num"},
    "telefono": {"Telefono", "Teléfono"},
    "colonia": {"Colonia"},
    "mes": {"Mes"},
    "anio": {"Año", "Anio"},
    "saldo_pendiente": {"Saldo_pendiente", "Saldo", "SaldoPendiente"},
    "monto_recibido": {"Monto_recibido", "Pago", "Monto"},
    "monto_descuento": {"Monto_descuento", "Descuento"},
}


def _pick(row_values, headers, key, default=None, cast=None):
    """
    Devuelve el valor de la fila según las variantes de nombre en COLUMNAS.
    - row_values: lista con los valores (values_only=True)
    - headers: lista de nombres de encabezado normalizados (str)
    - key: la llave interna en COLUMNAS
    """
    posibles = COLUMNAS.get(key, {key})
    for i, h in enumerate(headers):
        if h in posibles:
            val = row_values[i] if i < len(row_values) else None
            if val is None or val == "":
                return default
            if cast:
                try:
                    return cast(val)
                except Exception:
                    return default
            return val
    return default


def _mes_a_num(mes: str) -> int:
    mes = (mes or "").strip().lower()
    mapa = {
        "enero": 1, "febrero": 2, "marzo": 3, "abril": 4,
        "mayo": 5, "junio": 6, "julio": 7, "agosto": 8,
        "septiembre": 9, "setiembre": 9, "octubre": 10,
        "noviembre": 11, "diciembre": 12,
    }
    return mapa.get(mes, 1)


class Command(BaseCommand):
    help = "Importa Cuentahabientes (+ pagos opcionales) desde un Excel."

    def add_arguments(self, parser):
        parser.add_argument("ruta_excel", type=str, help="Ruta del archivo .xlsx")
        parser.add_argument("--hoja", type=str, default=None,
                            help="Nombre de la hoja. Si no se indica, se usa la primera.")
        parser.add_argument("--servicio", type=str, required=True,
                            help="Nombre del Servicio a asignar a TODOS los cuentahabientes creados/actualizados.")
        parser.add_argument("--cobrador", type=str, required=True,
                            help="Usuario del cobrador que se asignará a los pagos creados.")
        parser.add_argument("--crear-pagos", action="store_true",
                            help="Si se indica, crea registros de Pago por fila con montos.")
        parser.add_argument("--dry-run", action="store_true",
                            help="Simula sin escribir cambios en la base de datos.")

    def handle(self, *args, **opts):
        ruta = Path(opts["ruta_excel"]).expanduser()
        if not ruta.exists():
            raise CommandError(f"No existe el archivo: {ruta}")

        hoja = opts["hoja"]
        dry = opts["dry_run"]
        crear_pagos = opts["crear_pagos"]
        servicio_nombre = opts["servicio"]
        cobrador_usuario = opts["cobrador"]

        # Validaciones previas
        try:
            servicio = Servicio.objects.get(nombre__iexact=servicio_nombre)
        except Servicio.DoesNotExist:
            raise CommandError(f"Servicio '{servicio_nombre}' no encontrado.")

        try:
            cobrador = Cobrador.objects.get(usuario__iexact=cobrador_usuario)
        except Cobrador.DoesNotExist:
            raise CommandError(f"Cobrador '{cobrador_usuario}' no encontrado.")

        # Descuentos conocidos (ajusta nombres si usas otros)
        desc_pp = Descuento.objects.filter(nombre_descuento__iexact="Promoción Anual").first()
        desc_inapam = Descuento.objects.filter(nombre_descuento__iexact="INAPAM").first()

        # Abre el Excel
        wb = openpyxl.load_workbook(ruta, data_only=True)
        ws = wb[hoja] if hoja else wb.worksheets[0]

        # === FIX DE HEADERS ===
        # Tomamos la primera fila como encabezados usando values_only=True
        headers = [ (c or "").strip() for c in next(ws.iter_rows(min_row=1, max_row=1, values_only=True)) ]

        creados = 0
        actualizados = 0
        pagos_creados = 0
        errores = 0

        # Usamos una transacción; si dry-run, marcamos rollback al final
        with transaction.atomic():
            try:
                for row_values in ws.iter_rows(min_row=2, values_only=True):
                    try:
                        numero_contrato = _pick(row_values, headers, "numero_contrato", cast=int)
                        if not numero_contrato:
                            # sin contrato -> saltamos
                            continue

                        nombres = (_pick(row_values, headers, "nombres", default="") or "").strip()
                        ap = (_pick(row_values, headers, "ap", default="") or "").strip()
                        am = (_pick(row_values, headers, "am", default="") or "").strip()
                        calle = (_pick(row_values, headers, "calle", default="S/N") or "").strip()
                        numero = _pick(row_values, headers, "numero", default=0, cast=int) or 0
                        telefono = (_pick(row_values, headers, "telefono", default="S/N") or "").strip()
                        nombre_colonia = (_pick(row_values, headers, "colonia", default="") or "").strip()

                        if not nombre_colonia:
                            raise CommandError(f"Colonia vacía (contrato {numero_contrato}).")

                        try:
                            colonia = Colonia.objects.get(nombre_colonia__iexact=nombre_colonia)
                        except Colonia.DoesNotExist:
                            raise CommandError(f"Colonia '{nombre_colonia}' no existe (contrato {numero_contrato}).")

                        saldo_pendiente = _pick(row_values, headers, "saldo_pendiente", default=None)
                        if saldo_pendiente is not None:
                            try:
                                saldo_pendiente = int(saldo_pendiente)
                            except Exception:
                                saldo_pendiente = None

                        saldo_inicial = (
                            saldo_pendiente
                            if saldo_pendiente is not None
                            else int(Decimal(servicio.costo))  # costo del servicio como base
                        )

                        ch, created = Cuentahabiente.objects.update_or_create(
                            numero_contrato=numero_contrato,
                            defaults={
                                "nombres": nombres,
                                "ap": ap,
                                "am": am,
                                "calle": calle,
                                "numero": numero,
                                "telefono": telefono,
                                "colonia": colonia,
                                "servicio": servicio,
                                "saldo_pendiente": saldo_inicial,
                                "deuda": "Al corriente" if saldo_inicial == 0 else "Con adeudo",
                            }
                        )
                        if created:
                            creados += 1
                        else:
                            actualizados += 1

                        if crear_pagos:
                            monto_recibido = _pick(row_values, headers, "monto_recibido", default=0)
                            try:
                                monto_recibido = int(monto_recibido or 0)
                            except Exception:
                                monto_recibido = 0

                            monto_descuento = _pick(row_values, headers, "monto_descuento", default=0)
                            try:
                                monto_descuento = int(monto_descuento or 0)
                            except Exception:
                                monto_descuento = 0

                            # Si hay movimiento, creamos pago
                            if monto_recibido > 0 or monto_descuento > 0:
                                mes = _pick(row_values, headers, "mes", default="Enero")
                                anio = _pick(row_values, headers, "anio", default=dt.date.today().year, cast=int)

                                # Fecha tentativa: primer día del mes
                                try:
                                    fecha_pago = dt.date(int(anio), _mes_a_num(mes), 1)
                                except Exception:
                                    fecha_pago = dt.date.today()

                                # Escoger descuento por monto
                                descuento = None
                                if monto_descuento == 60 and desc_pp:
                                    descuento = desc_pp
                                elif monto_descuento in (300, 360) and desc_inapam:
                                    descuento = desc_inapam

                                Pago.objects.create(
                                    descuento=descuento,
                                    cobrador=cobrador,
                                    cuentahabiente=ch,
                                    fecha_pago=fecha_pago,
                                    monto_recibido=monto_recibido,
                                    monto_descuento=monto_descuento,
                                    mes=str(mes),
                                    anio=int(anio),
                                )

                                # Actualizar saldo del cuentahabiente
                                nuevo_saldo = max(0, int(ch.saldo_pendiente) - (monto_recibido + monto_descuento))
                                ch.saldo_pendiente = nuevo_saldo
                                ch.deuda = "Al corriente" if nuevo_saldo == 0 else "Con adeudo"
                                ch.save(update_fields=["saldo_pendiente", "deuda"])

                                pagos_creados += 1

                    except Exception as e:
                        errores += 1
                        self.stderr.write(self.style.WARNING(f"[Fila] Error: {e}"))
                        continue

                if dry:
                    # No persistimos nada
                    transaction.set_rollback(True)

            except Exception:
                # Cualquier excepción revierte
                transaction.set_rollback(True)
                raise

        self.stdout.write(self.style.SUCCESS(
            f"OK. Creados {creados}, actualizados {actualizados}, pagos {pagos_creados}, errores {errores}."
        ))
