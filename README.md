# Blend Optimizer Web Application

<div align="center">

![Version](https://img.shields.io/badge/version-1.0.0-blue.svg)
![License](https://img.shields.io/badge/license-Proprietary-red.svg)
![Status](https://img.shields.io/badge/status-Active-success.svg)

Sistema web full-stack per l'ottimizzazione di miscele (blend) di piuma e piumino con gestione inventario WMS integrata.

[Documentazione](./docs) • [API Reference](./docs/API.md) • [Changelog](./CHANGELOG.md) • [Architettura](./ARCHITECTURE.md)

</div>

---

## 📋 Indice

- [Panoramica](#-panoramica)
- [Quick Start](#-quick-start)
- [Funzionalità](#-funzionalità)
- [Architettura](#-architettura)
- [Tecnologie](#-tecnologie)
- [Installazione](#-installazione)
- [Testing](#-testing)
- [Documentazione](#-documentazione)
- [Troubleshooting](#-troubleshooting)
- [Contribuire](#-contribuire)

---

## 🎯 Panoramica

Blend Optimizer è un'applicazione web enterprise per l'ottimizzazione automatica di blend di piuma e piumino. Il sistema integra dati da WMS aziendale, applica algoritmi multi-criterio per trovare le migliori combinazioni di lotti, e genera report Excel dettagliati per la produzione.

### Caratteristiche Principali

- **Ottimizzazione Multi-Criterio**: 10+ parametri di qualità (Fill Power, Down Content, Cleanliness, ecc.)
- **Integrazione WMS**: Import diretto da CSV esportati dal sistema gestionale
- **Sistema Ruoli**: Admin, Operatore, Visualizzatore con permessi granulari
- **Export Professionale**: Report Excel formattati con analisi completa
- **API REST**: Documentazione interattiva Swagger/ReDoc
- **Real-time**: Processamento asincrono con feedback progressivo
- **Containerizzato**: Deploy Docker Compose ready-to-use

---

## 🚀 Quick Start

**Setup completo in 5 minuti**:

```bash
# 1. Clone repository
git clone https://github.com/pokerbushido/blend-optimizer-web.git
cd blend-optimizer-web

# 2. Installa git hooks (per auto-update documentazione)
./.githooks/install-hooks.sh

# 3. Setup environment
cp .env.example .env
# Modifica .env: cambia POSTGRES_PASSWORD e genera SECRET_KEY

# 4. Avvia con Docker
docker-compose up -d

# 5. Test automatico
cd scripts
chmod +x test_api.sh
./test_api.sh
```

**Note**:
- I git hooks automatizzano l'aggiornamento di CHANGELOG.md e documentazione
- Vedi [.githooks/README.md](./.githooks/README.md) per dettagli

📖 **Guide Dettagliate**:
- [Quick Start Guide](docs/QUICKSTART.md) - Avvio in 5 minuti
- [Deployment Guide](docs/DEPLOYMENT.md) - Guida completa con troubleshooting
- [API Documentation](docs/API.md) - Documentazione completa API

---

## 🏗️ Architettura

```
blend-optimizer-web/
├── backend/                    # Backend FastAPI
│   ├── app/
│   │   ├── api/                   # REST endpoints
│   │   │   └── endpoints/         # Auth, Inventory, Optimize, Users
│   │   ├── core/                  # Business logic
│   │   │   ├── inventory_service.py
│   │   │   ├── optimizer_service.py
│   │   │   ├── excel_export_service.py
│   │   │   └── security.py
│   │   ├── models/                # SQLAlchemy ORM
│   │   └── schemas/               # Pydantic validation
│   ├── optimizer_core/         # Algoritmo ottimizzazione
│   │   ├── optimizer.py           # Motore principale
│   │   ├── inventory.py           # Gestione lotti
│   │   ├── compatibility.py       # Regole compatibilità
│   │   └── excel_export.py        # Generazione report
│   ├── migrations/             # Database schema
│   └── requirements.txt
├── frontend/                   # Frontend React + TypeScript
│   ├── src/
│   │   ├── components/            # UI Components
│   │   ├── pages/                 # Pagine applicazione
│   │   ├── hooks/                 # React hooks custom
│   │   ├── store/                 # State management (Zustand)
│   │   ├── api/                   # API client
│   │   └── utils/                 # Utilities
│   └── package.json
├── docker/                     # Docker configurations
├── scripts/                    # Utility e test scripts
├── docs/                       # Documentazione completa
├── ARCHITECTURE.md             # Architettura dettagliata
├── CHANGELOG.md                # Cronologia modifiche
└── docker-compose.yml
```

Per dettagli sull'architettura, vedi [ARCHITECTURE.md](./ARCHITECTURE.md).

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

---

## 🤝 Contribuire

### Workflow Git

1. Crea un branch per la feature: `git checkout -b feature/nome-feature`
2. Fai le modifiche e commit: `git commit -m "descrizione"`
3. Aggiorna la documentazione:
   - `CHANGELOG.md` - Aggiungi entry nella sezione `[Unreleased]`
   - `ARCHITECTURE.md` - Aggiorna se modifiche strutturali
4. Push e crea Pull Request: `git push origin feature/nome-feature`

### Convenzioni

- **Commit Messages**: Usa conventional commits (`feat:`, `fix:`, `docs:`, ecc.)
- **Branch Names**: `feature/`, `bugfix/`, `hotfix/`, `docs/`
- **Code Style**: Segui PEP8 per Python, ESLint per TypeScript

### Aggiornamento Documentazione

La documentazione viene aggiornata automaticamente tramite git hooks. Assicurati di:
- Aggiornare `CHANGELOG.md` per ogni modifica significativa
- Aggiornare `ARCHITECTURE.md` per modifiche architetturali
- Il README viene mantenuto aggiornato automaticamente

---

## 📊 Stato Progetto

Vedi [CHANGELOG.md](./CHANGELOG.md) per la cronologia completa delle modifiche.

**Versione Corrente**: 1.0.0
**Ultimo Aggiornamento**: 2025-01-10

---

## 📄 License

Proprietario - Uso interno aziendale

---

## 👥 Team

Sviluppato internamente per l'ottimizzazione della produzione di articoli in piuma e piumino.

**Contatti**: Per supporto o domande, contattare il team IT interno.
