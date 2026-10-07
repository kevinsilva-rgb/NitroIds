-- Ingresos de hielo en Nitro desde el 29/09/2026 (lanzamiento de la foto del remito en NitroIds), maximo 60 dias, una fila por orden x dia de ingreso (hora CDMX).
-- Misma regla que ingresos_hielo.sql (reporte diario): recepcion terminada en DELIVERED / PARTIAL_DELIVERED con
-- hielo recibido > 0, todos los proveedores, sin paletas, sin "FABIANA prueba" ni tiendas INACTIVE.
-- Guardada en Redash como query (ver README) para el dash de trazabilidad (Control Hielo ?api=trazabilidadFotos).
SELECT
  DATE_FORMAT(CONVERT_TZ(R.ended_at, '+00:00', '-06:00'), '%Y-%m-%d') AS dia,
  A.id AS po_id,
  COALESCE(NULLIF(A.ingress_order_external_id, ''), NULLIF(A.sap_id, '')) AS external_id,
  W.name AS tienda,
  S.business_name AS proveedor,
  DATE_FORMAT(CONVERT_TZ(MAX(R.ended_at), '+00:00', '-06:00'), '%Y-%m-%d %H:%i') AS ingreso_mx,
  GROUP_CONCAT(DISTINCT P.name SEPARATOR ' | ') AS productos_hielo,
  SUM(RP.received) AS unidades_hielo_recibidas
FROM `turbo_reception_order_ms`.reception_order R
JOIN `turbo_reception_order_ms`.status St ON St.id = R.status_id
JOIN `turbo_reception_order_ms`.reception_order_product RP ON RP.reception_order_id = R.id
JOIN purchase_order A ON A.id = R.purchase_order_id
LEFT JOIN `turbo-sync`.warehouse W ON W.id = A.warehouse_id
LEFT JOIN `turbo-sync`.supplier S ON S.id = A.supplier_id
LEFT JOIN `turbo-sync`.product P ON P.id = RP.product_id
WHERE R.ended_at >= GREATEST(DATE_SUB(UTC_TIMESTAMP(), INTERVAL 60 DAY), '2026-09-29 06:00:00')  -- 29/09 00:00 CDMX
  AND St.status_name IN ('DELIVERED', 'PARTIAL_DELIVERED')
  AND LOWER(P.name) LIKE '%hielo%' AND LOWER(P.name) NOT LIKE '%paleta%'
  AND COALESCE(S.business_name, '') <> 'FABIANA prueba'
  AND COALESCE(W.name, '') NOT LIKE '%INACTIVE%'
GROUP BY dia, A.id, external_id, W.name, S.business_name
HAVING SUM(RP.received) > 0
ORDER BY dia, W.name
