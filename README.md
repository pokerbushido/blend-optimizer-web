# Blend Optimizer Web Application

Sistema web per l'ottimizzazione di miscele di piumino, accessibile via intranet aziendale.

## 🚀 Quick Start

**Per testare subito il backend**:

```bash
# 1. Setup
cd /Users/carlocassigoli/CODE-progetti-Claude/Claude/WEP_APPS/blend-optimizer-web
cp .env.example .env

# 2. Modifica .env (IMPORTANTE!)
# - Cambia POSTGRES_PASSWORD
# - Genera SECRET_KEY: openssl rand -base64 32

# 3. Avvia
docker-compose up -d

# 4. Test automatico
cd scripts
chmod +x test_api.sh
./test_api.sh
```

📖 **Guide Dettagliate**:
- [Quick Start Guide](docs/QUICKSTART.md) - Avvio in 5 minuti
- [Deployment Guide](docs/DEPLOYMENT.md) - Guida completa con troubleshooting
- [API Documentation](docs/API.md) - Documentazione completa API

## Architettura

```
blend-optimizer-web/
├── backend/          # FastAPI + PostgreSQL
│   ├── app/
│   │   ├── api/         # REST endpoints
│   │   ├── core/        # Business logic + optimizer adapter
│   │   ├── models/      # SQLAlchemy models
│   │   └── schemas/     # Pydantic schemas
│   ├── migrations/      # SQL schema + seed data
│   └── requirements.txt
├── frontend/         # React + TypeScript (in sviluppo)
├── scripts/          # Test e utility
│   ├── test_api.sh       # Script test completo
│   └── test_inventory.csv # CSV di esempio
├── docs/             # Documentazione
│   ├── QUICKSTART.md
│   ├── DEPLOYMENT.md
│   └── API.md
└── docker-compose.yml
```

## Tecnologie

- **Backend**: FastAPI, SQLAlchemy, PostgreSQL
- **Frontend**: React 18, TypeScript, TailwindCSS (in sviluppo)
- **Database**: PostgreSQL 15
- **Cache**: Redis
- **Deploy**: Docker Compose
- **Core Algorithm**: Riutilizza optimizer_v33 (80%+ codice condiviso)

## Stato Sviluppo

✅ **Completato**:
- Backend FastAPI completo
- Autenticazione JWT + ruoli (admin/operatore/visualizzatore)
- API upload CSV → PostgreSQL
- API ottimizzazione miscele
- API export Excel
- Database schema + migrations
- Docker Compose sviluppo e produzione
- Documentazione completa
- Script di test

🚧 **In Sviluppo**:
- Frontend React (login, dashboard, forms)

## Testing Backend

### Test Automatico

```bash
cd scripts
./test_api.sh
```

### Test Manuale

```bash
# Health check
curl http://localhost:8000/health

# Login
curl -X POST "http://localhost:8000/api/auth/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin&password=changeme123"

# Salva token
export TOKEN="<token-ricevuto>"

# Upload CSV
curl -X POST "http://localhost:8000/api/inventory/upload" \
  -H "Authorization: Bearer $TOKEN" \
  -F "file=@scripts/test_inventory.csv"

# Richiedi ottimizzazione
curl -X POST "http://localhost:8000/api/optimize/blend" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"target_dc": 82.0, "target_fp": 700.0, "total_kg": 100.0, "num_solutions": 3}'
```

Vedi [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md) per test completi.

## Accesso Servizi

| Servizio | URL | Descrizione |
|----------|-----|-------------|
| Backend API | http://localhost:8000 | REST API |
| API Docs (Swagger) | http://localhost:8000/docs | Documentazione interattiva |
| ReDoc | http://localhost:8000/redoc | Documentazione alternativa |
| PostgreSQL | localhost:5432 | Database (user: optimizer) |
| Redis | localhost:6379 | Cache |

## Funzionalità

- ✅ Autenticazione JWT con ruoli (admin/operatore/visualizzatore)
- ✅ Upload CSV inventario WMS
- ✅ Ottimizzazione miscele multi-criterio
- ✅ Export risultati Excel
- ✅ API REST complete
- 🚧 Dashboard inventario con filtri (frontend in sviluppo)
- 🚧 Background processing per ottimizzazioni lunghe

## Ruoli Utenti

| Ruolo | Permissions |
|-------|-------------|
| **Admin** | Upload CSV, gestione utenti, tutte le operazioni |
| **Operatore** | Richiesta miscele, download Excel, visualizzazione inventario |
| **Visualizzatore** | Solo consultazione inventario |

## Credenziali Default

**IMPORTANTE**: Cambiare dopo primo accesso!

```
Username: admin
Password: changeme123
```

## Documentazione

- [Quick Start](docs/QUICKSTART.md) - Avvio rapido in 5 minuti
- [Deployment Guide](docs/DEPLOYMENT.md) - Deploy e troubleshooting completo
- [API Documentation](docs/API.md) - Riferimento API REST
- API Docs Interattiva: http://localhost:8000/docs

## Core Algorithm

Il motore di ottimizzazione è basato sul codebase [optimizer_v33](../../../MCP_ATTIVI/optimizer_v33) con:
- Scoring multi-criterio (10 parametri)
- Strategie diverse di generazione combinazioni
- Algoritmi di allocazione quantità ottimali
- Sistema compatibilità specie/colore/materiale
- **Riuso 80%+ codice esistente** tramite mount volume Docker

## Comandi Utili

```bash
# Avvio
docker-compose up -d

# Stop
docker-compose down

# Logs
docker-compose logs -f

# Restart backend
docker-compose restart backend

# Accedi al database
docker-compose exec db psql -U optimizer -d blend_optimizer

# Backup database
docker-compose exec db pg_dump -U optimizer blend_optimizer > backup.sql

# Reset completo (⚠️ CANCELLA DATI!)
docker-compose down
docker volume rm blend_optimizer_postgres_data
docker-compose up -d
```

## Troubleshooting

Vedi [docs/DEPLOYMENT.md#troubleshooting](docs/DEPLOYMENT.md#troubleshooting) per:
- Backend non si avvia
- Errori database
- Problemi upload CSV
- Reset database

## License

Proprietario - Uso interno aziendale
