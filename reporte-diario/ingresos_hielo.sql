-- Ordenes de hielo con INGRESO en Nitro en un dia (hora CDMX), para el reporte diario (fotos 0/2, 1/2, 2/2).
-- Ingreso = la tienda hizo la recepcion en Nitro (turbo_reception_order_ms.reception_order_execution) con hielo recibido > 0
--   en esa ejecucion (reception_order_execution_product.quantity), recepcion no CANCELED, todos los proveedores.
-- Fecha/hora del ingreso = hora de la foto del remito en Nitro (reception_order_execution_document.reception_invoice, UTC
--   -> CDMX); si no hay documento, la hora de la ejecucion. NO se usa reception_order.ended_at: puede ser dias despues
--   (cierre automatico), p. ej. Sauz 327707: foto 03/10 11:28, ended_at 06/10 00:10. (Cambio pedido por Kevin 2026-10-08.)
-- remito_nitro_url = PDF que arma Nitro al cerrar la recepcion con la foto del remito (S3 turbo-data-adapter-mx).
-- Hielo = producto con "hielo" en el nombre, sin paletas. Fuera "FABIANA prueba" y tiendas INACTIVE.
-- {fecha} = 'YYYY-MM-DD'.
SELECT
  DATE_FORMAT(CONVERT_TZ(COALESCE(D.reception_invoice, E.created_at), '+00:00', '-06:00'), '%Y-%m-%d') AS dia,
  A.id AS po_id,
  COALESCE(NULLIF(A.ingress_order_external_id, ''), NULLIF(A.sap_id, '')) AS external_id,
  W.name AS tienda,
  S.business_name AS proveedor,
  GROUP_CONCAT(DISTINCT St.status_name SEPARATOR ', ') AS estado_recepcion,
  DATE_FORMAT(CONVERT_TZ(MIN(COALESCE(D.reception_invoice, E.created_at)), '+00:00', '-06:00'), '%Y-%m-%d %H:%i') AS ingreso_mx,
  GROUP_CONCAT(DISTINCT P.name SEPARATOR ' | ') AS productos_hielo,
  SUM(EP.quantity) AS unidades_hielo_recibidas,
  MIN(NULLIF(D.url, '')) AS remito_nitro_url
FROM `turbo_reception_order_ms`.reception_order R
JOIN `turbo_reception_order_ms`.status St ON St.id = R.status_id
JOIN `turbo_reception_order_ms`.reception_order_execution E ON E.reception_order_id = R.id
LEFT JOIN `turbo_reception_order_ms`.reception_order_execution_document D ON D.reception_order_execution_id = E.id
JOIN `turbo_reception_order_ms`.reception_order_execution_product EP ON EP.reception_order_execution_id = E.id
JOIN purchase_order A ON A.id = R.purchase_order_id
LEFT JOIN `turbo-sync`.warehouse W ON W.id = A.warehouse_id
LEFT JOIN `turbo-sync`.supplier S ON S.id = A.supplier_id
LEFT JOIN `turbo-sync`.product P ON P.id = EP.product_id
WHERE COALESCE(D.reception_invoice, E.created_at) >= CONVERT_TZ('{fecha} 00:00:00', '-06:00', '+00:00')
  AND COALESCE(D.reception_invoice, E.created_at) < CONVERT_TZ(DATE_ADD('{fecha} 00:00:00', INTERVAL 1 DAY), '-06:00', '+00:00')
  AND St.status_name <> 'CANCELED'
  AND LOWER(P.name) LIKE '%hielo%' AND LOWER(P.name) NOT LIKE '%paleta%'
  AND COALESCE(S.business_name, '') <> 'FABIANA prueba'
  AND COALESCE(W.name, '') NOT LIKE '%INACTIVE%'
GROUP BY dia, A.id, external_id, W.name, S.business_name
HAVING SUM(EP.quantity) > 0
ORDER BY dia, W.name, ingreso_mx
