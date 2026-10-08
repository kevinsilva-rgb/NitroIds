-- Recepciones de hielo en Nitro de un dia (hora CDMX) con el detalle por producto y el PDF del remito, para la revision
-- diaria de remitos (remitos_del_dia.py). Misma regla de ingreso que ingresos_hielo.sql: ejecucion de recepcion en Nitro con
-- hielo recibido > 0, a la hora de la foto del remito en Nitro, recepcion no CANCELED, todos los proveedores.
-- Una fila por orden x producto de hielo. {fecha} = 'YYYY-MM-DD'.
SELECT
  A.id AS po_id,
  COALESCE(NULLIF(A.ingress_order_external_id, ''), NULLIF(A.sap_id, '')) AS external_id,
  W.name AS tienda,
  S.business_name AS proveedor,
  St.status_name AS estado_recepcion,
  DATE_FORMAT(CONVERT_TZ(COALESCE(D.reception_invoice, E.created_at), '+00:00', '-06:00'), '%Y-%m-%d %H:%i') AS ingreso_mx,
  P.name AS producto,
  RP.quantity AS solicitado,
  EP.quantity AS recibido,
  EP.missing AS faltante,
  EP.damaged AS averiado,
  EP.additional AS sobrante,
  NULLIF(D.url, '') AS remito_nitro_url
FROM `turbo_reception_order_ms`.reception_order R
JOIN `turbo_reception_order_ms`.status St ON St.id = R.status_id
JOIN `turbo_reception_order_ms`.reception_order_execution E ON E.reception_order_id = R.id
LEFT JOIN `turbo_reception_order_ms`.reception_order_execution_document D ON D.reception_order_execution_id = E.id
JOIN `turbo_reception_order_ms`.reception_order_execution_product EP ON EP.reception_order_execution_id = E.id
LEFT JOIN `turbo_reception_order_ms`.reception_order_product RP ON RP.reception_order_id = R.id AND RP.product_id = EP.product_id
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
  AND EP.quantity > 0
ORDER BY ingreso_mx, A.id
