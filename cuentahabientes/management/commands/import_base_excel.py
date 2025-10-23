from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from pathlib import Path
import datetime as dt
from decimal import Decimal
from collections import defaultdict

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
    help = "Importa Cuentahabientes desde Excel con múltiples pagos por persona."

    def add_arguments(self, parser):
        parser.add_argument("ruta_excel", type=str, help="Ruta del archivo .xlsx")
        parser.add_argument("--hoja", type=str, default=None,
                            help="Nombre de la hoja. Si no se indica, se usa la primera.")
        parser.add_argument("--servicio", type=str, required=True,
                            help="Nombre del Servicio a asignar.")
        parser.add_argument("--cobrador", type=str, required=True,
                            help="Usuario del cobrador para los pagos.")
        parser.add_argument("--crear-pagos", action="store_true",
                            help="Crea registros de Pago por cada fila.")
        parser.add_argument("--generar-contratos", action="store_true",
                            help="Genera números de contrato automáticamente.")
        parser.add_argument("--base-contrato", type=int, default=10000,
                            help="Número base para generar contratos (default: 10000).")
        parser.add_argument("--dry-run", action="store_true",
                            help="Simula sin escribir cambios.")

    def handle(self, *args, **opts):
        ruta = Path(opts["ruta_excel"]).expanduser()
        if not ruta.exists():
            raise CommandError(f"No existe el archivo: {ruta}")

        hoja = opts["hoja"]
        dry = opts["dry_run"]
        crear_pagos = opts["crear_pagos"]
        generar_contratos = opts["generar_contratos"]
        base_contrato = opts["base_contrato"]
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

        desc_pp = Descuento.objects.filter(nombre_descuento__iexact="Promoción Anual").first()
        desc_inapam = Descuento.objects.filter(nombre_descuento__iexact="INAPAM").first()

        # Abre el Excel
        wb = openpyxl.load_workbook(ruta, data_only=True)
        ws = wb[hoja] if hoja else wb.worksheets[0]
        headers = [str(c or "").strip() for c in next(ws.iter_rows(min_row=1, max_row=1, values_only=True))]

        # === PASO 1: AGRUPAR DATOS POR CUENTAHABIENTE ===
        # Usamos diccionario con clave = (numero_contrato, nombres, ap, am, colonia)
        cuentahabientes_data = {}
        
        for row_values in ws.iter_rows(min_row=2, values_only=True):
            try:
                numero_contrato = _pick(row_values, headers, "numero_contrato", cast=int)
                nombres = (_pick(row_values, headers, "nombres", default="") or "").strip()
                ap = (_pick(row_values, headers, "ap", default="") or "").strip()
                am = (_pick(row_values, headers, "am", default="") or "").strip()
                nombre_colonia = (_pick(row_values, headers, "colonia", default="") or "").strip()

                # Si no hay datos mínimos, saltar
                if not nombres and not ap and not numero_contrato:
                    continue
                if not nombre_colonia:
                    continue

                # Crear una clave única para identificar al cuentahabiente
                # Si tiene número de contrato, usarlo como clave principal
                if numero_contrato:
                    clave = (numero_contrato, None, None, None, nombre_colonia)
                else:
                    # Sin contrato, usar nombre completo + colonia
                    clave = (None, nombres.lower(), ap.lower(), am.lower(), nombre_colonia)

                # Si no existe, inicializar
                if clave not in cuentahabientes_data:
                    cuentahabientes_data[clave] = {
                        "numero_contrato": numero_contrato,
                        "nombres": nombres,
                        "ap": ap,
                        "am": am,
                        "calle": (_pick(row_values, headers, "calle", default="S/N") or "").strip(),
                        "numero": _pick(row_values, headers, "numero", default=0, cast=int) or 0,
                        "telefono": (_pick(row_values, headers, "telefono", default="S/N") or "").strip(),
                        "colonia": nombre_colonia,
                        "pagos": []
                    }

                # Agregar pago a la lista
                monto_recibido = _pick(row_values, headers, "monto_recibido", default=0)
                try:
                    monto_recibido = int(monto_recibido or 0)
                except:
                    monto_recibido = 0

                monto_descuento = _pick(row_values, headers, "monto_descuento", default=0)
                try:
                    monto_descuento = int(monto_descuento or 0)
                except:
                    monto_descuento = 0

                # Solo agregar si hay movimiento
                if monto_recibido > 0 or monto_descuento > 0:
                    mes = _pick(row_values, headers, "mes", default="Enero")
                    anio = _pick(row_values, headers, "anio", default=dt.date.today().year, cast=int)
                    saldo_pendiente = _pick(row_values, headers, "saldo_pendiente", default=None)
                    
                    cuentahabientes_data[clave]["pagos"].append({
                        "mes": mes,
                        "anio": anio,
                        "monto_recibido": monto_recibido,
                        "monto_descuento": monto_descuento,
                        "saldo_pendiente": saldo_pendiente
                    })

            except Exception as e:
                self.stderr.write(self.style.WARNING(f"[Lectura] Error: {e}"))
                continue

        # === PASO 2: PROCESAR CUENTAHABIENTES ÚNICOS ===
        creados = 0
        actualizados = 0
        pagos_creados = 0
        errores = 0
        contratos_generados = 0

        # Si se va a generar contratos, obtener el último número usado
        if generar_contratos:
            ultimo_contrato = Cuentahabiente.objects.filter(
                numero_contrato__isnull=False
            ).order_by('-numero_contrato').values_list('numero_contrato', flat=True).first()
            
            proximo_contrato = max(base_contrato, (ultimo_contrato or 0) + 1) if ultimo_contrato else base_contrato
        else:
            proximo_contrato = None

        with transaction.atomic():
            try:
                for clave, datos in cuentahabientes_data.items():
                    try:
                        numero_contrato = datos["numero_contrato"]
                        nombre_colonia = datos["colonia"]

                        # Obtener colonia
                        try:
                            colonia = Colonia.objects.get(nombre_colonia__iexact=nombre_colonia)
                        except Colonia.DoesNotExist:
                            raise CommandError(f"Colonia '{nombre_colonia}' no existe.")

                        # Calcular saldo inicial (último saldo_pendiente de los pagos si existe)
                        saldo_inicial = None
                        if datos["pagos"]:
                            # Tomar el último saldo reportado
                            for pago in reversed(datos["pagos"]):
                                if pago["saldo_pendiente"] is not None:
                                    try:
                                        saldo_inicial = int(pago["saldo_pendiente"])
                                        break
                                    except:
                                        pass
                        
                        if saldo_inicial is None:
                            saldo_inicial = int(Decimal(servicio.costo))

                        # Crear o actualizar cuentahabiente
                        if numero_contrato:
                            ch, created = Cuentahabiente.objects.update_or_create(
                                numero_contrato=numero_contrato,
                                defaults={
                                    "nombres": datos["nombres"],
                                    "ap": datos["ap"],
                                    "am": datos["am"],
                                    "calle": datos["calle"],
                                    "numero": datos["numero"],
                                    "telefono": datos["telefono"],
                                    "colonia": colonia,
                                    "servicio": servicio,
                                    "saldo_pendiente": saldo_inicial,
                                    "deuda": "Al corriente" if saldo_inicial == 0 else "Con adeudo",
                                }
                            )
                        else:
                            # Sin contrato
                            if generar_contratos:
                                # Generar número automático
                                while Cuentahabiente.objects.filter(numero_contrato=proximo_contrato).exists():
                                    proximo_contrato += 1
                                
                                ch, created = Cuentahabiente.objects.update_or_create(
                                    numero_contrato=proximo_contrato,
                                    defaults={
                                        "nombres": datos["nombres"],
                                        "ap": datos["ap"],
                                        "am": datos["am"],
                                        "calle": datos["calle"],
                                        "numero": datos["numero"],
                                        "telefono": datos["telefono"],
                                        "colonia": colonia,
                                        "servicio": servicio,
                                        "saldo_pendiente": saldo_inicial,
                                        "deuda": "Al corriente" if saldo_inicial == 0 else "Con adeudo",
                                    }
                                )
                                contratos_generados += 1
                                proximo_contrato += 1
                            else:
                                # Buscar duplicado por nombre
                                ch = Cuentahabiente.objects.filter(
                                    nombres__iexact=datos["nombres"],
                                    ap__iexact=datos["ap"],
                                    am__iexact=datos["am"],
                                    colonia=colonia,
                                    numero_contrato__isnull=True
                                ).first()
                                
                                if ch:
                                    ch.calle = datos["calle"]
                                    ch.numero = datos["numero"]
                                    ch.telefono = datos["telefono"]
                                    ch.servicio = servicio
                                    ch.saldo_pendiente = saldo_inicial
                                    ch.deuda = "Al corriente" if saldo_inicial == 0 else "Con adeudo"
                                    ch.save()
                                    created = False
                                else:
                                    ch = Cuentahabiente.objects.create(
                                        numero_contrato=None,
                                        nombres=datos["nombres"],
                                        ap=datos["ap"],
                                        am=datos["am"],
                                        calle=datos["calle"],
                                        numero=datos["numero"],
                                        telefono=datos["telefono"],
                                        colonia=colonia,
                                        servicio=servicio,
                                        saldo_pendiente=saldo_inicial,
                                        deuda="Al corriente" if saldo_inicial == 0 else "Con adeudo",
                                    )
                                    created = True

                        if created:
                            creados += 1
                        else:
                            actualizados += 1

                        # Crear todos los pagos de este cuentahabiente
                        if crear_pagos:
                            for pago_data in datos["pagos"]:
                                try:
                                    fecha_pago = dt.date(
                                        int(pago_data["anio"]), 
                                        _mes_a_num(pago_data["mes"]), 
                                        1
                                    )
                                except:
                                    fecha_pago = dt.date.today()

                                # Determinar descuento
                                descuento = None
                                monto_desc = pago_data["monto_descuento"]
                                if monto_desc == 60 and desc_pp:
                                    descuento = desc_pp
                                elif monto_desc in (300, 360) and desc_inapam:
                                    descuento = desc_inapam

                                Pago.objects.create(
                                    descuento=descuento,
                                    cobrador=cobrador,
                                    cuentahabiente=ch,
                                    fecha_pago=fecha_pago,
                                    monto_recibido=pago_data["monto_recibido"],
                                    monto_descuento=pago_data["monto_descuento"],
                                    mes=str(pago_data["mes"]),
                                    anio=int(pago_data["anio"]),
                                )
                                pagos_creados += 1

                    except Exception as e:
                        errores += 1
                        self.stderr.write(self.style.WARNING(f"[Procesamiento] Error: {e}"))
                        continue

                if dry:
                    transaction.set_rollback(True)

            except Exception:
                transaction.set_rollback(True)
                raise

        msg = f"OK. Cuentahabientes únicos: {len(cuentahabientes_data)} | "
        msg += f"Creados: {creados}, Actualizados: {actualizados} | "
        msg += f"Pagos: {pagos_creados}"
        if generar_contratos:
            msg += f" | Contratos generados: {contratos_generados}"
        msg += f" | Errores: {errores}"
        
        self.stdout.write(self.style.SUCCESS(msg))