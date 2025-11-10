# Git Hooks - Documentazione

## Overview

Questo progetto utilizza **git hooks** per automatizzare l'aggiornamento della documentazione e mantenere traccia delle modifiche in modo consistente.

## Hook Attivi

### prepare-commit-msg

**Posizione**: `.git/hooks/prepare-commit-msg`

**Funzionalità**:
- Rileva modifiche significative al codice (file `.py`, `.ts`, `.tsx`, `.js`, `.jsx`, `.sql`)
- Mostra un reminder per aggiornare la documentazione prima del commit
- Controlla se `CHANGELOG.md` è stato modificato
- Permette di annullare il commit se la documentazione non è aggiornata

**Quando si attiva**:
- Ogni volta che esegui `git commit` (esclusi merge e amend)

**Output di esempio**:
```
════════════════════════════════════════════════════════
  📝 REMINDER: Aggiorna la Documentazione!
════════════════════════════════════════════════════════

Hai modificato file di codice. Considera di aggiornare:

  📋 CHANGELOG.md
     └─ Aggiungi entry nella sezione [Unreleased]

  🏗️  ARCHITECTURE.md
     └─ Aggiorna se ci sono modifiche architetturali

  📖 README.md
     └─ Aggiorna se nuove features o setup changes

────────────────────────────────────────────────────────

⚠️  CHANGELOG.md non è stato modificato!

Vuoi continuare comunque? (y/N)
```

## Script Helper

### update-docs.sh

**Posizione**: `scripts/update-docs.sh`

**Funzionalità**:
Script interattivo per facilitare l'aggiornamento della documentazione.

**Uso**:
```bash
# Aggiorna tutto (interattivo)
./scripts/update-docs.sh

# Aggiorna solo CHANGELOG
./scripts/update-docs.sh changelog

# Aggiorna solo ARCHITECTURE
./scripts/update-docs.sh architecture

# Aggiorna solo README
./scripts/update-docs.sh readme
```

**Esempio workflow con script**:
```bash
# 1. Fai modifiche al codice
vim backend/app/api/endpoints/optimize.py

# 2. Aggiorna documentazione con script helper
./scripts/update-docs.sh

# 3. Commit (il git hook non ti fermerà più)
git add .
git commit -m "feat: aggiungi caching risultati ottimizzazione"
git push
```

## Workflow Completo

### Scenario 1: Nuova Feature

```bash
# 1. Crea branch feature
git checkout -b feature/caching-optimization

# 2. Implementa la feature
# ... modifiche ai file ...

# 3. Aggiorna documentazione
./scripts/update-docs.sh
# - Scegli "Added" nel CHANGELOG
# - Descrivi: "Sistema di caching per risultati ottimizzazione"
# - Aggiorna ARCHITECTURE.md se necessario

# 4. Stage e commit
git add .
git commit -m "feat: aggiungi caching risultati ottimizzazione

- Implementato Redis cache con TTL 1 ora
- Invalidazione automatica su nuovo upload inventario
- Ridotto tempo response da 2s a 200ms per query ripetute"

# 5. Push
git push origin feature/caching-optimization
```

### Scenario 2: Bug Fix

```bash
# 1. Fix il bug
# ... modifiche ai file ...

# 2. Aggiorna documentazione
./scripts/update-docs.sh changelog
# - Scegli "Fixed"
# - Descrivi: "Corretto calcolo percentuali con arrotondamento"

# 3. Commit
git add .
git commit -m "fix: corretto calcolo percentuali blend

Il calcolo precedente non arrotondava correttamente causando
somme != 100%. Ora usa Decimal per precisione."

# 4. Push
git push
```

### Scenario 3: Modifiche Architetturali

```bash
# 1. Implementa modifiche architetturali
# ... es: aggiungi nuovo microservizio ...

# 2. Aggiorna documentazione completa
./scripts/update-docs.sh all
# - Aggiungi al CHANGELOG sotto "Changed"
# - Apri ARCHITECTURE.md e aggiungi diagramma nuovo servizio
# - README viene aggiornato automaticamente

# 3. Commit con dettagli
git add .
git commit -m "refactor: migra optimizer a servizio separato

BREAKING CHANGE: API endpoint /optimize ora richiede header X-API-Key

Motivazione: Separare optimizer permette scaling indipendente
e supporto per multiple versioni algoritmo.

Vedi ARCHITECTURE.md per dettagli implementazione."

# 4. Push
git push
```

