# Plan: Employee Self-Service Portal

**Branch:** `claude/employee-self-service-portal-76d459`

**Fecha:** 2026-01-04

---

## 📋 Resumen Ejecutivo

Convertir el portal en un portal de self-service completo para empleados con tres componentes principales:

1. **✈️ Sistema de Aprobación de Viajes** - Solicitudes de viáticos con aprobación Manager → HR Admin
2. **🛠️ Sistema de Aprobación de Herramientas** - Solicitudes de equipo de trabajo con mismo flujo de aprobación
3. **📦 Gestión de Activos** - Vista para managers para rastrear activos asignados a empleados

---

## 🎯 Requerimientos Funcionales

### 1. Sistema de Aprobación de Viajes

**Campos del Formulario:**
- Itinerario (origen, destino, fechas)
- Propósito del viaje
- Lista de gastos estimados (categorizados)
- Monto total estimado (en la moneda del empleado - `salary_currency`)
- Tipo de desembolso: Anticipo o Reembolso

**Flujo de Aprobación:**
1. Empleado crea solicitud → Status: `PENDING`
2. Manager aprueba → Status: `MANAGER_APPROVED`
3. HR Admin aprueba → Status: `APPROVED`
4. Sistema envía email a `pagos@edvolution.io` con copia a empleado y manager

**Email Final (cuando status = APPROVED):**
- **To:** `FINANCE_EMAIL` (variable de entorno - ej: pagos@edvolution.io)
- **CC:** empleado, manager
- **Subject:** Aprobación de Viaje - [Nombre Empleado] - [Destino]
- **Body:** Itinerario completo, gastos detallados, monto total, tipo de desembolso

**Variables de Configuración Requeridas:**
- `FINANCE_EMAIL` - Email del área de administración para pagos
- `TOOLS_PROCUREMENT_EMAIL` - Email para compra de herramientas (puede ser el mismo que FINANCE_EMAIL)

### 2. Sistema de Aprobación de Herramientas

**Opciones Predefinidas:**
- Audífonos
- Portátil
- Monitor
- Teclado/Mouse
- Silla
- Escritorio
- **Otro** (campo abierto con precio y enlace al producto)

**Campos:**
- Tipo de herramienta (selección o custom)
- Justificación
- Precio estimado (si es custom)
- Enlace al producto (si es custom)

**Flujo de Aprobación:**
Igual que viajes: Empleado → Manager → HR Admin

### 3. Gestión de Activos (Vista de Manager)

**Funcionalidad:**
- Ver activos asignados a cada empleado del equipo
- Agregar/editar activos
- Categorías de activos:
  - **Hardware:** Laptop, monitor, teclado, mouse, audífonos, silla, escritorio
  - **Suscripciones:** Google Workspace, Mailchimp, Odoo, Gain, otros
- Campos por activo:
  - Tipo de activo
  - Descripción
  - Fecha de asignación
  - Número de serie / ID (si aplica)
  - Costo (opcional)
  - Estado (activo, devuelto, dañado)

---

## 🏗️ Arquitectura Técnica

### Base de Datos (Firestore)

**Nueva Colección: `travel_requests`**
```python
{
  "request_id": "auto-generated",
  "employee_email": "user@edvolution.io",
  "origin": "Mexico City",
  "destination": "San Francisco",
  "start_date": "2026-02-01",
  "end_date": "2026-02-05",
  "purpose": "Client meeting",
  "expenses": [
    {
      "category": "airfare",
      "description": "Round trip flight",
      "estimated_cost": 500.00
    },
    {
      "category": "accommodation",
      "description": "4 nights hotel",
      "estimated_cost": 800.00
    },
    {
      "category": "meals",
      "description": "Per diem",
      "estimated_cost": 200.00
    },
    {
      "category": "transportation",
      "description": "Ground transport",
      "estimated_cost": 100.00
    }
  ],
  "total_estimated_cost": 1600.00,
  "currency": "USD",  // From employee.salary_currency
  "disbursement_type": "advance",  // or "reimbursement"
  "status": "pending",  // pending, manager_approved, approved, rejected
  "manager_email": "manager@edvolution.io",
  "manager_approved_at": null,
  "manager_approved_by": null,
  "admin_approved_at": null,
  "admin_approved_by": null,
  "rejected_at": null,
  "rejected_by": null,
  "rejection_reason": null,
  "created_at": "2026-01-04T12:00:00Z",
  "updated_at": "2026-01-04T12:00:00Z"
}
```

