# Quick Start Guide

Avvio rapido del sistema Blend Optimizer in 5 minuti.

## Prerequisiti

- Docker e Docker Compose installati
- File `.env` configurato

## Avvio Rapido

### 1. Setup Iniziale (Prima Volta)

```bash
# Vai nella directory del progetto
cd /Users/carlocassigoli/CODE-progetti-Claude/Claude/WEP_APPS/blend-optimizer-web

# Copia configurazione
cp .env.example .env

# IMPORTANTE: Modifica .env e cambia:
# - POSTGRES_PASSWORD
# - SECRET_KEY (genera con: openssl rand -base64 32)
nano .env
```

### 2. Avvia i Servizi

```bash
# Avvia tutto
docker-compose up -d

# Verifica che i servizi siano attivi
docker-compose ps

# Attendi 10-20 secondi per l'inizializzazione del database
# Verifica logs
docker-compose logs -f backend
```

### 3. Test Rapido

```bash
# Test health
curl http://localhost:8000/health

# Dovrebbe rispondere:
# {"status":"healthy","version":"1.0.0"}
```

### 4. Login e Test API

```bash
# Login (ottieni token)
curl -X POST "http://localhost:8000/api/auth/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin&password=changeme123"

# Salva il token
export TOKEN="<il-token-ricevuto>"

# Test autenticazione
curl -X GET "http://localhost:8000/api/auth/me" \
  -H "Authorization: Bearer $TOKEN"
```

### 5. Upload Inventario di Test

```bash
# Vai nella directory scripts
cd scripts

# Upload CSV di test
curl -X POST "http://localhost:8000/api/inventory/upload" \
  -H "Authorization: Bearer $TOKEN" \
  -F "file=@test_inventory.csv" \
  -F "notes=Test upload iniziale"

# Verifica inventario
curl -X GET "http://localhost:8000/api/inventory/stats" \
  -H "Authorization: Bearer $TOKEN"
```

### 6. Richiedi Ottimizzazione

```bash
# Richiedi miscela ottimizzata
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

# Salva request_id dalla risposta
export REQUEST_ID="<request-id-dalla-risposta>"

# Scarica Excel
curl -X GET "http://localhost:8000/api/optimize/$REQUEST_ID/excel" \
  -H "Authorization: Bearer $TOKEN" \
  -o risultato.xlsx
```

## Script Test Automatico

```bash
# Rendi eseguibile lo script
chmod +x scripts/test_api.sh

# Esegui tutti i test
cd scripts
./test_api.sh
```

## Accesso API Documentation

Apri nel browser:

- **API Docs (Swagger)**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## Credenziali Default

⚠️ **CAMBIARE DOPO PRIMO ACCESSO!**

- **Username**: `admin`
- **Password**: `changeme123`
- **Ruolo**: admin

## Comandi Utili

```bash
# Ferma servizi
docker-compose down

# Riavvia
docker-compose restart

# Logs in tempo reale
docker-compose logs -f

# Solo logs backend
docker-compose logs -f backend

# Accedi al database
docker-compose exec db psql -U optimizer -d blend_optimizer
```

## Troubleshooting Rapido

### Backend non risponde

```bash
# Verifica logs
docker-compose logs backend

# Riavvia backend
docker-compose restart backend
```

### Database non pronto

```bash
# Verifica che il DB sia healthy
docker-compose ps

# Attendi fino a vedere "healthy" per db
# Se necessario, riavvia
docker-compose restart db
docker-compose restart backend
```

### Reset completo (cancella dati!)

```bash
docker-compose down
docker volume rm blend_optimizer_postgres_data
docker-compose up -d
```

## Struttura API

### Autenticazione
- `POST /api/auth/login` - Login (ottieni token)
- `GET /api/auth/me` - Info utente corrente

### Inventario
- `POST /api/inventory/upload` - Upload CSV (admin)
- `GET /api/inventory/lots` - Lista lotti
- `GET /api/inventory/stats` - Statistiche

### Ottimizzazione
- `POST /api/optimize/blend` - Richiedi ottimizzazione
- `GET /api/optimize/{id}/results` - Risultati
- `GET /api/optimize/{id}/excel` - Download Excel

### Utenti (Admin)
- `GET /api/users/` - Lista utenti
- `POST /api/users/` - Crea utente
- `PATCH /api/users/{id}` - Aggiorna utente

## Prossimi Step

1. ✅ Backend funzionante
2. Carica il tuo CSV inventario reale
3. Testa ottimizzazioni con requisiti reali
4. Completa frontend web
5. Deploy produzione

## Documentazione Completa

Per istruzioni dettagliate, vedi:

- [Deployment Guide](./DEPLOYMENT.md) - Guida completa deployment
- [API Documentation](http://localhost:8000/docs) - Swagger UI
- [README](../README.md) - Panoramica progetto

## Supporto

In caso di problemi:

1. Controlla [DEPLOYMENT.md](./DEPLOYMENT.md) sezione Troubleshooting
2. Verifica logs: `docker-compose logs -f`
3. Reset servizi: `docker-compose restart`
