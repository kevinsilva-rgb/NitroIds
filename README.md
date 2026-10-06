# NitroIds — Buscador de Órdenes Nitro

Página estática (un solo `index.html`) que usan tiendas y Torre de Control para:

1. **Buscar una orden de compra o albarán** y obtener su **ID Nitro (PO_ID)** —o el **SAP ID** si es
   una transferencia— junto con tienda, estado y cantidades.
2. **Órdenes de Hielo:** saber en qué orden abierta debe ingresar el hielo cada tienda, según el
   proveedor (= marca de hielo: Hielo Club, Hielo Fiesta, Iglú, KLYR, Yely, Pingüino…, de cualquier proveedor
   Turbo desde 2026-10-06), y enviar la foto del ticket del proveedor.

- **Para quién:** personal de tiendas Chedraui (Turbo) y Torre de Control CEDIS MX.
- **URL:** https://kevinsilva-rgb.github.io/NitroIds/ (GitHub Pages, rama `main`; verificada HTTP 200 el 2026-09-30).
- **Repo:** `kevinsilva-rgb/NitroIds` (**público**).
- **Versión:** sin número de versión; la versión vigente es el último commit de `main`.
- **En el CEDA Hub:** tarjeta "🔎 Buscador de Órdenes Nitro".
- **Tecnología:** HTML + Tailwind (CDN) + JavaScript sin frameworks. No tiene backend propio en este repo.

---

## 1. Arquitectura

```
index.html (GitHub Pages)
   ├── Buscador ──fetch GET──►  Web App "búsqueda" (AKfycbyar0C3…)  ──► Redash (queries sin confirmar)
   └── Hielo ─────fetch GET──►  Web App Control Hielo Chedraui (AKfycbxUy3…) ?api=ordenesHielo ──► Redash 138873
                  fetch POST─►  mismo Web App (accion=ticketHielo) ──► Drive + Sheet "Ticket Hielo"
```

| Backend | Deployment (URL `/exec`) | Código | Qué hace |
|---|---|---|---|
| **Búsqueda de IDs** | `https://script.google.com/macros/s/AKfycbyar0C3avos5tH4S5lte-Bjc00aAhp0dnqE0X2YIXPPOdolUEZrvJylodQ9q_cJC7Vhaw/exec` | **No versionado.** No aparece en `clasp list`; candidato: script vinculado al Sheet "IDS OCS Y ALBARANES" (`1424NYH8EyBLVJnap8S7gelMrFV8tUNwop3PzP9BfT6M`) | `GET ?externalId=<texto>&refrescar=<true/false>` → órdenes que coinciden |
| **Órdenes de hielo / tickets** | `https://script.google.com/macros/s/AKfycbxUy3nlvDOEHp20OzHcYJAH2N7f9El1eRjWl3lfVvNMJDw3EYRyz0E6j0dtKtDhHHjY/exec` | Repo `kevinsilva-rgb/Control-Hielo-Chedraui` (`Código.js`: `doGet`, `apiOrdenesHielo_`, `doPost`, `registrarTicketHielo_`) | `GET ?api=ordenesHielo&refrescar=…` y `POST` con `accion=ticketHielo` |

### Funciones de la página

| Función | Qué hace |
|---|---|
| `ejecutarBusqueda(forzarRefresco)` | Valida el texto, muestra el loader y llama `GET WEB_APP_URL?externalId=…&refrescar=…`. Con `error` muestra el mensaje; con `mensajeRefresco` muestra el aviso verde; con `data` pinta tarjetas. |
| `actualizarDataQueries()` | Botón "Actualizar Data": pone el botón en estado de carga y ejecuta la búsqueda con `refrescar=true` (el backend re-ejecuta sus queries en Redash). Se puede usar con la caja vacía. |
| `mostrarMultiplesDatos(lista)` | Pinta una tarjeta por orden encontrada, con el contador "Registros encontrados: N". |
| `alternarVistaHielo()` | Cambia entre el buscador y la vista de hielo; la primera vez carga las órdenes de hielo. |
| `cargarOrdenesHielo(forzar)` | `GET HIELO_API_URL&refrescar=…`, llena el dropdown de tiendas y recuerda la tienda y el proveedor elegidos al actualizar. |
| `elegirTiendaHielo()` / `mostrarOrdenesHielo()` | Llenan el dropdown de proveedor y pintan la orden a usar. |
| `seleccionarFotoTicket()` / `comprimirImagen()` | Leen la foto y la comprimen en el navegador (lado mayor ≤ 1280 px, JPEG calidad 0.72). |
| `enviarTicketHielo(i)` | `POST` JSON como `text/plain` (sin preflight CORS) con `accion: 'ticketHielo'`, datos de la orden y la foto en base64. |
| `copiarIdNitroCualquiera()` | Copia al portapapeles; el botón muestra "✓ Copiado" 2 s y recupera su texto y clases originales. |

No hay triggers, cache local ni almacenamiento en el navegador. Enter en la caja de búsqueda = Buscar.