**Nueva Colección: `tool_requests`**
```python
{
  "request_id": "auto-generated",
  "employee_email": "user@edvolution.io",
  "tool_type": "laptop",  // or "headphones", "monitor", "keyboard_mouse", "chair", "desk", "custom"
  "custom_description": null,  // Only if tool_type is "custom"
  "custom_price": null,  // Only if tool_type is "custom"
  "custom_link": null,  // Only if tool_type is "custom"
  "justification": "Current laptop is 5 years old and slow",
  "status": "pending",  // Same as travel_requests
  "manager_email": "manager@edvolution.io",
  "manager_approved_at": null,
  "manager_approved_by": null,
  "admin_approved_at": null,
  "admin_approved_by": null,
  "rejected_at": null,
  "rejected_by": null,
  "rejection_reason": null,
  "created_at": "2026-01-04T12:00:00Z",
  "updated_at": "2026-01-04T12:00:00Z"
}
```

**Nueva Colección: `employee_assets`**
```python
{
  "asset_id": "auto-generated",
  "employee_email": "user@edvolution.io",
  "asset_type": "hardware",  // or "subscription"
  "category": "laptop",  // laptop, monitor, keyboard, mouse, headphones, chair, desk, workspace, mailchimp, odoo, gain, other
  "description": "MacBook Pro 16\" 2024",
  "serial_number": "C02XK0ECMD6M",
  "assigned_date": "2024-06-15",
  "cost": 2500.00,
  "currency": "USD",
  "status": "active",  // active, returned, damaged
  "notes": "Purchased from Apple Store",
  "assigned_by": "hr@edvolution.io",
  "created_at": "2024-06-15T10:00:00Z",
  "updated_at": "2024-06-15T10:00:00Z"
}
```

### Configuration (settings.py)

**Nuevas Variables de Entorno:**
```python
# Notification Emails for Approvals
FINANCE_EMAIL = os.getenv('FINANCE_EMAIL', 'pagos@edvolution.io')
TOOLS_PROCUREMENT_EMAIL = os.getenv('TOOLS_PROCUREMENT_EMAIL', 'pagos@edvolution.io')
```

**Agregar a Cloud Run Environment Variables:**
- `FINANCE_EMAIL` = pagos@edvolution.io (o el email que corresponda)
- `TOOLS_PROCUREMENT_EMAIL` = pagos@edvolution.io (o el email que corresponda)

### Backend (Flask)

**Nuevos Modelos:**
- `backend/app/models/travel_request.py` - Similar a TimeOffRequest
- `backend/app/models/tool_request.py` - Similar a TimeOffRequest
- `backend/app/models/employee_asset.py` - Nuevo modelo para activos

**Nuevas Rutas:**
- `backend/app/api/travel_routes.py`:
  - `POST /api/travel/requests` - Crear solicitud
  - `GET /api/travel/requests` - Ver mis solicitudes
  - `GET /api/travel/requests/pending` - Ver solicitudes pendientes de aprobar
  - `POST /api/travel/requests/<id>/approve-manager` - Aprobar como manager
  - `POST /api/travel/requests/<id>/approve-admin` - Aprobar como admin
  - `POST /api/travel/requests/<id>/reject` - Rechazar

- `backend/app/api/tool_routes.py`:
  - Mismos endpoints que travel_routes

- `backend/app/api/asset_routes.py`:
  - `GET /api/employees/<email>/assets` - Ver activos de un empleado
  - `POST /api/employees/<email>/assets` - Agregar activo
  - `PUT /api/assets/<id>` - Actualizar activo
  - `DELETE /api/assets/<id>` - Eliminar activo

