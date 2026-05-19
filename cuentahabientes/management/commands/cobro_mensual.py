from datetime import date
from decimal import Decimal

from django.core.management.base import BaseCommand
from django.db import transaction

from cuentahabientes.models import Cuentahabiente


class Command(BaseCommand):
    help = "Cobro mensual automático: suma tarifa/12 al saldo_pendiente de cuentas parciales."

    def add_arguments(self, parser):
        parser.add_argument("--anio", type=int, default=None)
        parser.add_argument("--mes",  type=int, default=None)

    def handle(self, *args, **options):
        hoy  = date.today()
        anio = options["anio"] or hoy.year
        mes  = options["mes"]  or hoy.month

        self.stdout.write(f"\n[cobro_mensual] Iniciando {mes}/{anio}...\n")

        primer_dia_mes = date(anio, mes, 1)

        # Cuentas parciales activas este mes
        cuentas = list(
            Cuentahabiente.objects
            .filter(
                tipo_cuenta="parcial",
                fecha_activacion__isnull=False,
            )
            .exclude(
                fecha_desactivacion__lt=primer_dia_mes
            )
            .select_related("servicio")
        )

        cuentas_a_actualizar = []
        omitidas             = []

        for cuenta in cuentas:
            tarifa = cuenta.tarifa_mensual

            if tarifa <= Decimal("0"):
                continue

            # ── Regla del día 15: ACTIVACIÓN en este mismo mes ────────
            if (
                cuenta.fecha_activacion.year  == anio and
                cuenta.fecha_activacion.month == mes
            ):
                if not Cuentahabiente.aplica_cobro_por_dia(cuenta.fecha_activacion.day):
                    # Activada después del 15 → ya se omitió en /activar/
                    # El cron tampoco la cobra, empieza el mes siguiente
                    omitidas.append(cuenta.numero_contrato)
                    self.stdout.write(
                        f"  ↷ Contrato {cuenta.numero_contrato}: "
                        f"activado el día {cuenta.fecha_activacion.day} "
                        f"(después del 15) → omitido"
                    )
                    continue

            # ── Regla del día 15: DESACTIVACIÓN en este mismo mes ─────
            if (
                cuenta.fecha_desactivacion and
                cuenta.fecha_desactivacion.year  == anio and
                cuenta.fecha_desactivacion.month == mes
            ):
                # En ambos casos se omite: el cargo de desactivación
                # ya fue manejado en /desactivar/ si aplicaba
                omitidas.append(cuenta.numero_contrato)
                self.stdout.write(
                    f"  ↷ Contrato {cuenta.numero_contrato}: "
                    f"desactivado el día {cuenta.fecha_desactivacion.day} "
                    f"→ ya manejado en desactivación, omitido del cron"
                )
                continue

            # ── Suma la tarifa mensual al saldo_pendiente ─────────────
            cuenta.saldo_pendiente = (
                Decimal(str(cuenta.saldo_pendiente)) + tarifa
            )
            cuenta.deuda = "adeudo"
            cuentas_a_actualizar.append(cuenta)

            self.stdout.write(
                f"  ✓ Contrato {cuenta.numero_contrato}: "
                f"+${tarifa} → saldo ${cuenta.saldo_pendiente}"
            )

        # ── Guardar todo de una vez ───────────────────────────────────
        with transaction.atomic():
            if cuentas_a_actualizar:
                Cuentahabiente.objects.bulk_update(
                    cuentas_a_actualizar,
                    ["saldo_pendiente", "deuda"],
                    batch_size=500,
                )

        self.stdout.write(self.style.SUCCESS(
            f"\n[cobro_mensual] ✓ Completado {mes}/{anio}\n"
            f"  Cuentas actualizadas : {len(cuentas_a_actualizar)}\n"
            f"  Cuentas omitidas     : {len(omitidas)}\n"
        ))