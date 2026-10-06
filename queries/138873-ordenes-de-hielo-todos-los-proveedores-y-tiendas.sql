-- Todas las ordenes de hielo: todos los proveedores (incluye TIENDAS CHEDRAUI) y todas las tiendas, ultimos 90 dias,
-- mas las que siguen abiertas (SENT / AT_STORE) aunque sean mas viejas (las usa NitroIds para bloquear vencidas).
-- Hielo = producto cuyo nombre contiene "hielo". Una fila por orden x producto de hielo.
-- Excluye el proveedor de prueba "FABIANA prueba".
-- external_id = External ID de la orden; si no tiene (proveedor directo), el SAP ID.
SELECT
  A.id AS po_id,
  COALESCE(NULLIF(A.ingress_order_external_id, ''), NULLIF(A.sap_id, '')) AS external_id,
  W.name AS tienda,
  S.business_name AS proveedor,
  C.status_name AS estado,
  P.ean,
  P.name AS producto,
  B.quantity AS cantidad_solicitada,
  COALESCE(B.received, 0) AS cantidad_recibida,
  B.quantity - COALESCE(B.received, 0) AS pendiente,
  DATE_FORMAT(CONVERT_TZ(A.created_at, '+00:00', '-06:00'), '%Y-%m-%d %H:%i') AS fecha_creacion_mx,
  DATE_FORMAT(CONVERT_TZ(A.delivered_at, '+00:00', '-06:00'), '%Y-%m-%d %H:%i') AS fecha_entrega_mx,
  DATE_FORMAT(CONVERT_TZ(A.close_at, '+00:00', '-06:00'), '%Y-%m-%d %H:%i') AS fecha_cierre_mx
FROM purchase_order A
JOIN purchase_order_detail B ON A.id = B.purchase_order_id
JOIN purchase_order_status C ON C.id = A.status_id
LEFT JOIN `turbo-sync`.warehouse W ON W.id = A.warehouse_id
LEFT JOIN `turbo-sync`.supplier S ON S.id = A.supplier_id
LEFT JOIN `turbo-sync`.product P ON P.id = B.product_id
WHERE (A.created_at >= DATE_SUB(NOW(), INTERVAL 90 DAY) OR C.status_name IN ('SENT', 'AT_STORE'))
  AND LOWER(P.name) LIKE '%hielo%'
  AND COALESCE(S.business_name, '') <> 'FABIANA prueba'
ORDER BY A.created_at DESC, A.id