**Servicios Firestore Extendidos:**
- Agregar métodos en `FirestoreService`:
  - `create_travel_request()`
  - `get_travel_request()`
  - `update_travel_request()`
  - `get_pending_travel_requests_for_manager()`
  - `get_pending_travel_requests_for_admin()`
  - Similar para tool_requests y employee_assets

**Servicio de Email:**
- Extender `NotificationService.send_email()` para enviar email a pagos@edvolution.io cuando un viaje sea aprobado
- Template HTML para email de aprobación de viaje con todos los detalles

### Frontend (React)

**Nuevos Componentes:**

1. **TravelRequestForm.jsx** - Formulario para crear solicitud de viaje
   - Campos: origen, destino, fechas, propósito
   - Tabla dinámica de gastos (agregar/eliminar filas)
   - Selección de tipo de desembolso
   - Preview del total en la moneda del empleado

2. **TravelRequestsView.jsx** - Vista de mis solicitudes de viaje
   - Tabla con historial de solicitudes
   - Filtros por status
   - Botón "Nueva Solicitud"

3. **ToolRequestForm.jsx** - Formulario para solicitar herramientas
   - Dropdown con opciones predefinidas + "Otro"
   - Campos condicionales para custom (precio, enlace)
   - Justificación

4. **ToolRequestsView.jsx** - Vista de mis solicitudes de herramientas
   - Similar a TravelRequestsView

5. **ApprovalsView.jsx** - Vista unificada de aprobaciones pendientes
   - Tabs: "Time Off", "Travel", "Tools"
   - Cards por solicitud con botones "Approve" / "Reject"
   - Modal para ver detalles completos

6. **EmployeeAssetsView.jsx** - Vista de activos (para managers)
   - Tabla de activos del empleado
   - Modal para agregar/editar activos
   - Filtros por tipo de activo

**Actualización de Dashboard.jsx:**
- Agregar tabs:
  - "✈️ Travel Requests"
  - "🛠️ Tool Requests"
  - "⏳ Approvals" (unificado para time-off, travel, tools)
- Para managers: agregar sección de activos en EmployeeDetailModal

**Actualización de api.js:**
```javascript
travelAPI: {
  create: (data) => fetchAPI('/api/travel/requests', { method: 'POST', body: JSON.stringify(data) }),
  getMyRequests: () => fetchAPI('/api/travel/requests'),
  getPendingApprovals: () => fetchAPI('/api/travel/requests/pending'),
  approveAsManager: (id) => fetchAPI(`/api/travel/requests/${id}/approve-manager`, { method: 'POST' }),
  approveAsAdmin: (id) => fetchAPI(`/api/travel/requests/${id}/approve-admin`, { method: 'POST' }),
  reject: (id, reason) => fetchAPI(`/api/travel/requests/${id}/reject`, { method: 'POST', body: JSON.stringify({ reason }) }),
},
toolAPI: {
  // Similar a travelAPI
},
assetAPI: {
  getEmployeeAssets: (email) => fetchAPI(`/api/employees/${email}/assets`),
  createAsset: (email, data) => fetchAPI(`/api/employees/${email}/assets`, { method: 'POST', body: JSON.stringify(data) }),
  updateAsset: (id, data) => fetchAPI(`/api/assets/${id}`, { method: 'PUT', body: JSON.stringify(data) }),
  deleteAsset: (id) => fetchAPI(`/api/assets/${id}`, { method: 'DELETE' }),
}
```

---

## 📝 Patrón de Reutilización de Código

**La lógica de aprobación ya existe en TimeOffRequest y puede ser reutilizada:**

1. ✅ Mismo flujo de dos niveles (Manager → Admin)
2. ✅ Mismos estados (PENDING, MANAGER_APPROVED, APPROVED, REJECTED)
3. ✅ Mismos métodos (approve_by_manager, approve_by_admin, reject)
4. ✅ Misma lógica de permisos (can_approve_manager, can_approve_admin)

