# cuentahabientes/migrations/0017_estadocuentanew_reportecargos_reportepadrongeneral_and_more.py

import cuentahabientes.models_views
from django.db import migrations, models


VISTAS_A_BORRAR = [
    "r_cuentahabientes",
    "vista_pagos",
    "vista_historial",
    "vista_deudores",
    "vista_progreso",
    "estado_cuenta",
    "estado_cuenta_resumen",
    "vista_cargos",
    "estado_cuenta_new",
    "reporte_cargos",
    "reporte_padron_general",
]


def drop_views(apps, schema_editor):
    with schema_editor.connection.cursor() as cursor:
        for vista in VISTAS_A_BORRAR:
            cursor.execute(f'DROP VIEW IF EXISTS "{vista}" CASCADE;')


def recreate_views(apps, schema_editor):
    # La tabla ya fue renombrada a "cuentahabiente" por AlterModelTable
    # Todas las referencias usan el nombre nuevo
    with schema_editor.connection.cursor() as cursor:

        cursor.execute("""
            CREATE OR REPLACE VIEW r_cuentahabientes AS
            SELECT c.id_cuentahabiente,
                c.numero_contrato,
                concat(c.nombres, ' ', c.ap, ' ', c.am) AS nombre,
                c.calle,
                co.nombre_colonia,
                c.telefono,
                c.saldo_pendiente,
                sum(p.monto_recibido) AS total_pagado,
                c.deuda AS estatus
            FROM ((cuentahabiente c
                JOIN colonia_colonia co ON ((co.id_colonia = c.colonia_id)))
                LEFT JOIN pagos_pago p ON ((p.cuentahabiente_id = c.id_cuentahabiente)))
            GROUP BY c.id_cuentahabiente, c.nombres, c.ap, c.am, co.nombre_colonia
            ORDER BY c.id_cuentahabiente;
        """)

        cursor.execute("""
            CREATE OR REPLACE VIEW vista_pagos AS
            WITH "años_operativos" AS (
                SELECT DISTINCT pagos_pago.anio
                FROM pagos_pago
                UNION
                SELECT (EXTRACT(year FROM CURRENT_DATE))::integer AS "extract"
            ), universo_cuentahabientes AS (
                SELECT c_1.id_cuentahabiente,
                    a.anio
                FROM (cuentahabiente c_1
                    CROSS JOIN "años_operativos" a)
            ), pagos_agrupados AS (
                SELECT p.cuentahabiente_id,
                    p.anio,
                    sum(COALESCE(p.monto_recibido, 0)) AS pagos_totales,
                    sum(((COALESCE(p.monto_recibido, 0))::numeric + COALESCE(d.porcentaje, (0)::numeric))) AS pagos_acreditados
                FROM (pagos_pago p
                    LEFT JOIN descuento_descuento d ON ((p.descuento_id = d.id_descuento)))
                GROUP BY p.cuentahabiente_id, p.anio
            )
            SELECT row_number() OVER (ORDER BY uc.anio DESC, c.numero_contrato) AS id,
                c.numero_contrato,
                concat(TRIM(BOTH FROM c.nombres), ' ', TRIM(BOTH FROM c.ap), ' ', TRIM(BOTH FROM c.am)) AS nombre_completo,
                s.nombre AS nombre_servicio,
                uc.anio,
                COALESCE(pa.pagos_totales, (0)::bigint) AS pagos_totales,
                GREATEST((s.costo - COALESCE(pa.pagos_acreditados, (0)::numeric)), (0)::numeric) AS saldo_pendiente,
                CASE
                    WHEN (s.costo IS NULL) THEN 'Sin servicio'::text
                    WHEN (COALESCE(pa.pagos_acreditados, (0)::numeric) >= s.costo) THEN 'Pagado'::text
                    WHEN ((uc.anio = (EXTRACT(year FROM CURRENT_DATE))::integer) AND (COALESCE(pa.pagos_totales, (0)::bigint) > 0)) THEN 'Corriente'::text
                    ELSE 'Adeudo'::text
                END AS estatus_deuda,
                c.calle
            FROM (((universo_cuentahabientes uc
                JOIN cuentahabiente c ON ((uc.id_cuentahabiente = c.id_cuentahabiente)))
                LEFT JOIN servicio s ON ((c.servicio_id = s.id_tipo_servicio)))
                LEFT JOIN pagos_agrupados pa ON (((uc.id_cuentahabiente = pa.cuentahabiente_id) AND (uc.anio = pa.anio))));
        """)

        cursor.execute("""
            CREATE OR REPLACE VIEW vista_historial AS
            SELECT row_number() OVER (ORDER BY p.fecha_pago DESC, c.numero_contrato) AS id,
                c.numero_contrato,
                p.fecha_pago,
                p.monto_recibido,
                p.mes,
                p.anio,
                concat(co.nombre, ' ', co.apellidos) AS cobrador,
                d.nombre_descuento,
                p.comentarios
            FROM (((pagos_pago p
                JOIN cuentahabiente c ON ((p.cuentahabiente_id = c.id_cuentahabiente)))
                LEFT JOIN descuento_descuento d ON ((p.descuento_id = d.id_descuento)))
                LEFT JOIN cobrador_cobrador co ON ((p.cobrador_id = co.id_cobrador)))
            ORDER BY p.fecha_pago DESC, c.numero_contrato;
        """)

        cursor.execute("""
            CREATE OR REPLACE VIEW vista_deudores AS
            SELECT c.id_cuentahabiente,
                concat(c.nombres, ' ', c.ap, ' ', c.am) AS nombre_cuentahabiente,
                sum(p.monto_recibido) AS monto_total,
                c.deuda AS estatus,
                col.nombre_colonia
            FROM ((pagos_pago p
                JOIN cuentahabiente c ON ((p.cuentahabiente_id = c.id_cuentahabiente)))
                JOIN colonia_colonia col ON ((c.colonia_id = col.id_colonia)))
            GROUP BY c.id_cuentahabiente, c.nombres, c.deuda, col.nombre_colonia;
        """)

        cursor.execute("""
            CREATE OR REPLACE VIEW vista_progreso AS
            WITH anios_operativos AS (
                SELECT DISTINCT pagos_pago.anio
                FROM pagos_pago
                UNION
                SELECT (EXTRACT(year FROM CURRENT_DATE))::integer AS "extract"
                UNION
                SELECT ((EXTRACT(year FROM cargos_cargo.fecha_cargo) - (1)::numeric))::integer AS int4
                FROM cargos_cargo
                WHERE ((cargos_cargo.tipo_cargo_id = 1) AND (cargos_cargo.fecha_cargo IS NOT NULL))
            ), universo_cuentahabientes AS (
                SELECT c.id_cuentahabiente,
                    c.numero_contrato,
                    c.nombres,
                    c.ap,
                    c.am,
                    c.servicio_id,
                    a.anio
                FROM (cuentahabiente c
                    CROSS JOIN anios_operativos a)
            ), pagos_agrupados AS (
                SELECT p.cuentahabiente_id,
                    p.anio,
                    sum(COALESCE(p.monto_recibido, 0)) AS pagos_totales,
                    sum(((COALESCE(p.monto_recibido, 0))::numeric + COALESCE(d.porcentaje, (0)::numeric))) AS pagos_acreditados
                FROM (pagos_pago p
                    LEFT JOIN descuento_descuento d ON ((p.descuento_id = d.id_descuento)))
                GROUP BY p.cuentahabiente_id, p.anio
            ), pagos_cargos_agrupados AS (
                SELECT c.cuentahabiente_id,
                    ((EXTRACT(year FROM c.fecha_cargo) - (1)::numeric))::integer AS anio_deuda,
                    sum(COALESCE(pc.monto_recibido, (0)::numeric)) AS pagos_cargo_totales
                FROM (cargos_cargo c
                    JOIN pagos_cargos pc ON ((c.id_cargo = pc.cargo_id)))
                WHERE (c.tipo_cargo_id = 1)
                GROUP BY c.cuentahabiente_id, (EXTRACT(year FROM c.fecha_cargo))
            )
            SELECT uc.numero_contrato,
                concat(TRIM(BOTH FROM uc.nombres), ' ', TRIM(BOTH FROM uc.ap), ' ', TRIM(BOTH FROM uc.am)) AS nombre,
                CASE
                    WHEN (s.costo IS NULL) THEN 'Sin servicio'::text
                    WHEN ((COALESCE(pa.pagos_acreditados, (0)::numeric) + COALESCE(pca.pagos_cargo_totales, (0)::numeric)) >= s.costo) THEN 'Pagado'::text
                    WHEN ((uc.anio = (EXTRACT(year FROM CURRENT_DATE))::integer) AND (((COALESCE(pa.pagos_totales, (0)::bigint))::numeric + COALESCE(pca.pagos_cargo_totales, (0)::numeric)) > (0)::numeric)) THEN 'Corriente'::text
                    ELSE 'Adeudo'::text
                END AS estatus,
                uc.anio AS anio_pago,
                ((COALESCE(pa.pagos_totales, (0)::bigint))::numeric + COALESCE(pca.pagos_cargo_totales, (0)::numeric)) AS total,
                GREATEST((s.costo - (COALESCE(pa.pagos_acreditados, (0)::numeric) + COALESCE(pca.pagos_cargo_totales, (0)::numeric))), (0)::numeric) AS saldo,
                CASE
                    WHEN (s.costo > (0)::numeric) THEN ((round((((COALESCE(pa.pagos_acreditados, (0)::numeric) + COALESCE(pca.pagos_cargo_totales, (0)::numeric)) / (s.costo)::numeric) * (100)::numeric), 2))::text || '%'::text)
                    ELSE '0%'::text
                END AS progreso,
                uc.id_cuentahabiente
            FROM (((universo_cuentahabientes uc
                LEFT JOIN servicio s ON ((uc.servicio_id = s.id_tipo_servicio)))
                LEFT JOIN pagos_agrupados pa ON (((uc.id_cuentahabiente = pa.cuentahabiente_id) AND (uc.anio = pa.anio))))
                LEFT JOIN pagos_cargos_agrupados pca ON (((uc.id_cuentahabiente = pca.cuentahabiente_id) AND (uc.anio = pca.anio_deuda))))
            ORDER BY uc.numero_contrato, uc.anio;
        """)

        cursor.execute("""
            CREATE OR REPLACE VIEW estado_cuenta_resumen AS
            WITH anios_operativos AS (
                SELECT DISTINCT pagos_pago.anio
                FROM pagos_pago
                WHERE (pagos_pago.anio IS NOT NULL)
                UNION
                SELECT (EXTRACT(year FROM CURRENT_DATE))::integer AS "extract"
                UNION
                SELECT ((EXTRACT(year FROM cargos_cargo.fecha_cargo) - (1)::numeric))::integer AS int4
                FROM cargos_cargo
                WHERE ((cargos_cargo.tipo_cargo_id = 1) AND (cargos_cargo.fecha_cargo IS NOT NULL))
            ), universo_cuentahabientes AS (
                SELECT c.id_cuentahabiente,
                    c.numero_contrato,
                    c.servicio_id,
                    a.anio
                FROM (cuentahabiente c
                    CROSS JOIN anios_operativos a)
            ), pagos_agrupados AS (
                SELECT p.cuentahabiente_id,
                    p.anio,
                    sum(COALESCE(p.monto_recibido, 0)) AS pagos_totales,
                    sum(((COALESCE(p.monto_recibido, 0))::numeric + COALESCE(d.porcentaje, (0)::numeric))) AS pagos_acreditados
                FROM (pagos_pago p
                    LEFT JOIN descuento_descuento d ON ((p.descuento_id = d.id_descuento)))
                GROUP BY p.cuentahabiente_id, p.anio
            ), pagos_cargos_agrupados AS (
                SELECT c.cuentahabiente_id,
                    ((EXTRACT(year FROM c.fecha_cargo) - (1)::numeric))::integer AS anio_deuda,
                    sum(COALESCE(pc.monto_recibido, (0)::numeric)) AS pagos_cargo_totales
                FROM (cargos_cargo c
                    JOIN pagos_cargos pc ON ((c.id_cargo = pc.cargo_id)))
                WHERE (c.tipo_cargo_id = 1)
                GROUP BY c.cuentahabiente_id, (EXTRACT(year FROM c.fecha_cargo))
            )
            SELECT row_number() OVER (ORDER BY uc.numero_contrato, uc.anio) AS id,
                uc.id_cuentahabiente,
                uc.numero_contrato,
                uc.anio,
                s.nombre AS nombre_servicio,
                CASE
                    WHEN (s.costo IS NULL) THEN 'Sin servicio'::text
                    WHEN ((COALESCE(pa.pagos_acreditados, (0)::numeric) + COALESCE(pca.pagos_cargo_totales, (0)::numeric)) >= s.costo) THEN 'Pagado'::text
                    WHEN (((COALESCE(pa.pagos_totales, (0)::bigint))::numeric + COALESCE(pca.pagos_cargo_totales, (0)::numeric)) > (0)::numeric) THEN 'Corriente'::text
                    ELSE 'Adeudo'::text
                END AS estatus,
                GREATEST((s.costo - (COALESCE(pa.pagos_acreditados, (0)::numeric) + COALESCE(pca.pagos_cargo_totales, (0)::numeric))), (0)::numeric) AS saldo_pendiente
            FROM (((universo_cuentahabientes uc
                LEFT JOIN servicio s ON ((uc.servicio_id = s.id_tipo_servicio)))
                LEFT JOIN pagos_agrupados pa ON (((uc.id_cuentahabiente = pa.cuentahabiente_id) AND (uc.anio = pa.anio))))
                LEFT JOIN pagos_cargos_agrupados pca ON (((uc.id_cuentahabiente = pca.cuentahabiente_id) AND (uc.anio = pca.anio_deuda))))
            ORDER BY uc.numero_contrato, uc.anio;
        """)

        cursor.execute("""
            CREATE OR REPLACE VIEW estado_cuenta AS
            WITH anios_operativos AS (
                SELECT DISTINCT pagos_pago.anio
                FROM pagos_pago
                UNION
                SELECT (EXTRACT(year FROM CURRENT_DATE))::integer AS "extract"
                UNION
                SELECT ((EXTRACT(year FROM cargos_cargo.fecha_cargo) - (1)::numeric))::integer AS int4
                FROM cargos_cargo
                WHERE ((cargos_cargo.tipo_cargo_id = 1) AND (cargos_cargo.fecha_cargo IS NOT NULL))
            ), universo_cuentahabientes AS (
                SELECT c_1.id_cuentahabiente,
                    c_1.servicio_id,
                    a.anio
                FROM (cuentahabiente c_1
                    CROSS JOIN anios_operativos a)
            ), pagos_agrupados AS (
                SELECT p.cuentahabiente_id,
                    p.anio,
                    sum(COALESCE(p.monto_recibido, 0)) AS pagos_totales,
                    sum(((COALESCE(p.monto_recibido, 0))::numeric + COALESCE(d.porcentaje, (0)::numeric))) AS pagos_acreditados
                FROM (pagos_pago p
                    LEFT JOIN descuento_descuento d ON ((p.descuento_id = d.id_descuento)))
                GROUP BY p.cuentahabiente_id, p.anio
            ), pagos_cargos_agrupados AS (
                SELECT c_1.cuentahabiente_id,
                    ((EXTRACT(year FROM c_1.fecha_cargo) - (1)::numeric))::integer AS anio_deuda,
                    sum(COALESCE(pc.monto_recibido, (0)::numeric)) AS pagos_cargo_totales
                FROM (cargos_cargo c_1
                    JOIN pagos_cargos pc ON ((c_1.id_cargo = pc.cargo_id)))
                WHERE (c_1.tipo_cargo_id = 1)
                GROUP BY c_1.cuentahabiente_id, (EXTRACT(year FROM c_1.fecha_cargo))
            ), saldos_calculados AS (
                SELECT uc.id_cuentahabiente,
                    uc.anio,
                    GREATEST((COALESCE(s.costo, (0)::numeric) - (COALESCE(pa.pagos_acreditados, (0)::numeric) + COALESCE(pca.pagos_cargo_totales, (0)::numeric))), (0)::numeric) AS saldo_dinamico
                FROM (((universo_cuentahabientes uc
                    LEFT JOIN servicio s ON ((uc.servicio_id = s.id_tipo_servicio)))
                    LEFT JOIN pagos_agrupados pa ON (((uc.id_cuentahabiente = pa.cuentahabiente_id) AND (uc.anio = pa.anio))))
                    LEFT JOIN pagos_cargos_agrupados pca ON (((uc.id_cuentahabiente = pca.cuentahabiente_id) AND (uc.anio = pca.anio_deuda))))
            ), historial_movimientos AS (
                SELECT pagos_pago.cuentahabiente_id,
                    pagos_pago.fecha_pago,
                    pagos_pago.monto_recibido,
                    pagos_pago.anio,
                    'Pago Normal'::text AS tipo_movimiento
                FROM pagos_pago
                WHERE (pagos_pago.fecha_pago IS NOT NULL)
                UNION ALL
                SELECT c_1.cuentahabiente_id,
                    pc.fecha_pago,
                    pc.monto_recibido,
                    ((EXTRACT(year FROM c_1.fecha_cargo) - (1)::numeric))::integer AS anio,
                    'Pago de Cargo'::text AS tipo_movimiento
                FROM (cargos_cargo c_1
                    JOIN pagos_cargos pc ON ((c_1.id_cargo = pc.cargo_id)))
                WHERE ((c_1.tipo_cargo_id = 1) AND (pc.fecha_pago IS NOT NULL))
            )
            SELECT c.id_cuentahabiente,
                c.numero_contrato,
                concat(c.nombres, ' ', c.ap, ' ', c.am) AS nombre,
                concat(c.calle, ' ', c.numero) AS direccion,
                c.telefono,
                sc.saldo_dinamico AS saldo_pendiente,
                hm.fecha_pago,
                hm.monto_recibido,
                sc.anio,
                hm.tipo_movimiento
            FROM ((saldos_calculados sc
                JOIN cuentahabiente c ON ((c.id_cuentahabiente = sc.id_cuentahabiente)))
                LEFT JOIN historial_movimientos hm ON (((hm.cuentahabiente_id = sc.id_cuentahabiente) AND (hm.anio = sc.anio))))
            ORDER BY c.numero_contrato, sc.anio, hm.fecha_pago;
        """)

        cursor.execute("""
            CREATE OR REPLACE VIEW vista_cargos AS
            SELECT c.id_cargo AS id_vista,
                c.id_cargo,
                c.cuentahabiente_id,
                tc.nombre AS tipo_cargo_nombre,
                c.fecha_cargo AS cargo_fecha,
                (EXTRACT(year FROM c.fecha_cargo))::integer AS anio_cargo,
                c.saldo_restante_cargo,
                c.activo AS cargo_activo,
                COALESCE(json_agg(json_build_object('monto', p.monto_recibido, 'fecha', p.fecha_pago)
                    ORDER BY p.fecha_pago) FILTER (WHERE (p.monto_recibido IS NOT NULL)), '[]'::json) AS desglose_pagos
            FROM ((cargos_cargo c
                LEFT JOIN cargos_tipocargo tc ON ((c.tipo_cargo_id = tc.id)))
                LEFT JOIN pagos_cargos p ON ((c.id_cargo = p.cargo_id)))
            GROUP BY c.id_cargo, c.cuentahabiente_id, tc.nombre, c.fecha_cargo, c.saldo_restante_cargo, c.activo;
        """)

        cursor.execute("""
            CREATE OR REPLACE VIEW estado_cuenta_new AS
            WITH anios_operativos AS (
                SELECT DISTINCT pagos_pago.anio
                FROM pagos_pago
                UNION
                SELECT (EXTRACT(year FROM CURRENT_DATE))::integer AS "extract"
                UNION
                SELECT ((EXTRACT(year FROM cargos_cargo.fecha_cargo) - (1)::numeric))::integer AS int4
                FROM cargos_cargo
                WHERE ((cargos_cargo.tipo_cargo_id = 1) AND (cargos_cargo.fecha_cargo IS NOT NULL))
            ), universo_cuentahabientes AS (
                SELECT c_1.id_cuentahabiente,
                    c_1.servicio_id,
                    a.anio
                FROM (cuentahabiente c_1
                    CROSS JOIN anios_operativos a)
            ), pagos_agrupados AS (
                SELECT p.cuentahabiente_id,
                    p.anio,
                    sum(COALESCE(p.monto_recibido, 0)) AS pagos_totales,
                    sum((COALESCE((p.monto_recibido)::numeric, (0)::numeric) + COALESCE(d.porcentaje, (0)::numeric))) AS pagos_acreditados
                FROM (pagos_pago p
                    LEFT JOIN descuento_descuento d ON ((p.descuento_id = d.id_descuento)))
                GROUP BY p.cuentahabiente_id, p.anio
            ), pagos_cargos_agrupados AS (
                SELECT c_1.cuentahabiente_id,
                    ((EXTRACT(year FROM c_1.fecha_cargo) - (1)::numeric))::integer AS anio_deuda,
                    sum(COALESCE(pc.monto_recibido, (0)::numeric)) AS pagos_cargo_totales
                FROM (cargos_cargo c_1
                    JOIN pagos_cargos pc ON ((c_1.id_cargo = pc.cargo_id)))
                WHERE (c_1.tipo_cargo_id = 1)
                GROUP BY c_1.cuentahabiente_id, (EXTRACT(year FROM c_1.fecha_cargo))
            ), saldos_calculados AS (
                SELECT uc.id_cuentahabiente,
                    uc.anio,
                    GREATEST((COALESCE(s_1.costo, (0)::numeric) - (COALESCE(pa.pagos_acreditados, (0)::numeric) + COALESCE(pca.pagos_cargo_totales, (0)::numeric))), (0)::numeric) AS saldo_dinamico
                FROM (((universo_cuentahabientes uc
                    LEFT JOIN servicio s_1 ON ((uc.servicio_id = s_1.id_tipo_servicio)))
                    LEFT JOIN pagos_agrupados pa ON (((uc.id_cuentahabiente = pa.cuentahabiente_id) AND (uc.anio = pa.anio))))
                    LEFT JOIN pagos_cargos_agrupados pca ON (((uc.id_cuentahabiente = pca.cuentahabiente_id) AND (uc.anio = pca.anio_deuda))))
            ), movimientos AS (
                SELECT p.cuentahabiente_id,
                    p.cobrador_id,
                    p.anio,
                    'Pago Normal'::text AS tipo_movimiento,
                    p.fecha_pago,
                    (p.monto_recibido)::numeric AS monto_recibido,
                    COALESCE((d.porcentaje)::numeric, (0)::numeric) AS monto_descuento,
                    d.nombre_descuento AS detalle
                FROM (pagos_pago p
                    LEFT JOIN descuento_descuento d ON ((p.descuento_id = d.id_descuento)))
                UNION ALL
                SELECT pc.cuentahabiente_id,
                    pc.cobrador_id,
                    ((EXTRACT(year FROM c_1.fecha_cargo) - (1)::numeric))::integer AS anio,
                    'Pago Cargo'::text AS tipo_movimiento,
                    pc.fecha_pago,
                    (pc.monto_recibido)::numeric AS monto_recibido,
                    0 AS monto_descuento,
                    tc.nombre AS detalle
                FROM ((cargos_cargo c_1
                    JOIN pagos_cargos pc ON ((c_1.id_cargo = pc.cargo_id)))
                    JOIN cargos_tipocargo tc ON ((c_1.tipo_cargo_id = tc.id)))
                WHERE (c_1.tipo_cargo_id = 1)
            ), agrupacionjson AS (
                SELECT movimientos.cuentahabiente_id,
                    movimientos.cobrador_id,
                    movimientos.anio,
                    movimientos.tipo_movimiento,
                    json_agg(json_build_object(
                        'fecha_pago', movimientos.fecha_pago,
                        'monto_recibido', movimientos.monto_recibido,
                        'monto_descuento', movimientos.monto_descuento,
                        'detalle_movimiento', movimientos.detalle)) AS json_pagos
                FROM movimientos
                GROUP BY movimientos.cuentahabiente_id, movimientos.cobrador_id,
                    movimientos.anio, movimientos.tipo_movimiento
            )
            SELECT row_number() OVER (ORDER BY c.numero_contrato, aj.anio) AS id,
                aj.cobrador_id AS id_cobrador,
                concat_ws(' '::text, cb.nombre, cb.apellidos) AS nombre_cobrador,
                c.id_cuentahabiente,
                c.numero_contrato,
                concat_ws(' '::text, c.nombres, c.ap, c.am) AS nombre_cuentahabiente,
                cl.nombre_calle AS calle,
                s.nombre AS servicio,
                sc.saldo_dinamico AS saldo_pendiente_actualizado,
                CASE
                    WHEN (sc.saldo_dinamico > (0)::numeric) THEN 'Adeudo'::text
                    WHEN ((sc.anio)::numeric = EXTRACT(year FROM CURRENT_DATE)) THEN 'Corriente'::text
                    ELSE 'Pagado'::text
                END AS deuda_actualizada,
                aj.anio,
                aj.tipo_movimiento,
                aj.json_pagos
            FROM (((((agrupacionjson aj
                JOIN cuentahabiente c ON ((aj.cuentahabiente_id = c.id_cuentahabiente)))
                JOIN saldos_calculados sc ON (((sc.id_cuentahabiente = aj.cuentahabiente_id) AND (sc.anio = aj.anio))))
                LEFT JOIN calles_calle cl ON ((c.calle_fk_id = cl.id_calle)))
                LEFT JOIN servicio s ON ((c.servicio_id = s.id_tipo_servicio)))
                LEFT JOIN cobrador_cobrador cb ON ((aj.cobrador_id = cb.id_cobrador)));
        """)

        cursor.execute("""
            CREATE OR REPLACE VIEW reporte_cargos AS
            SELECT row_number() OVER () AS id,
                c.id_cobrador,
                c.nombre AS nombre_cobrador,
                ch.id_cuentahabiente,
                ch.numero_contrato,
                concat(ch.nombres, ' ', ch.ap, ' ', ch.am) AS nombre_cuentahabiente,
                concat(cal.nombre_calle, ' #', ch.numero) AS calle,
                tc.nombre AS tipo_cargo,
                cc.fecha_cargo,
                cc.saldo_restante_cargo,
                CASE
                    WHEN (cc.activo = false) THEN 'Pagado'::text
                    WHEN (cc.saldo_restante_cargo <= (0)::numeric) THEN 'Pagado'::text
                    ELSE 'Pendiente'::text
                END AS estatus_cargo,
                pc.fecha_pago,
                COALESCE(pc.monto_recibido, (0)::numeric) AS monto_recibido
            FROM (((((cargos_cargo cc
                JOIN cuentahabiente ch ON ((cc.cuentahabiente_id = ch.id_cuentahabiente)))
                JOIN calles_calle cal ON ((ch.calle_fk_id = cal.id_calle)))
                JOIN cargos_tipocargo tc ON ((cc.tipo_cargo_id = tc.id)))
                LEFT JOIN pagos_cargos pc ON ((cc.id_cargo = pc.cargo_id)))
                LEFT JOIN cobrador_cobrador c ON ((pc.cobrador_id = c.id_cobrador)));
        """)

        cursor.execute("""
            CREATE OR REPLACE VIEW reporte_padron_general AS
            WITH totales_globales AS (
                SELECT anio_tabla.anio,
                    COALESCE(( SELECT sum((NULLIF(regexp_replace((pp.monto_recibido)::text, '[^0-9.]'::text, ''::text, 'g'::text), ''::text))::numeric) AS sum
                        FROM pagos_pago pp
                        WHERE (EXTRACT(year FROM pp.fecha_pago) = (anio_tabla.anio)::numeric)), (0)::numeric) AS total_pagos_cobrados,
                    COALESCE(( SELECT sum((NULLIF(regexp_replace((pc.monto_recibido)::text, '[^0-9.]'::text, ''::text, 'g'::text), ''::text))::numeric) AS sum
                        FROM pagos_cargos pc
                        WHERE (EXTRACT(year FROM pc.fecha_pago) = (anio_tabla.anio)::numeric)), (0)::numeric) AS total_cobros_cargos,
                    CASE
                        WHEN ((anio_tabla.anio)::numeric = EXTRACT(year FROM CURRENT_DATE)) THEN
                            COALESCE(( SELECT sum((NULLIF(regexp_replace((ch_d.saldo_pendiente)::text, '[^0-9.]'::text, ''::text, 'g'::text), ''::text))::numeric) AS sum
                                FROM cuentahabiente ch_d), (0)::numeric)
                        ELSE
                            COALESCE(( SELECT sum((NULLIF(regexp_replace((cc_1.saldo_restante_cargo)::text, '[^0-9.]'::text, ''::text, 'g'::text), ''::text))::numeric) AS sum
                                FROM cargos_cargo cc_1
                                WHERE ((cc_1.tipo_cargo_id = 1) AND (cc_1.activo = true) AND (EXTRACT(year FROM cc_1.fecha_cargo) = ((anio_tabla.anio)::numeric + (1)::numeric)))), (0)::numeric)
                    END AS total_pagos_pendientes_global,
                    COALESCE(( SELECT sum((NULLIF(regexp_replace((cc.saldo_restante_cargo)::text, '[^0-9.]'::text, ''::text, 'g'::text), ''::text))::numeric) AS sum
                        FROM cargos_cargo cc
                        WHERE ((cc.tipo_cargo_id <> 1) AND (cc.activo = true) AND (EXTRACT(year FROM cc.fecha_cargo) = (anio_tabla.anio)::numeric))), (0)::numeric) AS total_cargos_pendientes_global,
                    ( SELECT count(*) AS count
                        FROM cuentahabiente) AS total_usuarios_global
                FROM ( SELECT DISTINCT (EXTRACT(year FROM pagos_pago.fecha_pago))::integer AS anio
                        FROM pagos_pago
                        WHERE (pagos_pago.fecha_pago IS NOT NULL)
                    UNION
                    SELECT DISTINCT (EXTRACT(year FROM pagos_cargos.fecha_pago))::integer AS "extract"
                        FROM pagos_cargos
                        WHERE (pagos_cargos.fecha_pago IS NOT NULL)
                    UNION
                    SELECT DISTINCT (EXTRACT(year FROM cargos_cargo.fecha_cargo))::integer AS "extract"
                        FROM cargos_cargo
                        WHERE (cargos_cargo.fecha_cargo IS NOT NULL)) anio_tabla
            )
            SELECT row_number() OVER () AS id,
                ch.id_cuentahabiente,
                ch.numero_contrato,
                concat(ch.nombres, ' ', ch.ap, ' ', ch.am) AS nombre_usuario,
                s.nombre AS tipo_servicio,
                s.costo AS costo_servicio_anual,
                ( SELECT count(*) AS count
                    FROM pagos_pago pp_cnt
                    WHERE ((pp_cnt.cuentahabiente_id = ch.id_cuentahabiente) AND (EXTRACT(year FROM pp_cnt.fecha_pago) = (tg.anio)::numeric))) AS cantidad_abonos_servicio,
                COALESCE(( SELECT sum((NULLIF(regexp_replace((pp_u.monto_recibido)::text, '[^0-9.]'::text, ''::text, 'g'::text), ''::text))::numeric) AS sum
                    FROM pagos_pago pp_u
                    WHERE ((pp_u.cuentahabiente_id = ch.id_cuentahabiente) AND (EXTRACT(year FROM pp_u.fecha_pago) = (tg.anio)::numeric))), (0)::numeric) AS total_pagado_servicio,
                ( SELECT jsonb_agg(jsonb_build_object('nombre_cargo', tc.nombre)) AS jsonb_agg
                    FROM (cargos_cargo cc_j
                        LEFT JOIN cargos_tipocargo tc ON ((cc_j.tipo_cargo_id = tc.id)))
                    WHERE ((cc_j.cuentahabiente_id = ch.id_cuentahabiente) AND (cc_j.tipo_cargo_id <> 1) AND (cc_j.activo = true) AND (EXTRACT(year FROM cc_j.fecha_cargo) = (tg.anio)::numeric))) AS detalle_cargos_activos_json,
                ( SELECT jsonb_agg(jsonb_build_object('monto_abonado', pc_j.monto_recibido, 'cargo_afectado', tc_p.nombre)) AS jsonb_agg
                    FROM ((pagos_cargos pc_j
                        LEFT JOIN cargos_cargo cc_p ON ((pc_j.cargo_id = cc_p.id_cargo)))
                        LEFT JOIN cargos_tipocargo tc_p ON ((cc_p.tipo_cargo_id = tc_p.id)))
                    WHERE ((pc_j.cuentahabiente_id = ch.id_cuentahabiente) AND (EXTRACT(year FROM pc_j.fecha_pago) = (tg.anio)::numeric))) AS detalle_abonos_cargos_json,
                ( SELECT count(*) AS count
                    FROM pagos_cargos pc_cnt
                    WHERE ((pc_cnt.cuentahabiente_id = ch.id_cuentahabiente) AND (EXTRACT(year FROM pc_cnt.fecha_pago) = (tg.anio)::numeric))) AS cantidad_pagos_cargos,
                COALESCE(( SELECT sum((NULLIF(regexp_replace((pc_u.monto_recibido)::text, '[^0-9.]'::text, ''::text, 'g'::text), ''::text))::numeric) AS sum
                    FROM pagos_cargos pc_u
                    WHERE ((pc_u.cuentahabiente_id = ch.id_cuentahabiente) AND (EXTRACT(year FROM pc_u.fecha_pago) = (tg.anio)::numeric))), (0)::numeric) AS total_pagado_cargos,
                (COALESCE(( SELECT sum((NULLIF(regexp_replace((pp_tot.monto_recibido)::text, '[^0-9.]'::text, ''::text, 'g'::text), ''::text))::numeric) AS sum
                    FROM pagos_pago pp_tot
                    WHERE ((pp_tot.cuentahabiente_id = ch.id_cuentahabiente) AND (EXTRACT(year FROM pp_tot.fecha_pago) = (tg.anio)::numeric))), (0)::numeric) +
                COALESCE(( SELECT sum((NULLIF(regexp_replace((pc_tot.monto_recibido)::text, '[^0-9.]'::text, ''::text, 'g'::text), ''::text))::numeric) AS sum
                    FROM pagos_cargos pc_tot
                    WHERE ((pc_tot.cuentahabiente_id = ch.id_cuentahabiente) AND (EXTRACT(year FROM pc_tot.fecha_pago) = (tg.anio)::numeric))), (0)::numeric)) AS total_pagado_general,
                tg.anio AS anio_reporte,
                tg.total_pagos_cobrados,
                tg.total_cobros_cargos,
                tg.total_pagos_pendientes_global AS total_pagos_pendientes,
                tg.total_cargos_pendientes_global AS total_cargos_pendientes,
                (tg.total_pagos_cobrados + tg.total_cobros_cargos) AS total_recaudado_global,
                tg.total_usuarios_global AS total_usuarios
            FROM ((cuentahabiente ch
                CROSS JOIN totales_globales tg)
                LEFT JOIN servicio s ON ((ch.servicio_id = s.id_tipo_servicio)));
        """)

