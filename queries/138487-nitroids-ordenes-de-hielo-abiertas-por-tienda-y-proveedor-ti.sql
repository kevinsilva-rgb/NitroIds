-- Ordenes de hielo abiertas por tienda y proveedor para el boton "Ordenes de Hielo" de NitroIds.
-- Definiciones de Kevin (2026-09-28):
--   * Solo ordenes del proveedor Turbo TIENDAS CHEDRAUI.
--   * Abierta = SENT / AT_STORE (PARTIAL_DELIVERY no cuenta), con hielo pendiente de recibir.
--   * "Proveedor" que elige la tienda = marca del producto: Hielo Club (EAN 7501124500023) o
--     Hielo Fiesta (EAN 7501012700009) o Iglu (EAN 7501103700000). Otras marcas no entran.
-- Filas con po_id NULL = catalogo de tiendas (con ordenes de hielo de TIENDAS CHEDRAUI en los ultimos 90 dias), para el dropdown.
SELECT
  W.name AS tienda,
  CASE TRIM(LEADING '0' FROM CAST(P.ean AS CHAR)) WHEN '7501124500023' THEN 'Hielo Club' WHEN '7501012700009' THEN 'Hielo Fiesta' ELSE 'Iglu' END AS proveedor,
  A.id AS po_id,
  A.ingress_order_external_id AS external_id,
  C.status_name AS estado,
  DATE_FORMAT(CONVERT_TZ(A.created_at, '+00:00', '-06:00'), '%Y-%m-%d %H:%i') AS fecha_creacion_mx,
  GROUP_CONCAT(DISTINCT P.name SEPARATOR ' | ') AS productos_hielo,
  SUM(B.quantity) AS cantidad_solicitada,
  SUM(B.received) AS cantidad_recibida
FROM purchase_order A
JOIN purchase_order_detail B ON A.id = B.purchase_order_id
JOIN purchase_order_status C ON C.id = A.status_id
LEFT JOIN `turbo-sync`.warehouse W ON W.id = A.warehouse_id
LEFT JOIN `turbo-sync`.supplier S ON S.id = A.supplier_id
LEFT JOIN `turbo-sync`.product P ON P.id = B.product_id
WHERE C.status_name IN ('SENT', 'AT_STORE')
  AND S.business_name = 'TIENDAS CHEDRAUI'
  AND TRIM(LEADING '0' FROM CAST(P.ean AS CHAR)) IN ('7501124500023', '7501012700009', '7501103700000')
  AND W.name NOT LIKE '%INACTIVE%'
GROUP BY 1, 2, 3, 4, 5, 6
HAVING SUM(B.quantity) > SUM(B.received)

UNION ALL

SELECT DISTINCT W.name, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL
FROM purchase_order A
JOIN purchase_order_detail B ON A.id = B.purchase_order_id
LEFT JOIN `turbo-sync`.warehouse W ON W.id = A.warehouse_id
LEFT JOIN `turbo-sync`.supplier S ON S.id = A.supplier_id
LEFT JOIN `turbo-sync`.product P ON P.id = B.product_id
WHERE A.created_at >= DATE_SUB(NOW(), INTERVAL 90 DAY)
  AND S.business_name = 'TIENDAS CHEDRAUI'
  AND TRIM(LEADING '0' FROM CAST(P.ean AS CHAR)) IN ('7501124500023', '7501012700009', '7501103700000')
  AND W.name NOT LIKE '%INACTIVE%'
