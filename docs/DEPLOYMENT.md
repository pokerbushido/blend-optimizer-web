# Deployment Guide - Blend Optimizer Web App

Guida completa per il deployment e testing del sistema.

## Indice

1. [Prerequisiti](#prerequisiti)
2. [Setup Iniziale](#setup-iniziale)
3. [Avvio Servizi Sviluppo](#avvio-servizi-sviluppo)
4. [Testing Backend](#testing-backend)
5. [Deploy Produzione](#deploy-produzione)
6. [Troubleshooting](#troubleshooting)
7. [Backup e Manutenzione](#backup-e-manutenzione)

---

## Prerequisiti

### Software Richiesto

- **Docker**: versione 20.10 o superiore
- **Docker Compose**: versione 2.0 o superiore
- **Git**: per clonare il repository

### Verifica Prerequisiti

```bash
# Verifica Docker
docker --version
# Output atteso: Docker version 20.10.x o superiore

# Verifica Docker Compose
docker-compose --version
# Output atteso: Docker Compose version 2.x.x o superiore

# Verifica che Docker sia in esecuzione
docker ps
# Se funziona, Docker è attivo
```

### Requisiti Hardware (Minimo)

- **CPU**: 2 cores
- **RAM**: 4 GB
- **Storage**: 20 GB liberi
- **Network**: Connessione intranet

---

## Setup Iniziale

### 1. Clona/Posiziona il Progetto

```bash
cd /Users/carlocassigoli/CODE-progetti-Claude/Claude/WEP_APPS/blend-optimizer-web
```

### 2. Configurazione Ambiente

```bash
# Copia il template delle variabili d'ambiente
cp .env.example .env

# Modifica .env con le tue configurazioni
nano .env  # oppure usa il tuo editor preferito
```

**IMPORTANTE**: Modifica questi valori nel file `.env`:

```bash
# Database - CAMBIA LA PASSWORD!
POSTGRES_PASSWORD=TuaPasswordSicura123!

# Backend - GENERA UN SECRET KEY CASUALE!
SECRET_KEY=genera_una_stringa_casuale_di_almeno_32_caratteri

# Admin User - CAMBIA LA PASSWORD!
ADMIN_PASSWORD=changeme123  # Cambiare dopo primo login
```

#### Generare un SECRET_KEY sicuro:

```bash
# Metodo 1: Python
python3 -c "import secrets; print(secrets.token_urlsafe(32))"

# Metodo 2: OpenSSL
openssl rand -base64 32
```

### 3. Verifica Struttura Cartelle

```bash
ls -la
# Dovresti vedere:
# - backend/
# - frontend/
# - docker-compose.yml
# - .env
# - README.md
```

---

## Avvio Servizi Sviluppo

### Avvio Completo

```bash
# Avvia tutti i servizi in background
docker-compose up -d

# Verifica che i container siano in esecuzione
docker-compose ps

# Output atteso:
# NAME                          STATUS              PORTS
# blend_optimizer_db            Up (healthy)        0.0.0.0:5432->5432/tcp
# blend_optimizer_redis         Up (healthy)        0.0.0.0:6379->6379/tcp
# blend_optimizer_backend       Up                  0.0.0.0:8000->8000/tcp
```

### Verifica Logs

```bash
# Logs di tutti i servizi
docker-compose logs -f

# Logs solo backend
docker-compose logs -f backend

# Logs solo database
docker-compose logs -f db
```

### Inizializzazione Database

Il database viene inizializzato automaticamente tramite i file in `backend/migrations/`:
- `001_initial_schema.sql` - Schema tabelle
- `002_seed_admin_user.sql` - Utente admin di default

**Verifica che le migration siano state eseguite:**

```bash
# Accedi al container PostgreSQL
docker-compose exec db psql -U optimizer -d blend_optimizer

# Verifica tabelle create
\dt

# Output atteso:
#  Schema |       Name        | Type  |  Owner
# --------+-------------------+-------+-----------
#  public | inventory_lots    | table | optimizer
#  public | inventory_uploads | table | optimizer
#  public | users             | table | optimizer

# Verifica utente admin creato
SELECT username, role, is_active FROM users;

# Output atteso:
#  username | role  | is_active
# ----------+-------+-----------
#  admin    | admin | t

# Esci da psql
\q
```

### Test Health Check

```bash
# Test endpoint health
curl http://localhost:8000/health

# Output atteso:
# {"status":"healthy","version":"1.0.0"}
```

---

## Testing Backend

### 1. Test Autenticazione

#### Login Admin (curl)

```bash
# Login con form data (OAuth2)
curl -X POST "http://localhost:8000/api/auth/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin&password=changeme123"

# Output atteso:
# {
#   "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
#   "token_type": "bearer"
# }
```

**SALVA IL TOKEN** - lo userai per le richieste successive:

```bash
# Salva il token in una variabile (bash)
export TOKEN="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."

# Oppure crea un file
echo "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..." > token.txt
```

#### Verifica Utente Corrente

```bash
# Usando la variabile TOKEN
curl -X GET "http://localhost:8000/api/auth/me" \
  -H "Authorization: Bearer $TOKEN"

# Output atteso:
# {
#   "username": "admin",
#   "email": "admin@company.local",
#   "role": "admin",
#   "is_active": true,
#   ...
# }
```

### 2. Test Upload Inventario CSV

#### Prepara un CSV di Test

Crea un file `test_inventory.csv`:

```csv
SCO_ART,SCO_LOTT,SCO_DESC,SCO_DownCluster_Real,SCO_FillPower_Real,SCO_Duck,SCO_OE,SCO_Feather,SCO_Oxygen,SCO_Turbidity,SCO_DownCluster_Nominal,SCO_FillPower_Nominal,SCO_TotalFibres,SCO_Broken,SCO_Landfowl,SCO_QTA,SCO_COSTO_KG,SCO_QUALITA,SCO_NOTE_LAB
3|POB,TEST001,Piumino Oca Bianco,85.5,720,0,2.1,12.4,7.5,18.2,85,720,1.2,0.8,0.5,150,45.50,DC85 FP720,Note laboratorio
3|PAB,TEST002,Piumino Anatra Bianco,78.2,650,100,3.5,18.3,9.1,22.5,78,650,1.8,1.2,0.7,200,32.00,DC78 FP650,
3|POAB,TEST003,Piumino Oca/Anatra Bianco,81.0,680,45,2.8,16.2,8.3,20.1,81,680,1.5,1.0,0.6,180,38.75,DC81 FP680,
```

#### Upload via API

```bash
# Upload CSV
curl -X POST "http://localhost:8000/api/inventory/upload" \
  -H "Authorization: Bearer $TOKEN" \
  -F "file=@test_inventory.csv" \
  -F "notes=Test upload iniziale"

# Output atteso:
# {
#   "id": "uuid-here",
#   "uploaded_by": "uuid-user",
#   "filename": "test_inventory.csv",
#   "total_lots": 3,
#   "status": "completed",
#   ...
# }
```

### 3. Test Inventario

#### Lista Lotti

```bash
# Ottieni lista lotti
curl -X GET "http://localhost:8000/api/inventory/lots?limit=10" \
  -H "Authorization: Bearer $TOKEN"

# Con filtri
curl -X GET "http://localhost:8000/api/inventory/lots?species=O&min_dc=80" \
  -H "Authorization: Bearer $TOKEN"
```

#### Statistiche Inventario

```bash
curl -X GET "http://localhost:8000/api/inventory/stats" \
  -H "Authorization: Bearer $TOKEN"

# Output atteso:
# {
#   "total_lots": 3,
#   "total_kg": 530.0,
#   "avg_dc": 81.57,
#   "avg_fp": 683.33,
#   "by_species": {
#     "O": {"count": 1, "total_kg": 150.0},
#     "A": {"count": 1, "total_kg": 200.0},
#     "OA": {"count": 1, "total_kg": 180.0}
#   }
# }
```

### 4. Test Ottimizzazione

#### Richiesta Ottimizzazione

```bash
# Richiedi ottimizzazione miscela
curl -X POST "http://localhost:8000/api/optimize/blend" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "target_dc": 82.0,
    "target_fp": 700.0,
    "target_duck": 20.0,
    "species": "O",
    "total_kg": 100.0,
    "num_solutions": 3,
    "exclude_raw_materials": true
  }'

# Output atteso:
# {
#   "request_id": "uuid-request",
#   "requirements": {...},
#   "solutions": [
#     {
#       "solution_number": 1,
#       "lots": [...],
#       "total_kg": 100.0,
#       "avg_dc": 82.15,
#       "avg_fp": 698.5,
#       "dc_compliance": true,
#       "fp_compliance": true,
#       "score": 8523.45
#     },
#     ...
#   ],
#   "computation_time_seconds": 1.23
# }
```

**SALVA IL request_id** per scaricare l'Excel:

```bash
export REQUEST_ID="uuid-from-response"
```

#### Download Excel

```bash
# Download file Excel
curl -X GET "http://localhost:8000/api/optimize/$REQUEST_ID/excel" \
  -H "Authorization: Bearer $TOKEN" \
  -o risultato_ottimizzazione.xlsx

# Verifica che il file sia stato scaricato
ls -lh risultato_ottimizzazione.xlsx
```

### 5. Test Gestione Utenti (Admin)

#### Crea Nuovo Utente

```bash
curl -X POST "http://localhost:8000/api/users/" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "operatore1",
    "email": "operatore1@company.local",
    "password": "password123",
    "full_name": "Operatore Test",
    "role": "operatore"
  }'
```

#### Lista Utenti

```bash
curl -X GET "http://localhost:8000/api/users/" \
  -H "Authorization: Bearer $TOKEN"
```

---

## Script di Test Automatico

Crea un file `test_api.sh` per testare tutte le API:

```bash
#!/bin/bash

# Script di test completo API backend
# Usage: ./test_api.sh

set -e

API_URL="http://localhost:8000"
echo "🧪 Testing Blend Optimizer API at $API_URL"

# 1. Health Check
echo "
📊 1. Health Check"
curl -s "$API_URL/health" | jq

# 2. Login
echo "
🔐 2. Login Admin"
TOKEN=$(curl -s -X POST "$API_URL/api/auth/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin&password=changeme123" | jq -r .access_token)

echo "Token: ${TOKEN:0:50}..."

# 3. Get Current User
echo "
👤 3. Get Current User"
curl -s -X GET "$API_URL/api/auth/me" \
  -H "Authorization: Bearer $TOKEN" | jq

# 4. Inventory Stats
echo "
📦 4. Inventory Stats"
curl -s -X GET "$API_URL/api/inventory/stats" \
  -H "Authorization: Bearer $TOKEN" | jq

# 5. List Lots
echo "
📋 5. List Inventory Lots (first 5)"
curl -s -X GET "$API_URL/api/inventory/lots?limit=5" \
  -H "Authorization: Bearer $TOKEN" | jq

echo "
✅ All tests completed successfully!"
```

Rendilo eseguibile e lancialo:

```bash
chmod +x test_api.sh
./test_api.sh
```

---

## Deploy Produzione

### Configurazione Produzione

1. **Copia e modifica variabili d'ambiente**:

```bash
cp .env.example .env.prod

# Modifica .env.prod con valori di produzione
# IMPORTANTE:
# - Password database sicure
# - SECRET_KEY univoco e complesso
# - CORS origins appropriati
# - LOG_LEVEL=WARNING
```

2. **Avvio in modalità produzione**:

```bash
# Usa il compose file di produzione
docker-compose -f docker-compose.prod.yml up -d

# Verifica servizi
docker-compose -f docker-compose.prod.yml ps

# Verifica logs
docker-compose -f docker-compose.prod.yml logs -f
```

### Configurazione Nginx Reverse Proxy (Opzionale)

Crea `docker/nginx/nginx.conf`:

```nginx
events {
    worker_connections 1024;
}

http {
    upstream backend {
        server backend:8000;
    }

    upstream frontend {
        server frontend:80;
    }

    server {
        listen 80;
        server_name your-domain.local;

        # Frontend
        location / {
            proxy_pass http://frontend;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
        }

        # Backend API
        location /api {
            proxy_pass http://backend;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
        }

        # API Docs
        location /docs {
            proxy_pass http://backend;
        }
    }
}
```

---

## Troubleshooting

### Il backend non si avvia

```bash
# Verifica logs dettagliati
docker-compose logs backend

# Errori comuni:
# 1. Database non raggiungibile
#    → Verifica che il container db sia healthy: docker-compose ps
#    → Attendi che il database sia pronto (può richiedere 10-30 secondi)

# 2. Variabili d'ambiente mancanti
#    → Verifica .env: cat .env
#    → Riavvia: docker-compose restart backend

# 3. Porta 8000 già in uso
#    → Verifica: lsof -i :8000
#    → Cambia porta in docker-compose.yml
```

### Errore "Could not validate credentials"

```bash
# 1. Verifica che il token non sia scaduto
#    I token durano 8 ore per default

# 2. Verifica che SECRET_KEY non sia cambiata
#    Se cambi SECRET_KEY, devi rifare login

# 3. Rigenera il token
curl -X POST "http://localhost:8000/api/auth/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin&password=changeme123"
```

### Errore upload CSV

```bash
# 1. Verifica formato CSV
#    - Encoding UTF-8 o Latin-1
#    - Separatore: virgola
#    - Colonne richieste: SCO_ART, SCO_LOTT, SCO_QTA minimo

# 2. Verifica dimensione file
#    MAX_UPLOAD_SIZE_MB = 50 (default)

# 3. Verifica ruolo utente
#    Solo admin può caricare CSV
```

### Database: reset completo

```bash
# ⚠️ ATTENZIONE: Cancella tutti i dati!

# Stop servizi
docker-compose down

# Rimuovi volume database
docker volume rm blend_optimizer_postgres_data

# Riavvia
docker-compose up -d

# Il database verrà ricreato con le migration
```

### Visualizza query SQL in esecuzione

```bash
# Accedi a PostgreSQL
docker-compose exec db psql -U optimizer -d blend_optimizer

# Visualizza connessioni attive
SELECT pid, usename, application_name, client_addr, state, query
FROM pg_stat_activity
WHERE datname = 'blend_optimizer';

# Dimensione database
SELECT pg_size_pretty(pg_database_size('blend_optimizer'));

# Dimensione tabelle
SELECT schemaname, tablename,
       pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS size
FROM pg_tables
WHERE schemaname = 'public'
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;
```

---

## Backup e Manutenzione

### Backup Database

```bash
# Backup manuale
docker-compose exec db pg_dump -U optimizer blend_optimizer > backup_$(date +%Y%m%d).sql

# Restore da backup
cat backup_20250104.sql | docker-compose exec -T db psql -U optimizer blend_optimizer
```

### Script Backup Automatico

Crea `scripts/backup.sh`:

```bash
#!/bin/bash

BACKUP_DIR="/path/to/backups"
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="$BACKUP_DIR/blend_optimizer_$DATE.sql"

# Backup database
docker-compose exec -T db pg_dump -U optimizer blend_optimizer > "$BACKUP_FILE"

# Comprimi
gzip "$BACKUP_FILE"

# Mantieni solo ultimi 30 giorni
find "$BACKUP_DIR" -name "*.sql.gz" -mtime +30 -delete

echo "Backup completato: ${BACKUP_FILE}.gz"
```

### Monitoraggio

```bash
# Verifica salute container
docker-compose ps

# Uso risorse
docker stats

# Spazio disco
docker system df
```

---

## Prossimi Step

1. ✅ Backend funzionante
2. ⏭️ Completare frontend React
3. ⏭️ Testing end-to-end
4. ⏭️ Deploy on-premise finale

Per domande o problemi, consulta:
- [README.md](../README.md)
- [ARCHITECTURE.md](./ARCHITECTURE.md)
- API Docs: http://localhost:8000/docs