class Migration(migrations.Migration):

    dependencies = [
        ('cuentahabientes', '0016_merge_20260402_0002'),
    ]

    operations = [

        # ── PASO 1: borrar vistas antes de alterar la columna ─────────
        migrations.RunPython(
            drop_views,
            reverse_code=migrations.RunPython.noop,
        ),

        # ── PASO 2: alterar saldo_pendiente INTEGER → DECIMAL ─────────
        migrations.AlterField(
            model_name='cuentahabiente',
            name='saldo_pendiente',
            field=models.DecimalField(
                decimal_places=2,
                default=0,
                max_digits=10,
            ),
        ),

        # ── PASO 3: campos nuevos ─────────────────────────────────────
        migrations.AddField(
            model_name='cuentahabiente',
            name='numero_interior',
            field=models.CharField(blank=True, max_length=10, null=True),
        ),
        migrations.AddField(
            model_name='cuentahabiente',
            name='tipo_cuenta',
            field=models.CharField(
                choices=[('permanente', 'Permanente'), ('parcial', 'Parcial')],
                default='permanente',
                max_length=20,
            ),
        ),
        migrations.AddField(
            model_name='cuentahabiente',
            name='fecha_registro',
            field=models.DateField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='cuentahabiente',
            name='fecha_activacion',
            field=models.DateField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='cuentahabiente',
            name='fecha_desactivacion',
            field=models.DateField(blank=True, null=True),
        ),
        migrations.AlterModelTable(
            name='cuentahabiente',
            table='cuentahabiente',
        ),

        # ── PASO 4: modelos de vistas (managed=False) ─────────────────
        migrations.CreateModel(
            name='EstadoCuentaNew',
            fields=[
                ('id', models.BigIntegerField(primary_key=True, serialize=False)),
                ('id_cobrador', models.IntegerField(null=True)),
                ('nombre_cobrador', models.CharField(max_length=255, null=True)),
                ('id_cuentahabiente', models.IntegerField()),
                ('numero_contrato', models.CharField(max_length=100)),
                ('nombre_cuentahabiente', models.CharField(max_length=255, null=True)),
                ('calle', models.CharField(max_length=255, null=True)),
                ('servicio', models.CharField(max_length=255, null=True)),
                ('saldo_pendiente_actualizado', models.DecimalField(decimal_places=2, max_digits=12, null=True)),
                ('deuda_actualizada', models.CharField(max_length=20, null=True)),
                ('anio', models.IntegerField()),
                ('tipo_movimiento', models.CharField(max_length=50)),
                ('json_pagos', cuentahabientes.models_views.PreParsedJSONField()),
            ],
            options={
                'db_table': 'estado_cuenta_new',
                'ordering': ['numero_contrato', 'anio'],
                'managed': False,
            },
        ),
        migrations.CreateModel(
            name='ReporteCargos',
            fields=[
                ('id', models.BigIntegerField(primary_key=True, serialize=False)),
                ('id_cobrador', models.IntegerField(null=True)),
                ('nombre_cobrador', models.CharField(max_length=255, null=True)),
                ('id_cuentahabiente', models.IntegerField()),
                ('numero_contrato', models.CharField(max_length=100)),
                ('nombre_cuentahabiente', models.CharField(max_length=255, null=True)),
                ('calle', models.CharField(max_length=255, null=True)),
                ('tipo_cargo', models.CharField(max_length=255)),
                ('fecha_cargo', models.DateField(null=True)),
                ('saldo_restante_cargo', models.DecimalField(decimal_places=2, max_digits=12, null=True)),
                ('estatus_cargo', models.CharField(max_length=20)),
                ('fecha_pago', models.DateField(null=True)),
                ('monto_recibido', models.DecimalField(decimal_places=2, max_digits=12)),
            ],
            options={
                'db_table': 'reporte_cargos',
                'ordering': ['numero_contrato', 'fecha_cargo'],
                'managed': False,
            },
        ),
        migrations.CreateModel(
            name='ReportePadronGeneral',
            fields=[
                ('id', models.BigIntegerField(primary_key=True, serialize=False)),
                ('id_cuentahabiente', models.IntegerField()),
                ('numero_contrato', models.CharField(max_length=100)),
                ('nombre_usuario', models.CharField(max_length=255, null=True)),
                ('tipo_servicio', models.CharField(max_length=255, null=True)),
                ('costo_servicio_anual', models.DecimalField(decimal_places=2, max_digits=14, null=True)),
                ('cantidad_abonos_servicio', models.BigIntegerField(null=True)),
                ('total_pagado_servicio', models.DecimalField(decimal_places=2, max_digits=14, null=True)),
                ('detalle_cargos_activos_json', cuentahabientes.models_views.PreParsedJSONField(null=True)),
                ('detalle_abonos_cargos_json', cuentahabientes.models_views.PreParsedJSONField(null=True)),
                ('cantidad_pagos_cargos', models.BigIntegerField(null=True)),
                ('total_pagado_cargos', models.DecimalField(decimal_places=2, max_digits=14, null=True)),
                ('total_pagado_general', models.DecimalField(decimal_places=2, max_digits=14, null=True)),
                ('anio_reporte', models.IntegerField()),
                ('total_pagos_cobrados', models.DecimalField(decimal_places=2, max_digits=14, null=True)),
                ('total_cobros_cargos', models.DecimalField(decimal_places=2, max_digits=14, null=True)),
                ('total_pagos_pendientes', models.DecimalField(decimal_places=2, max_digits=14, null=True)),
                ('total_cargos_pendientes', models.DecimalField(decimal_places=2, max_digits=14, null=True)),
                ('total_recaudado_global', models.DecimalField(decimal_places=2, max_digits=14, null=True)),
                ('total_usuarios', models.BigIntegerField(null=True)),
            ],
            options={
                'db_table': 'reporte_padron_general',
                'ordering': ['numero_contrato', 'anio_reporte'],
                'managed': False,
            },
        ),
        migrations.CreateModel(
            name='VistaCargos',
            fields=[
                ('id_vista', models.IntegerField(primary_key=True, serialize=False)),
                ('id_cargo', models.IntegerField()),
                ('cuentahabiente_id', models.IntegerField()),
                ('tipo_cargo_nombre', models.CharField(max_length=255)),
                ('cargo_fecha', models.DateField()),
                ('anio_cargo', models.IntegerField()),
                ('saldo_restante_cargo', models.DecimalField(decimal_places=2, max_digits=12)),
                ('cargo_activo', models.BooleanField()),
                ('desglose_pagos', cuentahabientes.models_views.PreParsedJSONField()),
            ],
            options={
                'db_table': 'vista_cargos',
                'ordering': ['-cargo_fecha'],
                'managed': False,
            },
        ),

        # ── PASO 5: recrear las vistas con el nuevo tipo de columna ───
        migrations.RunPython(
            recreate_views,
            reverse_code=migrations.RunPython.noop,
        ),
    ]