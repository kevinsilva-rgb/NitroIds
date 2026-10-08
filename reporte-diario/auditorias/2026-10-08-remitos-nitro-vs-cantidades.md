# Auditoría: fotos del remito en Nitro vs. cantidades recibidas · hielo 07/10 y 08/10/2026

Pedido de Kevin (2026-10-08): revisar todas las fotos de remito de Nitro de órdenes de hielo de ayer y hoy y ver si
coinciden con lo recibido en Nitro. 26 recepciones (19 del 07/10, 7 del 08/10 hasta ~14:15). Fuente: PDF de Nitro
(`reception_order_execution_document.url`) vs. `reception_order_execution_product.quantity`. Revisión visual de cada PDF.

## Resumen
| Resultado | Órdenes |
|---|---|
| ✅ Coincide con documento del proveedor/Chedraui | 14 |
| ✅ Coincide, pero solo con anotación de la tienda sobre la OC (sin nota del proveedor) | 2 (Jardines de la Patria 328742, SOLARES 328744) |
| ❌ **No coincide** | 1 (Picacho 326591) |
| ⚠️ Documento dudoso (de otra orden / foto vieja) | 2 (PRADOS COAPA 328083, Agrícola 314240) |
| ⚠️ Sin evidencia de cantidad: la foto es solo la OC/pedido | 7 (Lindavista 325011, Estadio Jalisco 328783, El Rosario 328900 Stark, Zedec 328556, TOREO 327390, Campestre 327334, El Rosario 329026 Tun Ha) |

## Hallazgos principales
1. **Picacho 326591 (Hielo Club, OC 4502056879): Nitro 100, documento 40.** La foto es la OC **4502056843** (otra
   orden de Picacho, PO 326574, que sigue `SENT` con 0 recibido) con "Recibí 40 bolsas de hielo – Rafael García" y sello
   "20 OCT 2026" (fecha futura). La otra recepción de Picacho del 07/10 (PO 328080) sí trae nota Hielo Club B 14194 por
   40 y Nitro 40. Posible sobre-registro de **60 bolsas** en 326591 y foto de la OC equivocada.
2. **PRADOS COAPA 328083 (OC 4502070874): Nitro 60 = nota 60, pero la nota es vieja.** Nota Hielo Club B 13302 del
   **12-SEP-26**, sello del 12-sep, que cita la OC **4502031342** (PO 324290, cerrada `CLOSED_ZERO_DELIVERY` sin recibir).
   No hay remito del 07/10.
3. **Agrícola 314240 (OC 4501933504): Nitro 30 = ticket 30, pero es foto de una pantalla** (se ve el dock de macOS) de
   un ticket con sello "Day Store 22 JUL". OC antigua cerrada el 08/10: recepción atrasada con imagen vieja.
4. **7 recepciones sin prueba de cantidad**: la foto es la orden de compra de Rappi o el pedido de Chedraui, sin nota del
   proveedor ni cantidad recibida (en Campestre y El Rosario Tun Ha Nitro registró exactamente lo pedido).
5. Detalle menor: PRADOS COAPA 326594 coincide (60) pero la fecha del sello se lee "02" o "07 OCT" y el sello es
   "Baja SLE", no Day Store.

## Detalle por orden
| PO | Tienda | Proveedor | Documento en la foto | Doc. dice | Nitro | Veredicto |
|---|---|---|---|---|---|---|
| 326414 | Las Aguilas | Chedraui | Nota Hielo Club A 13746 + entrada Chedraui 5117256997 | 65 | 65 | ✅ |
| 325011 | Lindavista | Chedraui | Solo pedido Chedraui 7038615013 (208) | — | 80 | ⚠️ solo OC |
| 328743 | Paseo del Sol | Apodaca | OC + nota KLYR/Aguafría 17961 | 60 | 60 | ✅ |
| 328742 | Jardines de la Patria | Apodaca | OC con "100" a mano, sello Day Store | 100 | 100 | ✅ (sin nota proveedor) |
| 328744 | SOLARES | Apodaca | OC con "Dejo 50" | 50 | 50 | ✅ (sin nota proveedor) |
| 327357 | ATIZAPAN | Chedraui | Entrada Chedraui 5117267798 | 40 | 40 | ✅ |
| 327335 | Toriello Guerra | Chedraui | Nota Hielo Club B 14193 | 84 | 84 | ✅ |
| 326402 | Granjas | Chedraui | Nota de entrega Chedraui (pedido 7038697781) | 50 | 50 | ✅ |
| 328783 | Estadio Jalisco | Apodaca | Solo OC (35) con sello Recibido | — | 35 | ⚠️ solo OC |
| 328072 | Huicholes | Hielo Club | Nota Hielo Club A 14077 | 120 | 120 | ✅ |
| 328901 | San Ramon | Stark | OC + nota Stark 22936 D ($2,362.50 = 135 × 17.50) | 135 | 135 | ✅ |
| 328900 | El Rosario | Stark | Solo OC (75), sin sello ni firma | — | 75 | ⚠️ solo OC |
| 327363 | Portales Norte | Chedraui | Ticket Hielo Club R16-51165 | 80 | 80 | ✅ |
| 326594 | PRADOS COAPA | Hielo Club | Nota Hielo Club B 1408? + OC | 60 | 60 | ✅ (fecha de sello dudosa) |
| 328083 | PRADOS COAPA | Hielo Club | Nota B 13302 del 12-sep de otra OC + pantalla OC | 60 | 60 | ⚠️ doc. de otra orden |
| 326591 | Picacho | Hielo Club | OC **4502056843** (otra orden) "Recibí 40" | 40 | 100 | ❌ +60 |
| 328080 | Picacho | Hielo Club | Nota Hielo Club B 14194 | 40 | 40 | ✅ |
| 328556 | Zedec | Chedraui | Solo pedido Chedraui (100) | — | 70 | ⚠️ solo OC |
| 327390 | TOREO | Chedraui | Pedido Chedraui (130) con sello de recibo 07/10 | — | 59 | ⚠️ solo OC |
| 327334 | Campestre | Chedraui | Solo pedido Chedraui (130) | — | 130 | ⚠️ solo OC |
| 329026 | El Rosario | Tun Ha | Solo OC Rappi (100) | — | 100 | ⚠️ solo OC |
| 328577 | Constituyentes | Chedraui | Nota Premium Ice 32155 QRO, sello Darks Constituyentes | 50 | 50 | ✅ |
| 314240 | Agrícola | Hielo Club | Foto de pantalla de ticket con sello 22-JUL | 30 | 30 | ⚠️ foto vieja |
| 328070 | Frida | Hielo Club | Nota Hielo Club B 14460 | 100 | 100 | ✅ |
| 328076 | Viaducto | Hielo Club | Ticket Hielo Club R5-36385 | 90 | 90 | ✅ |
| 328088 | Gustavo Baz | Hielo Club | Ticket Hielo Club R101-1089 (foto cortada) | 50 | 50 | ✅ |

Nota: el "PO: 45xxxx" impreso arriba de cada PDF es el `reception_order_id` de Nitro, no el PO de compra.
