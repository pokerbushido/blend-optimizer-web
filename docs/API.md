# API Documentation

Documentazione dettagliata delle API REST del sistema Blend Optimizer.

## Base URL

```
Development: http://localhost:8000
Production: http://your-server:8000
```

Tutte le richieste API sono prefissate con `/api` (eccetto health check).

## Autenticazione

Il sistema usa **JWT (JSON Web Tokens)** per l'autenticazione.

### Ottenere un Token

**Endpoint**: `POST /api/auth/login`

**Body (form-data)**:
```
username: admin
password: changeme123
```

**Response**:
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

### Usare il Token

Includi il token in ogni richiesta nell'header `Authorization`:

```
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

### Scadenza Token

- **Default**: 8 ore (480 minuti)
- Configurabile via `ACCESS_TOKEN_EXPIRE_MINUTES` in `.env`

---

## Endpoints

### 🔐 Autenticazione

#### POST /api/auth/login
Login con username e password.

**Request**:
```bash
curl -X POST "http://localhost:8000/api/auth/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin&password=changeme123"
```

**Response 200**:
```json
{
  "access_token": "eyJhbGciOi...",
  "token_type": "bearer"
}
```

**Response 401** (credenziali errate):
```json
{
  "detail": "Incorrect username or password"
}
```

#### POST /api/auth/login/json
Alternativa con JSON body.

**Request**:
```json
{
  "username": "admin",
  "password": "changeme123"
}
```

#### GET /api/auth/me
Ottieni informazioni utente corrente.

**Headers**: `Authorization: Bearer <token>`

**Response 200**:
```json
{
  "id": "uuid",
  "username": "admin",
  "email": "admin@company.local",
  "full_name": "Administrator",
  "role": "admin",
  "is_active": true,
  "created_at": "2025-01-04T10:00:00Z",
  "last_login": "2025-01-04T15:30:00Z"
}
```

---

### 👥 Gestione Utenti (Admin Only)

#### GET /api/users/
Lista tutti gli utenti.

**Permissions**: Admin

**Query Parameters**:
- `skip` (int): Offset pagination (default: 0)
- `limit` (int): Limite risultati (default: 100)

**Response 200**:
```json
[
  {
    "id": "uuid",
    "username": "admin",
    "email": "admin@company.local",
    "role": "admin",
    "is_active": true,
    ...
  },
  ...
]
```

#### POST /api/users/
Crea nuovo utente.

**Permissions**: Admin

**Request Body**:
```json
{
  "username": "operatore1",
  "email": "operatore1@company.local",
  "password": "password123",
  "full_name": "Mario Rossi",
  "role": "operatore"
}
```

**Roles**: `admin`, `operatore`, `visualizzatore`

**Response 201**:
```json
{
  "id": "uuid",
  "username": "operatore1",
  "email": "operatore1@company.local",
  "role": "operatore",
  ...
}
```

#### GET /api/users/{user_id}
Ottieni dettagli utente specifico.

**Permissions**: Admin

#### PATCH /api/users/{user_id}
Aggiorna utente.

**Permissions**: Admin

**Request Body** (campi opzionali):
```json
{
  "email": "nuovo@email.com",
  "full_name": "Nuovo Nome",
  "role": "operatore",
  "is_active": false
}
```

#### DELETE /api/users/{user_id}
Elimina utente (non puoi eliminare te stesso).

**Permissions**: Admin

**Response 204**: No content

#### POST /api/users/me/password
Cambia la propria password.

**Permissions**: Qualsiasi utente autenticato

**Request Body**:
```json
{
  "old_password": "vecchia_password",
  "new_password": "nuova_password_sicura"
}
```

---

### 📦 Inventario

#### POST /api/inventory/upload
Upload file CSV inventario (sostituisce inventario esistente).

**Permissions**: Admin

**Request**: multipart/form-data
```bash
curl -X POST "http://localhost:8000/api/inventory/upload" \
  -H "Authorization: Bearer $TOKEN" \
  -F "file=@inventario.csv" \
  -F "notes=Caricamento gennaio 2025"
