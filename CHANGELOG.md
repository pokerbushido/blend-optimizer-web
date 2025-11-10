# Changelog

Tutte le modifiche significative a questo progetto saranno documentate in questo file.

Il formato è basato su [Keep a Changelog](https://keepachangelog.com/it/1.0.0/),
e questo progetto aderisce al [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Planned
- Frontend React completo con tutte le pagine
- Background processing per ottimizzazioni lunghe con progress bar
- Notifiche real-time via WebSocket
- Sistema di caching per risultati ottimizzazione
- Dashboard analytics avanzata
- Export PDF report
- Multi-lingua (IT/EN)

---

## [1.1.0] - 2025-11-10

### Added
- **Color Compatibility Scoring**: Nuova metrica per penalizzare l'uso di lotti con qualità colore inferiore rispetto a quella richiesta
  - Implementata `COLOR_COMPATIBILITY_MATRIX` per gestire penalità tra diversi livelli di qualità (PW, NPW, B)
  - Metodo `_score_color_compatibility()` per calcolare penalità proporzionali ai kg utilizzati
- **Product Match Percentage**: Nuova metrica `requested_product_match_pct` nelle soluzioni di blend
  - Calcola la percentuale di kg che utilizza esattamente il colore/qualità richiesto
  - Visibile nei risultati per aiutare l'utente a capire quanto della miscela usa il prodotto premium richiesto

### Changed
- **Timeout Aumentati per Ottimizzazioni Complesse**:
  - Frontend API client: timeout portato da 30s a 300s (5 minuti)
  - Nginx proxy: aggiunti timeout settings (connect: 60s, send/read: 300s)
  - Documentazione API: aggiornata nota timeout da ~10s a "fino a 5 minuti per richieste complesse"

### Fixed
- **Path Dinamico Optimizer Core**: Risolto problema hardcoded path `/app/optimizer_core`
  - `excel_export_service.py`: calcolo dinamico path relativo
  - `inventory_service.py`: calcolo dinamico path relativo
  - `optimizer_service.py`: calcolo dinamico path relativo
  - Migliora portabilità del codice tra ambienti (Docker, locale, test)
- **Config Validation**: Aggiunti validatori Pydantic per parsing corretto di variabili d'ambiente
  - `BACKEND_CORS_ORIGINS`: supporto parsing JSON string
  - `ALLOWED_EXTENSIONS`: supporto parsing JSON string
  - Aggiunta configurazione `extra = "ignore"` per ignorare variabili extra

### Technical Improvements
- Migliorata robustezza del sistema di scoring ottimizzatore con nuove metriche qualitative
- Aggiunta gestione sicura dei path per compatibilità cross-platform
- Estesa validazione configurazione backend per deployment più flessibile

---

## [1.0.0] - 2025-01-10

### Added - Rilascio Iniziale

#### Backend
- Sistema di autenticazione JWT con refresh token
- Gestione ruoli utente (Admin, Operatore, Visualizzatore)
- API REST complete per:
  - Autenticazione (`/api/auth/*`)
  - Gestione inventario (`/api/inventory/*`)
  - Ottimizzazione blend (`/api/optimize/*`)
  - Gestione utenti (`/api/users/*`)
- Upload CSV inventario WMS con validazione completa
- Ottimizzatore multi-criterio con 10+ parametri qualità
- Export Excel report formattati con:
  - Foglio "Mix Details" con composizione blend
  - Foglio "Lot Details" con dettagli singoli lotti
  - Foglio "Quality Metrics" con analisi qualità
  - Formattazione professionale e colori
- Database PostgreSQL con migrations
- Redis cache per sessioni
- Documentazione API interattiva (Swagger/ReDoc)

#### Frontend
- Setup React 18 + TypeScript + Vite
- Tailwind CSS per styling
- Zustand per state management
- Axios per API calls
- React Router per navigazione
- Componenti UI base:
  - Layout (Navbar, Sidebar)
  - Form components (Input, Select, Button)
  - UI components (Card, Modal, Spinner, Badge)
- Pagine implementate:
  - Login con autenticazione JWT
  - Dashboard con statistiche inventario
  - Inventory listing con filtri
  - Upload CSV
  - Optimize blend form
  - Results display
  - Users management (Admin)
  - History ottimizzazioni
- Hook custom per auth, inventory, optimization

#### DevOps & Infrastructure
- Docker Compose setup per sviluppo
- Docker Compose production-ready
- Dockerfile multi-stage per backend e frontend
- Nginx reverse proxy configurato
- Health check endpoints
- Volume persistenti per database
- Network isolation tra servizi

#### Algoritmo Core
- Riuso 80%+ codice da optimizer_v33
- Sistema compatibilità specie/colore/materiale
- Scoring multi-criterio normalizzato
- Strategie multiple generazione combinazioni:
  - Greedy
  - Best performers
  - Diversity
  - Quality first
- Algoritmi allocazione quantità ottimali
- Gestione gerarchica dati reali vs stimati
- Validazione standard Fill Power (EN, US, JIS, CN)

#### Documentazione
- README.md completo con quick start
- QUICKSTART.md per avvio rapido
- DEPLOYMENT.md con guida completa deploy
- API.md con reference completo
- ARCHITECTURE.md con diagrammi sistema
- CHANGELOG.md per tracking modifiche
- Script di test automatici

#### Testing & Quality
- Script bash test_api.sh per testing automatico
- CSV di test per validazione upload
- Test suite per export Excel
- Test integrazione optimizer
- Validazione Pandas Series fix

### Security
- Password hashing con bcrypt
- JWT token con expiration
- CORS configurato per intranet
- Environment variables per secrets
- SQL injection protection via ORM
- Input validation con Pydantic
- Rate limiting su API critiche

### Performance
- Connection pooling PostgreSQL
- Redis caching sessioni utente
- Lazy loading componenti React
- Code splitting frontend
- Ottimizzazione query database con indici
- Async/await per operazioni I/O

---

## Convenzioni

### Tipi di Modifiche
- `Added` - Nuove funzionalità
- `Changed` - Modifiche a funzionalità esistenti
- `Deprecated` - Funzionalità deprecate (saranno rimosse)
- `Removed` - Funzionalità rimosse
- `Fixed` - Bug fix
- `Security` - Vulnerabilità risolte

### Formato Entry
```
### Tipo
- Breve descrizione della modifica (#issue-number se applicabile)
- Dettagli addizionali se necessari
```

---

## Link Versioni

- [Unreleased]: https://github.com/pokerbushido/blend-optimizer-web/compare/v1.1.0...HEAD
- [1.1.0]: https://github.com/pokerbushido/blend-optimizer-web/compare/v1.0.0...v1.1.0
- [1.0.0]: https://github.com/pokerbushido/blend-optimizer-web/releases/tag/v1.0.0

---

**Note**: Questo changelog viene aggiornato automaticamente tramite git hooks ad ogni commit significativo.