**Estrategia:**
- Crear clase base `ApprovalRequest` con la lógica común
- `TimeOffRequest`, `TravelRequest`, `ToolRequest` heredan de `ApprovalRequest`
- O simplemente copiar y adaptar el patrón

---

## 🚀 Plan de Implementación

### Fase 1: Modelos y Base de Datos ✅
1. Crear modelos: `TravelRequest`, `ToolRequest`, `EmployeeAsset`
2. Definir enums para categorías de gastos, tipos de herramientas, tipos de activos
3. Agregar métodos a FirestoreService

### Fase 2: Backend API ✅
1. Crear rutas para travel requests (CRUD + aprobaciones)
2. Crear rutas para tool requests (CRUD + aprobaciones)
3. Crear rutas para employee assets (CRUD)
4. Implementar lógica de email para aprobaciones finales
5. Agregar validaciones y permisos

### Fase 3: Frontend - Travel Requests ✅
1. Crear TravelRequestForm component
2. Crear TravelRequestsView component
3. Integrar con Dashboard
4. Conectar con API

### Fase 4: Frontend - Tool Requests ✅
1. Crear ToolRequestForm component
2. Crear ToolRequestsView component
3. Integrar con Dashboard
4. Conectar con API

### Fase 5: Frontend - Aprobaciones ✅
1. Crear ApprovalsView unificado (time-off, travel, tools)
2. Actualizar notificaciones de aprobaciones pendientes
3. Conectar con APIs

### Fase 6: Frontend - Assets Management ✅
1. Crear EmployeeAssetsView component
2. Integrar en EmployeeDetailModal para managers
3. Conectar con API

### Fase 7: Testing & Deployment ✅
1. Probar flujo completo de travel request
2. Probar flujo completo de tool request
3. Probar gestión de activos
4. Verificar emails
5. Deploy con traffic splitting
6. Test en producción
7. Merge a main

---

## ⚠️ Consideraciones

### Seguridad
- Validar que solo el empleado pueda crear sus propias solicitudes
- Validar que solo managers puedan aprobar solicitudes de su equipo
- Validar que solo admins puedan aprobar como admin
- Validar que solo managers/admins puedan ver/editar activos

### Email
- Usar `NotificationService.send_email()` existente
- Email a `FINANCE_EMAIL` (configuración) solo cuando status = APPROVED
- **CC:** Siempre incluir empleado y manager en copia
- Para tool requests: enviar a `TOOLS_PROCUREMENT_EMAIL` (puede ser el mismo)
- Incluir toda la información relevante en formato legible
- Usar template HTML profesional
- **NO hardcodear emails** - usar variables de configuración del sistema

### UX
- Formularios claros y fáciles de usar
- Preview de costos totales antes de submit
- Confirmaciones antes de aprobar/rechazar
- Feedback visual claro del estado de cada solicitud
- Mobile-friendly

### Performance
- Paginar solicitudes si hay muchas
- Índices en Firestore para queries frecuentes
- Cache de datos cuando sea apropiado

---

## 📊 Métricas de Éxito

- ✅ Empleados pueden crear solicitudes de viaje y herramientas
- ✅ Managers ven y aprueban solicitudes de su equipo
- ✅ HR Admins ven y aprueban solicitudes finales
- ✅ Email automático a pagos@edvolution.io funciona correctamente
- ✅ Managers pueden gestionar activos de empleados
- ✅ UI es intuitiva y mobile-friendly
- ✅ Audit trail completo de todas las aprobaciones

---

## 🎯 Próximos Pasos

1. ✅ Revisar y aprobar este plan
2. 🔄 Comenzar implementación por fases
3. 🔄 Testing incremental en cada fase
4. 🔄 Deploy con traffic splitting al completar
5. 🔄 Merge a main después de validación

---

**¿Estás de acuerdo con este plan? ¿Algún ajuste o clarificación antes de empezar?** 🚀