```

**Form Fields**:
- `file`: File CSV (required)
- `notes`: Note opzionali (optional)

**Response 201**:
```json
{
  "id": "uuid",
  "uploaded_by": "uuid-admin",
  "filename": "inventario.csv",
  "upload_timestamp": "2025-01-04T15:00:00Z",
  "total_lots": 1523,
  "status": "completed",
  "notes": "Caricamento gennaio 2025"
}
```

**CSV Format Expected**:

Colonne minime richieste:
- `SCO_ART`: Codice articolo
- `SCO_LOTT`: Codice lotto
- `SCO_QTA`: Quantità disponibile (kg)

Colonne qualità (opzionali ma raccomandate):
- `SCO_DownCluster_Real`: DC % reale
- `SCO_FillPower_Real`: FP reale
- `SCO_Duck`: Duck %
- `SCO_OE`: Other Elements %
- ...e altre (vedi schema database)

#### GET /api/inventory/lots
Lista lotti inventario con filtri.

**Permissions**: Visualizzatore, Operatore, Admin

**Query Parameters**:
- `skip` (int): Offset (default: 0)
- `limit` (int): Limite (default: 100, max: 1000)
- `article_code` (string): Filtra per codice articolo (partial match)
- `species` (string): Filtra per specie (O, A, OA, C)
- `min_dc` (float): DC minimo
- `max_dc` (float): DC massimo
- `min_available_kg` (float): Kg disponibili minimo
- `only_active` (bool): Solo lotti attivi (default: true)

**Example**:
```bash
GET /api/inventory/lots?species=O&min_dc=80&limit=20
```

**Response 200**:
```json
[
  {
    "id": "uuid",
    "article_code": "3|POB",
    "lot_code": "DY|2025|32277|1",
    "description": "Piumino Oca Bianco",
    "dc_real": 85.5,
    "fp_real": 720.0,
    "duck_real": 0.0,
    "available_kg": 150.50,
    "species": "O",
    "is_active": true
  },
  ...
]
```

#### GET /api/inventory/lots/{lot_id}
Dettagli completi di un lotto specifico.

**Permissions**: Visualizzatore, Operatore, Admin

**Response 200**:
```json
{
  "id": "uuid",
  "article_code": "3|POB",
  "lot_code": "DY|2025|32277|1",
  "description": "Piumino Oca Bianco Premium",
  "dc_real": 85.5,
  "fp_real": 720.0,
  "duck_real": 0.0,
  "oe_real": 2.1,
  "feather_real": 12.4,
  "oxygen_real": 7.5,
  "turbidity_real": 18.2,
  "dc_nominal": 85.0,
  "fp_nominal": 720.0,
  "total_fibres": 1.2,
  "broken": 0.8,
  "landfowl": 0.5,
  "available_kg": 150.50,
  "cost_per_kg": 45.50,
  "group_code": "3",
  "species": "O",
  "color": "B",
  "state": "P",
  "certification": null,
  "quality_nominal": "DC85 FP720",
  "lab_notes": "Note laboratorio...",
  "is_estimated": false,
  "dc_was_imputed": false,
  "fp_was_imputed": false,
  "is_active": true,
  "created_at": "2025-01-04T10:00:00Z",
  "updated_at": "2025-01-04T10:00:00Z"
}
```

#### GET /api/inventory/stats
Statistiche aggregate inventario.

**Permissions**: Visualizzatore, Operatore, Admin

**Response 200**:
```json
{
  "total_lots": 1523,
  "total_kg": 45230.50,
  "avg_dc": 78.45,
  "avg_fp": 672.30,
  "by_species": {
    "O": {
      "count": 523,
      "total_kg": 15230.50
    },
    "A": {
      "count": 782,
      "total_kg": 23500.00
    },
    "OA": {
      "count": 218,
      "total_kg": 6500.00
    }
  }
}
```

#### GET /api/inventory/uploads
Cronologia upload CSV.

**Permissions**: Admin

**Response 200**:
```json
[
  {
    "id": "uuid",
    "uploaded_by": "uuid-admin",
    "filename": "inventario_gennaio.csv",
    "upload_timestamp": "2025-01-04T15:00:00Z",
    "total_lots": 1523,
    "status": "completed"
  },
  ...
]
```

---

### 🎯 Ottimizzazione Miscele

#### POST /api/optimize/blend
Richiedi ottimizzazione miscela.

**Permissions**: Operatore, Admin

**Request Body**:
```json
{
  "target_dc": 82.0,
  "target_fp": 700.0,
  "target_duck": 20.0,
  "species": "O",
  "color": "B",
  "water_repellent": false,
  "exclude_raw_materials": true,
  "total_kg": 100.0,
  "num_solutions": 3,
  "max_lots": 10
}
```

**Fields**:
- `target_dc` (float, optional): Down Cluster % target (0-100)
- `target_fp` (float, optional): Fill Power target
- `target_duck` (float, optional): Duck % target (0-100)
- `species` (string, optional): O, A, OA, C
- `color` (string, optional): B, G, PW, NPW
- `water_repellent` (bool, optional): Richiede GWR/NWR
- `exclude_raw_materials` (bool): Escludi materiali grezzi (default: true)
- `total_kg` (float, required): Kg totali richiesti
- `num_solutions` (int): Numero soluzioni (1-10, default: 3)
- `max_lots` (int): Max lotti per miscela (2-15, default: 10)

**Response 200**:
```json
{
  "request_id": "uuid",
  "requirements": {
    "target_dc": 82.0,
    "target_fp": 700.0,
    ...
  },
  "solutions": [
    {
      "solution_number": 1,
      "lots": [
        {
          "lot_id": "uuid",
          "article_code": "3|POB",
          "lot_code": "DY|2025|32277|1",
          "description": "Piumino Oca Bianco",
          "kg_used": 45.50,
          "percentage": 45.50,
          "dc_real": 85.5,
          "fp_real": 720.0,
          "duck_real": 0.0,
          "cost_per_kg": 45.50
        },
        ...
      ],
      "total_kg": 100.0,
      "total_cost": 4125.50,
      "cost_per_kg": 41.26,
      "avg_dc": 82.15,
      "avg_fp": 698.50,
      "avg_duck": 18.75,
      "dc_compliance": true,
      "fp_compliance": true,
      "duck_compliance": true,
      "score": 8523.45
    },
    ...
  ],
  "generated_at": "2025-01-04T15:30:00Z",
  "computation_time_seconds": 2.34
}
```

**Compliance Criteria**:
- `dc_compliance`: |DC_avg - DC_target| ≤ 3%
- `fp_compliance`: |FP_avg - FP_target| ≤ 5%
- `duck_compliance`: |Duck_avg - Duck_target| ≤ 5%

#### GET /api/optimize/{request_id}/status
Status ottimizzazione (per future async implementation).

**Permissions**: Operatore, Admin

**Response 200**:
```json
{
  "request_id": "uuid",
  "status": "completed",
  "progress": 100,
  "result": { ... }
}
```

#### GET /api/optimize/{request_id}/results
Risultati ottimizzazione (JSON).

**Permissions**: Operatore, Admin

Stesso formato della risposta POST /api/optimize/blend.

#### GET /api/optimize/{request_id}/excel
Download risultati come file Excel.

**Permissions**: Operatore, Admin

**Response**: File Excel (application/vnd.openxmlformats-officedocument.spreadsheetml.sheet)

**Headers**:
```
Content-Disposition: attachment; filename="blend_optimization_20250104_153000.xlsx"
```

**Excel Format**:
- Multi-sheet (1 foglio per soluzione)
- 23 colonne dettagliate per lotto
- Sezione riepilogo con metriche aggregate
- Compliance indicators (✅⚠️❌)
- Formattazione colori e bordi

---

## Status Codes

| Code | Meaning |
|------|---------|
| 200 | Success |
| 201 | Created |
| 204 | No Content (delete successful) |
| 400 | Bad Request (validation error) |
| 401 | Unauthorized (token missing/invalid) |
| 403 | Forbidden (insufficient permissions) |
| 404 | Not Found |
| 500 | Internal Server Error |

---

## Error Response Format

```json
{
  "detail": "Error message here"
}
```

**Validation Errors** (422):
```json
{
  "detail": [
    {
      "loc": ["body", "target_dc"],
      "msg": "ensure this value is less than or equal to 100",
      "type": "value_error.number.not_le"
    }
  ]
}
```

---

## Rate Limiting

Attualmente non implementato. Per produzione, considerare:
- Max requests per IP/utente
- Timeout ottimizzazione: fino a 5 minuti per richieste complesse (es. grandi quantità con vincoli specifici)

---

## Interactive Documentation

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

Usa Swagger UI per testare direttamente le API dal browser!

---

## Examples

Vedi [scripts/test_api.sh](../scripts/test_api.sh) per esempi completi di uso delle API.