### Manejo de errores

- Caja vacía → "Por favor, ingresa un término de búsqueda."
- `response.error` → se muestra `response.mensaje`; error de red → "Error al conectar con el servidor de la API de Redash."
  Siempre con la indicación de reintentar y, si persiste, avisar a **Torre de Control**.
- Hielo: error al cargar → "No se pudieron cargar las órdenes de hielo" (reintentar con 🔄 Actualizar).
- Ticket: imagen ilegible → "No se pudo leer la imagen"; fallo al enviar → "No se pudo enviar el ticket".

---

## 2. Fuentes de datos

### Contrato del backend de búsqueda (verificado en vivo el 2026-09-30)

`GET ?externalId=14212974&refrescar=false` → `{ error: false, data: [...] }` con 2 filas
(`CLOSED_PARTIAL_DELIVERY`, `CLOSED_ZERO_DELIVERY`). Campos por fila:

| Campo | Uso en la tarjeta |
|---|---|
| `externalId` | Título (número de albarán / OC) |
| `idNitro` | "ID NITRO (PO_ID)" — lo que se copia en órdenes normales |
| `sapId` | "SAP ID" — lo que se copia si es transferencia |
| `esTransferencia` | `true` → tarjeta roja con badge "🔄 Transferencia" |
| `tienda` | "Tienda Destino" |
| `estadoPo` | Badge de estado |
| `cantidadSolicitada`, `cantidadRecibida` | Cant. Solicitada / Cant. Recibida |
| `fechaCreacionMx` | Fecha (solo la parte antes del espacio) |
| `mensajeRefresco` (raíz, opcional) | Aviso verde tras "Actualizar Data" |

**Queries de Redash del backend de búsqueda: sin confirmar.** El código no está en ningún repo. Por
los campos (`sapId`, `esTransferencia`), candidatas probables (no verificadas): órdenes de compra de
Turbo (tipo 131730) y transferencias WMS (135829 "Detalle transferencias WMS - MX STORE", de Kevin).
Por eso no se guardó su SQL en `queries/`.

### Query de hielo (vía backend de Control Hielo Chedraui)

| ID | Nombre en Redash | DS | Granularidad | Filtros | Columnas |
|---|---|---|---|---|---|
| **138873** (desde 2026-10-06; antes 138487) | Ordenes de hielo - todos los proveedores y tiendas (90 dias + abiertas) | 10271 (MySQL turbo-po-savvy-ms) | 1 fila por PO × producto de hielo (la misma query que el dashboard de Control Hielo) | Producto con "hielo" en el nombre; todos los proveedores salvo "FABIANA prueba"; creadas en 90 días o todavía `SENT`/`AT_STORE`. El backend filtra abiertas (`SENT`/`AT_STORE` con Σ solicitado > Σ recibido), salta almacenes "INACTIVE" y agrupa por marca (`marcaHielo_`). Catálogo = tiendas y marcas de la query | `po_id, external_id (External ID o SAP ID), tienda, proveedor, estado, ean, producto, cantidad_solicitada, cantidad_recibida, fecha_creacion_mx, …` |

SQL vigente: [`queries/138873-ordenes-de-hielo-todos-los-proveedores-y-tiendas.sql`](queries/) (copia; la fuente de verdad está en el repo de Control Hielo).
Sin schedule en Redash. El backend acepta resultados de hasta **5 min** (`max_age 300`); con
`refrescar=true` fuerza re-ejecución (`max_age 0`).

Respuesta del endpoint: `{ error, actualizado: "aaaa-mm-dd HH:mm", tiendas: [{ tienda, proveedores:
[{ proveedor, totalAbiertas, ordenes: [{ idNitro, externalId, estadoPo, fechaCreacionMx, productos,
cantidadSolicitada, cantidadRecibida }] }] }] }`.

### Google Sheet y Drive (escritos por el backend de Control Hielo)

| Recurso | ID | Detalle |
|---|---|---|
| Sheet **Ticket Hielo** | `1JB-eKW2W8zcHUeBvBFKmyb873KRWxXspGE0fQMor4C0` | Pestaña `Hoja 1`. Columnas: Fecha registro (texto, hora CDMX), Tienda, Proveedor, ID Nitro (PO_ID), External ID, Estado PO, Fecha creación orden, Cant. solicitada, Foto ticket (URL), ID archivo foto |
| Carpeta Drive **Ticket Hielo - Fotos** | `14WvVMhKqKeKTxiImfX-2JzGfoAEf5GKw` | Junto al sheet; fotos `Ticket_<tienda>_<idNitro>_<aaaaMMdd_HHmmss>.jpg`, públicas con link (solo lectura) |

---

## 3. Lógicas de negocio

### Buscador
- La búsqueda y el match (exacto o parcial) los hace el backend; la página solo muestra lo que devuelve.
- **Orden normal:** se destaca y copia el **ID Nitro (PO_ID)**. **Transferencia** (`esTransferencia`):
  se destaca y copia el **SAP ID**, y hay otro botón para copiar el ID.
