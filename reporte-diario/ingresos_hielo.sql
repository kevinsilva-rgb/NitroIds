-- Ordenes de hielo con INGRESO en Nitro en un dia (hora CDMX), para el reporte diario de ingresos sin foto.
-- Ingreso = recepcion (turbo_reception_order_ms.reception_order) terminada ese dia (ended_at) en estado
-- DELIVERED o PARTIAL_DELIVERED, con mas de 0 unidades de hielo recibidas. No cuenta
-- PO_EXPIRED_WITH_PARTIAL_DELIVERY: es un cierre automatico por vencimiento, su ended_at no es el ingreso.
-- Hielo = producto con "hielo" en el nombre, sin paletas. Fuera "FABIANA prueba" y tiendas INACTIVE.
-- Todos los proveedores (TIENDAS CHEDRAUI y directos). {fecha} = 'YYYY-MM-DD'.
SELECT
  A.id AS po_id,
  COALESCE(NULLIF(A.ingress_order_external_id, ''), NULLIF(A.sap_id, '')) AS external_id,
  W.name AS tienda,
  S.business_name AS proveedor,
  C.status_name AS estado_po,
  GROUP_CONCAT(DISTINCT St.status_name SEPARATOR ', ') AS estado_recepcion,
  DATE_FORMAT(CONVERT_TZ(MAX(R.ended_at), '+00:00', '-06:00'), '%Y-%m-%d %H:%i') AS ingreso_mx,
  GROUP_CONCAT(DISTINCT P.name SEPARATOR ' | ') AS productos_hielo,
  SUM(RP.received) AS unidades_hielo_recibidas
FROM `turbo_reception_order_ms`.reception_order R
JOIN `turbo_reception_order_ms`.status St ON St.id = R.status_id
JOIN `turbo_reception_order_ms`.reception_order_product RP ON RP.reception_order_id = R.id
JOIN purchase_order A ON A.id = R.purchase_order_id
JOIN purchase_order_status C ON C.id = A.status_id
LEFT JOIN `turbo-sync`.warehouse W ON W.id = A.warehouse_id
LEFT JOIN `turbo-sync`.supplier S ON S.id = A.supplier_id
LEFT JOIN `turbo-sync`.product P ON P.id = RP.product_id
WHERE R.ended_at >= CONVERT_TZ('{fecha} 00:00:00', '-06:00', '+00:00')
  AND R.ended_at < CONVERT_TZ(DATE_ADD('{fecha} 00:00:00', INTERVAL 1 DAY), '-06:00', '+00:00')
  AND St.status_name IN ('DELIVERED', 'PARTIAL_DELIVERED')
  AND LOWER(P.name) LIKE '%hielo%' AND LOWER(P.name) NOT LIKE '%paleta%'
  AND COALESCE(S.business_name, '') <> 'FABIANA prueba'
  AND COALESCE(W.name, '') NOT LIKE '%INACTIVE%'
GROUP BY A.id, external_id, W.name, S.business_name, C.status_name
HAVING SUM(RP.received) > 0
ORDER BY W.name, ingreso_mx
