# Architettura Sistema - Blend Optimizer Web

## Indice

- [Overview](#overview)
- [Architettura High-Level](#architettura-high-level)
- [Stack Tecnologico](#stack-tecnologico)
- [Componenti Sistema](#componenti-sistema)
- [Flussi Dati](#flussi-dati)
- [Database Schema](#database-schema)
- [API Design](#api-design)
- [Sicurezza](#sicurezza)
- [Deploy e Infrastructure](#deploy-e-infrastructure)
- [Performance e Scalabilità](#performance-e-scalabilità)
- [Decisioni Architetturali](#decisioni-architetturali)

---

## Overview

Blend Optimizer è un'applicazione web full-stack enterprise per l'ottimizzazione automatica di miscele (blend) di piuma e piumino. L'architettura segue un pattern **3-tier classico** con separazione netta tra presentazione, business logic e persistenza.

### Obiettivi Architetturali

1. **Modularità**: Separazione chiara tra layer e componenti
2. **Riusabilità**: Core algorithm condiviso con optimizer_v33
3. **Scalabilità**: Preparato per crescita utenti e dati
4. **Manutenibilità**: Codice pulito, documentato, testabile
5. **Sicurezza**: Autenticazione, autorizzazione, validazione input
6. **Performance**: Response time < 2s per ottimizzazioni standard

---

## Architettura High-Level

```
┌─────────────────────────────────────────────────────────────┐
│                        CLIENT LAYER                          │
│                                                               │
│  ┌──────────────────────────────────────────────────────┐  │
│  │           React Frontend (TypeScript)                 │  │
│  │  - Components (UI + Layout)                          │  │
│  │  - State Management (Zustand)                        │  │
│  │  - API Client (Axios)                                │  │
│  │  - Routing (React Router)                            │  │
│  └──────────────────────────────────────────────────────┘  │
│                            ▼                                 │
│                     HTTPS (Nginx)                            │
└─────────────────────────────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────┐
│                     APPLICATION LAYER                        │
│                                                               │
│  ┌──────────────────────────────────────────────────────┐  │
│  │           FastAPI Backend (Python 3.11)               │  │
│  │                                                        │  │
│  │  ┌────────────────────────────────────────────────┐ │  │
│  │  │  API Endpoints (REST)                          │ │  │
│  │  │  /api/auth, /api/inventory,                   │ │  │
│  │  │  /api/optimize, /api/users                     │ │  │
│  │  └────────────────────────────────────────────────┘ │  │
│  │                       ▼                               │  │
│  │  ┌────────────────────────────────────────────────┐ │  │
│  │  │  Business Logic Services                       │ │  │
│  │  │  - InventoryService                            │ │  │
│  │  │  - OptimizerService                            │ │  │
│  │  │  - ExcelExportService                          │ │  │
│  │  │  - SecurityService                             │ │  │
│  │  └────────────────────────────────────────────────┘ │  │
│  │                       ▼                               │  │
│  │  ┌────────────────────────────────────────────────┐ │  │
│  │  │  Core Optimizer Engine                         │ │  │
│  │  │  - Optimizer (multi-criteria scoring)          │ │  │
│  │  │  - Inventory (lot management)                  │ │  │
│  │  │  - Compatibility (rules engine)                │ │  │
│  │  │  - ExcelExport (report generator)              │ │  │
│  │  └────────────────────────────────────────────────┘ │  │
│  │                       ▼                               │  │
│  │  ┌────────────────────────────────────────────────┐ │  │
│  │  │  Data Access Layer (SQLAlchemy ORM)            │ │  │
│  │  │  - Models (User, InventoryLot, etc.)           │ │  │
│  │  │  - Repositories                                 │ │  │
│  │  └────────────────────────────────────────────────┘ │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────┐
│                      PERSISTENCE LAYER                       │
│                                                               │
│  ┌──────────────────┐           ┌──────────────────┐       │
│  │   PostgreSQL     │           │      Redis       │       │
│  │   (Primary DB)   │           │    (Sessions)    │       │
│  │  - Users         │           │  - JWT tokens    │       │
│  │  - Inventory     │           │  - Cache         │       │
│  │  - Optimizations │           └──────────────────┘       │
│  │  - Results       │                                       │
│  └──────────────────┘                                       │
└─────────────────────────────────────────────────────────────┘
```

---

## Stack Tecnologico

### Frontend

| Componente | Tecnologia | Versione | Motivazione |
|------------|-----------|----------|-------------|
| Framework | React | 18.x | Virtual DOM, component-based, ecosystem |
| Language | TypeScript | 5.x | Type safety, better IDE support |
| Build Tool | Vite | 5.x | Fast HMR, modern build |
| State Mgmt | Zustand | 4.x | Lightweight, simple API |
| HTTP Client | Axios | 1.x | Interceptors, better error handling |
| Routing | React Router | 6.x | Standard per SPA React |
| Styling | TailwindCSS | 3.x | Utility-first, rapid development |
| Forms | React Hook Form | 7.x | Performance, validation |

### Backend

| Componente | Tecnologia | Versione | Motivazione |
|------------|-----------|----------|-------------|
| Framework | FastAPI | 0.100+ | Async, auto docs, performance |
| Language | Python | 3.11 | Team expertise, rich libraries |
| ORM | SQLAlchemy | 2.x | Mature, powerful, migrations |
| Validation | Pydantic | 2.x | Data validation, serialization |
| Auth | JWT | - | Stateless, scalable |
| Password | bcrypt | - | Industry standard hashing |
| Excel | openpyxl | 3.x | Full Excel support, formatting |
| Optimization | PuLP | 2.x | Linear programming solver |

### Infrastructure

| Componente | Tecnologia | Versione | Motivazione |
|------------|-----------|----------|-------------|
| Database | PostgreSQL | 15 | Relational, ACID, performance |
| Cache | Redis | 7.x | Fast in-memory, sessions |
| Web Server | Nginx | 1.25 | Reverse proxy, static files |
| Container | Docker | 24.x | Isolamento, portabilità |
| Orchestration | Docker Compose | 2.x | Multi-container management |

---

## Componenti Sistema

### 1. Frontend Application

#### Struttura Directory
```
frontend/src/
├── components/         # React components
│   ├── layout/            # Layout components (Navbar, Sidebar)
│   └── ui/                # Reusable UI (Button, Input, Modal)
├── pages/              # Page components (one per route)
│   ├── Login.tsx
│   ├── Dashboard.tsx
│   ├── Inventory.tsx
│   ├── Optimize.tsx
│   └── Results.tsx
├── hooks/              # Custom React hooks
│   ├── useAuth.ts
│   ├── useInventory.ts
│   └── useOptimization.ts
├── store/              # Zustand state stores
│   ├── auth.store.ts
│   └── ui.store.ts
├── api/                # API client functions
│   ├── auth.ts
│   ├── inventory.ts
│   └── optimize.ts
├── utils/              # Utility functions
│   ├── formatters.ts
│   ├── validators.ts
│   └── constants.ts
└── types/              # TypeScript type definitions
    └── api.ts
```

#### Key Features
- **Component Composition**: Atomic design pattern
- **State Management**: Zustand stores for global state
- **Routing**: Protected routes con auth guard
- **API Integration**: Axios con interceptors per auth
- **Error Handling**: Toast notifications per feedback utente
- **Responsive**: Mobile-first design con Tailwind

### 2. Backend Application

#### Struttura Directory
```
backend/
├── app/
│   ├── api/
│   │   ├── endpoints/
│   │   │   ├── auth.py         # Login, logout, refresh token
│   │   │   ├── inventory.py    # CRUD inventory, upload CSV
│   │   │   ├── optimize.py     # Request optimization
│   │   │   └── users.py        # User management (admin)
│   │   └── __init__.py
│   ├── core/
│   │   ├── inventory_service.py    # Business logic inventory
│   │   ├── optimizer_service.py    # Adapter to optimizer_core
│   │   ├── excel_export_service.py # Excel generation
│   │   └── security.py             # JWT, password hashing
│   ├── models/
│   │   └── models.py           # SQLAlchemy ORM models
│   ├── schemas/
│   │   └── schemas.py          # Pydantic validation schemas
│   ├── database.py             # DB connection, session
│   ├── config.py               # Configuration (env vars)
│   └── main.py                 # FastAPI app initialization
├── optimizer_core/         # Core algorithm (shared)
│   ├── optimizer.py
│   ├── inventory.py
│   ├── compatibility.py
│   └── excel_export.py
├── migrations/             # SQL migrations
│   ├── 001_initial_schema.sql
│   ├── 002_seed_admin_user.sql
│   └── ...
└── requirements.txt
```

#### Key Features
- **Layered Architecture**: Clear separation API → Service → Core
- **Dependency Injection**: FastAPI dependencies per auth, DB
- **Async/Await**: Async endpoints per performance
- **Validation**: Pydantic schemas per input/output
- **Error Handling**: Custom exceptions, HTTP error handlers
- **Logging**: Structured logging per debugging

### 3. Core Optimizer Engine

Il cuore algoritmico del sistema, riutilizzato dall'optimizer_v33.

#### Componenti Principali

**optimizer.py**
```python
class BlendOptimizer:
    """
    Motore principale ottimizzazione blend multi-criterio.

    Strategie:
    - Greedy: Massimizza score globale
    - BestPerformers: Usa solo top N lotti
    - Diversity: Massimizza varietà fornitori
    - QualityFirst: Priorità parametri qualità
    """
    def optimize(self, target_specs, strategies, num_solutions)
    def score_combination(self, lots, weights)
    def calculate_blend_properties(self, lots, quantities)
```

**inventory.py**
```python
class InventoryManager:
    """
    Gestione lotti inventario con gerarchia dati.

    Priorità:
    1. Dati reali (da lab notes)
    2. Dati stimati/calcolati
    3. Default valori specie
    """
    def load_lots_from_db(self, filters)
    def validate_compatibility(self, lot1, lot2)
    def check_availability(self, lot_id, required_kg)
```

**compatibility.py**
```python
class CompatibilityEngine:
    """
    Regole compatibilità blend.

    Controlli:
    - Specie compatibili (goose, duck, mix)
    - Colori compatibili (bianco, grigio)
    - Materiali compatibili (down, feather)
    - Standard Fill Power (EN vs US vs JIS vs CN)
    """
    def are_compatible(self, lot1, lot2) -> bool
    def get_compatibility_score(self, lots) -> float
```

**excel_export.py**
```python
class ExcelExporter:
    """
    Generazione report Excel formattati.

    Sheets:
    1. Mix Details: Composizione blend, costi, qualità
    2. Lot Details: Dettagli singoli lotti utilizzati
    3. Quality Metrics: Analisi parametri qualità

    Formattazione:
    - Colori per differenziare sezioni
    - Bold per header e totali
    - Bordi per tabelle
    - Formati numero (%, €, kg)
    """
    def generate_report(self, optimization_result)
    def format_worksheet(self, ws, data)
```

---

## Flussi Dati

### 1. Flusso Autenticazione

```
User                Frontend              Backend              Database
 │                     │                     │                     │
 │  1. Submit          │                     │                     │
 │    credentials      │                     │                     │
 ├────────────────────>│                     │                     │
 │                     │  2. POST            │                     │
 │                     │    /api/auth/login  │                     │
 │                     ├────────────────────>│                     │
 │                     │                     │  3. Verify user     │
 │                     │                     ├────────────────────>│
 │                     │                     │<────────────────────┤
 │                     │                     │  4. User data       │
 │                     │                     │                     │
 │                     │                     │  5. Generate JWT    │
 │                     │                     │     + refresh token │
 │                     │<────────────────────┤                     │
 │                     │  6. Return tokens   │                     │
 │  7. Store tokens    │                     │                     │
 │    in localStorage  │                     │                     │
 │<────────────────────┤                     │                     │
 │                     │                     │                     │
```

### 2. Flusso Upload Inventario

```
User           Frontend         Backend           Database        WMS CSV
 │                │                 │                  │              │
 │  1. Select     │                 │                  │              │
 │     CSV file   │                 │                  │              │
 ├───────────────>│                 │                  │              │
 │                │  2. Validate    │                  │              │
 │                │     format      │                  │              │
 │                │                 │                  │              │
 │                │  3. POST        │                  │              │
 │                │    /api/inv..   │                  │              │
 │                ├────────────────>│                  │              │
 │                │                 │  4. Parse CSV    │              │
 │                │                 │     validate     │              │
 │                │                 │     data         │              │
 │                │                 │                  │              │
 │                │                 │  5. Insert       │              │
 │                │                 │     lots         │              │
 │                │                 ├─────────────────>│              │
 │                │                 │<─────────────────┤              │
 │                │                 │  6. Confirm      │              │
 │                │                 │                  │              │
 │                │<────────────────┤                  │              │
 │<───────────────┤  7. Success     │                  │              │
 │  8. Show       │     response    │                  │              │
 │     toast      │                 │                  │              │
```

### 3. Flusso Ottimizzazione Blend

```
User        Frontend       Backend         Optimizer      Database     Excel
 │             │              │                │             │           │
 │ 1. Input    │              │                │             │           │
 │    target   │              │                │             │           │
 │    specs    │              │                │             │           │
 ├────────────>│              │                │             │           │
 │             │  2. POST     │                │             │           │
 │             │   /optimize  │                │             │           │
 │             ├─────────────>│                │             │           │
 │             │              │  3. Load       │             │           │
 │             │              │     inventory  │             │           │
 │             │              ├───────────────────────────>│           │
 │             │              │<───────────────────────────┤           │
 │             │              │  4. Lots data  │             │           │
 │             │              │                │             │           │
 │             │              │  5. Run        │             │           │
 │             │              │     optimization           │             │
 │             │              ├───────────────>│             │           │
 │             │              │                │             │           │
 │             │              │  6. Calculate  │             │           │
 │             │              │     combos     │             │           │
 │             │              │     score      │             │           │
 │             │              │     allocate   │             │           │
 │             │              │<───────────────┤             │           │
 │             │              │  7. Top N      │             │           │
 │             │              │     solutions  │             │           │
 │             │              │                │             │           │
 │             │              │  8. Save       │             │           │
 │             │              │     results    │             │           │
 │             │              ├─────────────────────────────>│           │
 │             │              │                │             │           │
 │             │              │  9. Generate   │             │           │
 │             │              │     Excel      │             │           │
 │             │              ├───────────────────────────────────────>│
 │             │              │<───────────────────────────────────────┤
 │             │              │  10. Excel     │             │           │
 │             │              │      file      │             │           │
 │             │<─────────────┤                │             │           │
 │<────────────┤  11. Return  │                │             │           │
 │  12. Show   │      results │                │             │           │
 │      + DL   │      + link  │                │             │           │
 │      Excel  │              │                │             │           │
```

---

## Database Schema

### Entity Relationship Diagram

```
┌─────────────────┐
│     users       │
├─────────────────┤
│ id (PK)         │─┐
│ username        │ │
│ email           │ │
│ password_hash   │ │
│ full_name       │ │
│ role            │ │
│ is_active       │ │
│ created_at      │ │
└─────────────────┘ │
                    │
                    │  ┌─────────────────────────┐
                    │  │   optimization_requests │
                    │  ├─────────────────────────┤
                    └──│ id (PK)                 │
                       │ user_id (FK)            │
                       │ target_dc               │
                       │ target_fp               │
                       │ target_fp_std           │
                       │ total_kg                │
                       │ num_solutions           │
                       │ status                  │
                       │ created_at              │
                       └─────────────────────────┘
                                 │
                                 │
                       ┌─────────▼─────────────┐
                       │  optimization_results │
                       ├───────────────────────┤
                       │ id (PK)               │
                       │ request_id (FK)       │
                       │ solution_rank         │
                       │ score                 │
                       │ total_cost            │
                       │ num_lots_used         │
                       │ blend_properties_json │
                       │ excel_file_path       │
                       │ created_at            │
                       └───────────────────────┘
                                 │
                                 │
                       ┌─────────▼─────────────┐
                       │   result_lot_details  │
                       ├───────────────────────┤
                       │ id (PK)               │
                       │ result_id (FK) ───────┘
                       │ inventory_lot_id (FK)─┐
                       │ quantity_kg           │ │
                       │ percentage            │ │
                       └───────────────────────┘ │
                                                 │
┌────────────────────────────────────────────────┘
│
│  ┌─────────────────────────┐
│  │     inventory_lots      │
│  ├─────────────────────────┤
└──│ id (PK)                 │
   │ lot_code                │
   │ product_code            │
   │ species                 │
   │ color                   │
   │ composition             │
   │ available_kg            │
   │ price_per_kg            │
   │ supplier                │
   │ location                │
   │ down_content            │
   │ fill_power              │
   │ fp_standard             │
   │ oxygen                  │
   │ cleanliness             │
   │ turbidity               │
   │ fat_content             │
   │ moisture                │
   │ residue                 │
   │ data_source             │
   │ has_real_data           │
   │ imported_at             │
   │ last_updated            │
   └─────────────────────────┘
```

### Tabelle Principali

#### users
```sql
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    full_name VARCHAR(100),
    role VARCHAR(20) NOT NULL CHECK (role IN ('admin', 'operator', 'viewer')),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT NOW()
);
```

#### inventory_lots
```sql
CREATE TABLE inventory_lots (
    id SERIAL PRIMARY KEY,
    lot_code VARCHAR(50) UNIQUE NOT NULL,
    product_code VARCHAR(100) NOT NULL,
    species VARCHAR(50) NOT NULL,
    color VARCHAR(50),
    composition VARCHAR(100),
    available_kg DECIMAL(10,2) NOT NULL,
    price_per_kg DECIMAL(10,2),
    supplier VARCHAR(200),
    location VARCHAR(200),

    -- Quality metrics
    down_content DECIMAL(5,2),           -- DC %
    fill_power DECIMAL(7,2),             -- FP cuin/oz
    fp_standard VARCHAR(10),             -- EN/US/JIS/CN
    oxygen DECIMAL(6,2),                 -- O2 mg/g
    cleanliness DECIMAL(6,2),            -- mm
    turbidity DECIMAL(6,2),              -- mm
    fat_content DECIMAL(5,2),            -- %
    moisture DECIMAL(5,2),               -- %
    residue DECIMAL(5,2),                -- %

    -- Metadata
    data_source VARCHAR(20) DEFAULT 'wms',  -- wms/lab/estimated
    has_real_data BOOLEAN DEFAULT FALSE,
    imported_at TIMESTAMP DEFAULT NOW(),
    last_updated TIMESTAMP DEFAULT NOW(),

    INDEX idx_species (species),
    INDEX idx_lot_code (lot_code),
    INDEX idx_product_code (product_code)
);
```

#### optimization_requests
```sql
CREATE TABLE optimization_requests (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),

    -- Target specifications
    target_dc DECIMAL(5,2),
    target_fp DECIMAL(7,2),
    target_fp_std VARCHAR(10),
    total_kg DECIMAL(10,2) NOT NULL,
    num_solutions INTEGER DEFAULT 3,

    -- Advanced filters (JSON)
    filters_json TEXT,

    -- Status
    status VARCHAR(20) DEFAULT 'pending',  -- pending/processing/completed/failed
    error_message TEXT,

    created_at TIMESTAMP DEFAULT NOW()
);
```

#### optimization_results
```sql
CREATE TABLE optimization_results (
    id SERIAL PRIMARY KEY,
    request_id INTEGER REFERENCES optimization_requests(id) ON DELETE CASCADE,

    -- Solution details
    solution_rank INTEGER NOT NULL,  -- 1 = best, 2 = second best, etc.
    score DECIMAL(10,4) NOT NULL,
    total_cost DECIMAL(12,2),
    num_lots_used INTEGER,

    -- Blend properties (JSON)
    blend_properties_json TEXT,  -- {dc, fp, oxygen, etc.}

    -- Export
    excel_file_path VARCHAR(500),

    created_at TIMESTAMP DEFAULT NOW(),

    INDEX idx_request_id (request_id),
    INDEX idx_rank (solution_rank)
);
```

#### result_lot_details
```sql
CREATE TABLE result_lot_details (
    id SERIAL PRIMARY KEY,
    result_id INTEGER REFERENCES optimization_results(id) ON DELETE CASCADE,
    inventory_lot_id INTEGER REFERENCES inventory_lots(id),

    quantity_kg DECIMAL(10,2) NOT NULL,
    percentage DECIMAL(5,2) NOT NULL,

    INDEX idx_result_id (result_id)
);
```

---

## API Design

### Principi REST

1. **Resource-based URLs**: `/api/resource/{id}`
2. **HTTP Verbs**: GET (read), POST (create), PUT (update), DELETE (delete)
3. **Stateless**: Ogni request contiene tutte le info necessarie (JWT)
4. **JSON**: Formato standard request/response
5. **HTTP Status Codes**: 200 (OK), 201 (Created), 400 (Bad Request), 401 (Unauthorized), 404 (Not Found), 500 (Server Error)

### Endpoints Overview

#### Authentication
```
POST   /api/auth/login           # Login (returns access + refresh token)
POST   /api/auth/logout          # Logout (invalidate tokens)
POST   /api/auth/refresh         # Refresh access token
GET    /api/auth/me              # Get current user info
```

#### Inventory
```
GET    /api/inventory/lots               # List all lots (with filters)
GET    /api/inventory/lots/{id}          # Get single lot details
POST   /api/inventory/upload             # Upload CSV (multipart/form-data)
DELETE /api/inventory/lots/{id}          # Delete lot (admin only)
GET    /api/inventory/stats              # Get inventory statistics
```

#### Optimization
```
POST   /api/optimize/blend               # Request blend optimization
GET    /api/optimize/requests            # List user's requests
GET    /api/optimize/requests/{id}       # Get request details + results
GET    /api/optimize/results/{id}/excel  # Download Excel report
```

#### Users (Admin only)
```
GET    /api/users                # List all users
POST   /api/users                # Create new user
GET    /api/users/{id}           # Get user details
PUT    /api/users/{id}           # Update user
DELETE /api/users/{id}           # Delete user
```

### Request/Response Examples

**POST /api/auth/login**
```json
Request:
POST /api/auth/login
Content-Type: application/x-www-form-urlencoded

username=admin&password=changeme123

Response: 200 OK
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 3600
}
```

**POST /api/optimize/blend**
```json
Request:
POST /api/optimize/blend
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
Content-Type: application/json

{
  "target_dc": 82.0,
  "target_fp": 700.0,
  "target_fp_std": "EN",
  "total_kg": 100.0,
  "num_solutions": 3,
  "filters": {
    "species": ["goose"],
    "min_cleanliness": 800
  }
}

Response: 201 Created
{
  "request_id": 42,
  "status": "processing",
  "estimated_time_seconds": 15,
  "message": "Optimization started"
}
```

**GET /api/optimize/requests/42**
```json
Response: 200 OK
{
  "id": 42,
  "user_id": 1,
  "target_dc": 82.0,
  "target_fp": 700.0,
  "total_kg": 100.0,
  "status": "completed",
  "created_at": "2025-01-10T14:30:00Z",
  "results": [
    {
      "id": 101,
      "solution_rank": 1,
      "score": 0.9234,
      "total_cost": 1850.50,
      "num_lots_used": 3,
      "blend_properties": {
        "dc": 82.1,
        "fp": 702.5,
        "oxygen": 4.8,
        "cleanliness": 900.2
      },
      "excel_download_url": "/api/optimize/results/101/excel"
    },
    {
      "id": 102,
      "solution_rank": 2,
      "score": 0.9145,
      "total_cost": 1820.30,
      ...
    }
  ]
}
```

---

## Sicurezza

### Autenticazione e Autorizzazione

**JWT (JSON Web Tokens)**
- **Access Token**: Durata 1 ora, usato per API calls
- **Refresh Token**: Durata 7 giorni, usato per rinnovare access token
- Payload: `{user_id, username, role, exp}`

**Role-Based Access Control (RBAC)**
```python
Roles:
- admin: Tutte le operazioni
- operator: Upload CSV, richiesta blend, download Excel
- viewer: Solo lettura inventario e risultati

Permissions Matrix:
                    │ viewer │ operator │ admin │
────────────────────┼────────┼──────────┼───────┤
View inventory      │   ✓    │    ✓     │   ✓   │
Upload CSV          │   ✗    │    ✓     │   ✓   │
Request blend       │   ✗    │    ✓     │   ✓   │
Download Excel      │   ✗    │    ✓     │   ✓   │
Manage users        │   ✗    │    ✗     │   ✓   │
Delete inventory    │   ✗    │    ✗     │   ✓   │
```

### Input Validation

1. **Pydantic Schemas**: Validazione automatica tipi e range
2. **Custom Validators**: Business logic validation
3. **SQL Injection**: Prevenuto da SQLAlchemy ORM (parametrized queries)
4. **XSS**: Frontend sanitizza input, backend valida

```python
# Example Pydantic Schema
class OptimizeRequest(BaseModel):
    target_dc: confloat(ge=0, le=100)  # 0-100%
    target_fp: confloat(ge=300, le=1000)  # 300-1000 cuin/oz
    total_kg: confloat(gt=0, le=10000)  # > 0, max 10 ton
    num_solutions: conint(ge=1, le=10)  # 1-10 solutions
```

### CORS (Cross-Origin Resource Sharing)

```python
# Configurato per intranet aziendale
CORS_ORIGINS = [
    "http://localhost:3000",  # Dev frontend
    "http://192.168.1.0/24",  # Rete aziendale
]
```

### Secrets Management

- **Environment Variables**: Tutti i secrets in `.env` (non committato)
- **Docker Secrets**: Per production deployment
- **Hashing**: bcrypt per password (cost factor 12)

```bash
# .env file (esempio)
SECRET_KEY=<generato-con-openssl-rand-base64-32>
POSTGRES_PASSWORD=<strong-password>
REDIS_PASSWORD=<strong-password>
```

---

## Deploy e Infrastructure

### Docker Compose Architecture

```yaml
services:
  frontend:
    build: ./frontend
    ports: ["3000:80"]
    depends_on: [backend]

  backend:
    build: ./backend
    ports: ["8000:8000"]
    depends_on: [db, redis]
    volumes:
      - ./backend:/app
      - optimizer_core:/app/optimizer_core:ro
    environment:
      - DATABASE_URL=postgresql://...
      - REDIS_URL=redis://...

  db:
    image: postgres:15
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./backend/migrations:/docker-entrypoint-initdb.d
    environment:
      - POSTGRES_DB=blend_optimizer
      - POSTGRES_USER=optimizer
      - POSTGRES_PASSWORD=${POSTGRES_PASSWORD}

  redis:
    image: redis:7-alpine
    volumes:
      - redis_data:/data
    command: redis-server --appendonly yes

volumes:
  postgres_data:
  redis_data:
  optimizer_core:
    driver: local
    driver_opts:
      type: none
      device: /path/to/optimizer_v33
      o: bind
```

### Deployment Strategy

**Sviluppo**
```bash
docker-compose up -d
# Hot reload: frontend (Vite HMR), backend (uvicorn --reload)
```

**Production**
```bash
docker-compose -f docker-compose.prod.yml up -d
# Multi-stage builds per ottimizzazione immagini
# Nginx per servire frontend statico + reverse proxy backend
# Gunicorn + Uvicorn workers per backend
```

### Monitoring e Logging

- **Health Checks**: `/health` endpoint con status DB, Redis
- **Structured Logging**: JSON logs con timestamp, level, context
- **Error Tracking**: Sentry integration (futuro)
- **Metrics**: Prometheus + Grafana (futuro)

---

## Performance e Scalabilità

### Ottimizzazioni Attuali

1. **Database**
   - Indici su colonne filtrate spesso (species, lot_code)
   - Connection pooling (10 connessioni)
   - Query ottimizzate con `select_from`, `join`

2. **Backend**
   - Async endpoints per I/O bound operations
   - Redis caching per sessioni utente
   - Lazy loading dati pesanti

3. **Frontend**
   - Code splitting per route
   - Lazy loading componenti
   - Debouncing input search
   - Virtual scrolling per liste lunghe

### Bottleneck Potenziali

1. **Ottimizzazione Blend**: O(n!) con n = numero lotti
   - Mitigazione: Filtri pre-ottimizzazione, max combinazioni

2. **Export Excel**: Generazione sincrona blocca thread
   - Mitigazione futura: Background task con Celery

3. **Upload CSV Grande**: >10MB può essere lento
   - Mitigazione futura: Streaming parser, chunk upload

### Scalabilità Futura

**Orizzontale (Scale Out)**
- Load balancer Nginx con multiple backend instances
- Read replicas PostgreSQL
- Redis Cluster per cache distribuita

**Verticale (Scale Up)**
- Aumentare CPU/RAM container backend
- Database su SSD per query più veloci

---

## Decisioni Architetturali

### ADR (Architecture Decision Records)

#### ADR-001: Riuso Optimizer Core

**Context**: Esiste già optimizer_v33 con algoritmo funzionante.

**Decision**: Riutilizzare 80%+ codice tramite volume mount Docker invece di riscrivere.

**Consequences**:
- ✅ Risparmio tempo sviluppo
- ✅ Algoritmo già testato e validato
- ✅ Facile aggiornamento condiviso
- ⚠️ Accoppiamento tra progetti

#### ADR-002: FastAPI vs Flask/Django

**Context**: Scegliere framework backend Python.

**Decision**: FastAPI per async support, auto-docs, performance.

**Consequences**:
- ✅ Async endpoints = better concurrency
- ✅ Swagger/ReDoc auto-generati
- ✅ Validazione Pydantic integrata
- ⚠️ Curva apprendimento async/await

#### ADR-003: React vs Vue vs Angular

**Context**: Scegliere framework frontend.

**Decision**: React per ecosystem, community, team expertise.

**Consequences**:
- ✅ Librerie mature (React Router, Zustand)
- ✅ TypeScript support first-class
- ✅ Component reusability
- ⚠️ Più boilerplate di Vue

#### ADR-004: PostgreSQL vs MongoDB

**Context**: Scegliere database.

**Decision**: PostgreSQL per dati strutturati, transazioni ACID.

**Consequences**:
- ✅ Schema ben definito
- ✅ JOIN efficienti per report
- ✅ ACID per consistency
- ⚠️ Meno flessibile schema changes

#### ADR-005: Monolith vs Microservices

**Context**: Architettura deployment.

**Decision**: Monolith modulare per MVP, considerare microservices se scaling necessario.

**Consequences**:
- ✅ Deploy più semplice
- ✅ Debugging più facile
- ✅ Meno overhead rete
- ⚠️ Scaling granulare limitato

---

## Prossimi Step Architetturali

### Breve Termine (1-3 mesi)

1. **Background Processing**
   - Celery + RabbitMQ per ottimizzazioni lunghe
   - Progress bar real-time via WebSocket

2. **Caching Avanzato**
   - Cache risultati ottimizzazione con TTL
   - Invalidazione cache intelligente

3. **Testing**
   - Unit tests (pytest)
   - Integration tests
   - E2E tests (Playwright)

### Medio Termine (3-6 mesi)

1. **Analytics Dashboard**
   - Metriche utilizzo sistema
   - Report automatici settimanali
   - Grafici trend qualità blend

2. **Notifications**
   - Email quando ottimizzazione completa
   - Alert admin per inventory basso

3. **Multi-tenancy**
   - Supporto multiple aziende/stabilimenti
   - Isolamento dati

### Lungo Termine (6-12 mesi)

1. **Machine Learning**
   - Predizione qualità blend basata su storico
   - Suggerimenti automatici parametri target

2. **Mobile App**
   - React Native app per consultazione mobile

3. **API Pubblica**
   - REST API per integrazioni esterne
   - Webhook per eventi

---

## Riferimenti

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [React Documentation](https://react.dev/)
- [PostgreSQL Documentation](https://www.postgresql.org/docs/)
- [Docker Documentation](https://docs.docker.com/)
- [SQLAlchemy Documentation](https://docs.sqlalchemy.org/)

---

**Ultimo Aggiornamento**: 2025-01-10
**Versione**: 1.0
**Autore**: Team IT Interno