## Convenzioni Commit

Questo progetto segue **Conventional Commits**:

```
<type>(<scope>): <description>

[body opzionale]

[footer opzionale]
```

### Tipi

- `feat`: Nuova feature (minor version bump)
- `fix`: Bug fix (patch version bump)
- `docs`: Solo documentazione
- `style`: Formattazione, manca punto e virgola, ecc
- `refactor`: Refactoring senza nuove feature o fix
- `perf`: Miglioramenti performance
- `test`: Aggiungi o correggi test
- `chore`: Modifiche build, deps, config
- `ci`: Modifiche CI/CD

### Scope (opzionale)

- `backend`
- `frontend`
- `optimizer`
- `database`
- `docker`
- `docs`

### Esempi

```bash
# Feature con scope
git commit -m "feat(backend): aggiungi endpoint WebSocket per progress

Permette tracking real-time ottimizzazioni lunghe"

# Fix semplice
git commit -m "fix: correggi parsing CSV con virgolette escape"

# Breaking change
git commit -m "feat(api): cambia formato risposta /optimize

BREAKING CHANGE: La risposta ora include array 'solutions'
invece di oggetto flat. Vedi docs/API.md per dettagli."

# Solo docs
git commit -m "docs: aggiorna ARCHITECTURE con diagramma caching"

# Refactoring
git commit -m "refactor(optimizer): estrai logica scoring in classe separata

Migliora testability e separation of concerns"
```

## Troubleshooting

### Hook non si attiva

```bash
# Verifica che l'hook sia eseguibile
ls -la .git/hooks/prepare-commit-msg

# Se non lo è, rendilo eseguibile
chmod +x .git/hooks/prepare-commit-msg
```

### Disabilitare temporaneamente hook

```bash
# Opzione 1: flag --no-verify
git commit --no-verify -m "wip: commit temporaneo"

# Opzione 2: rinomina hook
mv .git/hooks/prepare-commit-msg .git/hooks/prepare-commit-msg.disabled

# Ricorda di riattivarlo!
mv .git/hooks/prepare-commit-msg.disabled .git/hooks/prepare-commit-msg
```

### Script update-docs.sh non funziona

```bash
# Verifica che sia eseguibile
ls -la scripts/update-docs.sh

# Rendilo eseguibile
chmod +x scripts/update-docs.sh

# Esegui dalla root del progetto
cd /path/to/blend-optimizer-web
./scripts/update-docs.sh
```

## Customizzazione

### Modificare comportamento hook

Edita il file `.git/hooks/prepare-commit-msg`:

```bash
# Apri con editor
vim .git/hooks/prepare-commit-msg

# Esempio: disabilitare prompt conferma
# Commenta le righe:
# read -p "Vuoi continuare comunque? (y/N) " -n 1 -r
# if [[ ! $REPLY =~ ^[Yy]$ ]]; then
#     exit 1
# fi
```

### Aggiungere nuovi hook

```bash
# Crea nuovo hook (es: pre-push per run tests)
vim .git/hooks/pre-push

# Rendilo eseguibile
chmod +x .git/hooks/pre-push
```

## Best Practices

1. **Aggiorna SEMPRE il CHANGELOG** per modifiche significative
2. **Usa conventional commits** per consistency
3. **Descrivi il "perché"**, non il "cosa" (il diff mostra il cosa)
4. **Aggiorna ARCHITECTURE.md** per modifiche strutturali
5. **Testa prima di committare** (run tests, build)
6. **Commit atomici**: un commit = una modifica logica
7. **Non committare**: `node_modules`, `.env`, file generati

## Automazione Futura

### GitHub Actions (Planned)

- **Auto-generate CHANGELOG**: Da conventional commits
- **Update version**: Semantic versioning automatico
- **Docs generation**: Auto-update API docs da code
- **Release notes**: Auto-generate da CHANGELOG

### Pre-commit Hooks (Planned)

- **Linting**: Black (Python), ESLint (TypeScript)
- **Type checking**: mypy (Python), tsc (TypeScript)
- **Tests**: Run unit tests modificati
- **Security**: Check secrets in commits

---

**Ultimo Aggiornamento**: 2025-01-10
**Versione**: 1.0