- **Color del estado:** rojo si contiene `CANCEL` o `ZERO` (se evalúa primero, para que
  `CLOSED_ZERO_DELIVERY` no salga verde); verde si contiene `SENT`, `DELIVERY` o `COMPLETED`; ámbar
  en cualquier otro caso (ej. `AT_STORE`).
- `cantidadRecibida` vacía o "N/A" se muestra como `0`.

### Órdenes de hielo (definiciones de Kevin, 2026-09-28)
- Desde 2026-10-06: **todos los proveedores** Turbo (antes solo TIENDAS CHEDRAUI).
- **Abierta** = `SENT` o `AT_STORE` con hielo pendiente de recibir (`PARTIAL_DELIVERY` no cuenta).
- **"Proveedor"** = marca del producto de hielo, por EAN (Hielo Club, Hielo Fiesta, Iglú, KLYR, Yely, Pingüino,
  Tun Ha, Stark, Cristalito…). Un Hielo Club por Chedraui y uno directo caen juntos (decisión de Kevin,
  2026-10-06). Cada tienda ve solo las marcas que pidió en 90 días.
- Flujo: tienda → proveedor → se muestra **solo la orden abierta más antigua** (por fecha de creación
  y luego PO_ID), etiquetada "Ingresar aquí · la más antigua". Si hay más, se avisa "La tienda tiene N
  órdenes abiertas de X; se muestra la más antigua".
- **Pendiente** = `max(0, solicitada − recibida)`.
- Sin órdenes abiertas para ese proveedor → aviso ámbar: comunicarse con Torre de Control antes de
  ingresar hielo.
- Los dropdowns muestran el conteo "(N abiertas)" / "sin órdenes abiertas".
- Antigüedad: "hoy", "hace 1 día", "hace N días".

### Ticket del proveedor
- Se adjunta una foto por tarjeta, se comprime en el celular, se previsualiza y se envía. El backend
  la guarda en Drive y agrega la fila al sheet. No registra quién envía (solo la tienda).

---

## 4. Pantallas

**Encabezado:** "🚀 Buscador de Órdenes Nitro" · "CONSULTA ID DESDE NITRO" · botón **🧊 Órdenes de
Hielo** (cambia a "🔎 Volver al buscador de IDs").

**Vista Buscador**
- Caja "Ingresar Numero de Albaran u Orden de Compra" (ej. `14212974`) + botón **Buscar**.
- Botón **🔄 Actualizar Data** (fuerza el refresh de Redash en el backend).
- Loader, aviso verde de refresh, caja roja de error y contador de registros.
- **Tarjeta por orden:** External ID (+ badge de transferencia), fecha, badge de estado, ID Nitro o
  SAP ID con botón **Copiar** / **Copiar SAP**, Tienda Destino, Cant. Solicitada y Cant. Recibida.

**Vista Órdenes de Hielo**
- Botón **🔄 Actualizar** (refresh forzado), dropdown **Tienda**, dropdown **Proveedor** y "Datos al <fecha>".
- **Tarjeta de la orden:** etiqueta "Ingresar aquí · la más antigua", proveedor, estado, fecha y
  antigüedad, **ID Nitro (PO_ID)** con Copiar, External ID con Copiar, producto, Solicitada /
  Recibida / Pendiente, y el bloque **📷 Adjuntar foto del ticket del proveedor** → vista previa →
  **Enviar ticket** → "✓ Ticket enviado a Torre de Control (orden N)".

---

## 5. Configuración sensible

- La página no guarda secretos: solo las URLs públicas de los dos Web Apps (`WEB_APP_URL`, `HIELO_WEBAPP_URL`).
- La API key de Redash vive en los backends (Script Properties `REDASH_API_KEY`). El backend de
  búsqueda la tuvo hardcodeada hasta la rotación del 2026-08-27 (ver `KNOWN_PROBLEMS.md` en ai-brain).

## 6. Despliegue

`git push` a `main` → GitHub Pages publica solo (1-2 min). Si se cambia el deployment o el `doGet`
de Control Hielo Chedraui, hay que actualizar `HIELO_WEBAPP_URL` aquí. Si cambia la URL de Pages,
actualizar también la tarjeta del CEDA Hub.

## 7. Problemas conocidos y riesgos

- **Backend de búsqueda no versionado ni localizado**: no se puede auditar qué queries usa ni cómo
  hace el match. Pendiente abrir el Sheet "IDS OCS Y ALBARANES" → Extensiones → Apps Script.
- **Acceso abierto**: repo público + Web Apps anónimos. Cualquiera con la URL puede consultar POs,
  forzar refresh en Redash y subir fotos al sheet de tickets.
- `data.estadoPo.toString()` falla si el estado viene `null`.
- Las tarjetas del buscador insertan datos con `innerHTML` sin escapar (la vista de hielo sí escapa).
- La vista de hielo depende de otro proyecto (Control Hielo Chedraui): un cambio ahí rompe el botón.
