#!/bin/bash
# Script Helper: Aggiornamento Documentazione
# Uso: ./scripts/update-docs.sh [changelog|architecture|readme|all]

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Colori per output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Funzione helper per timestamp
get_date() {
    date +"%Y-%m-%d"
}

# Funzione per aggiornare CHANGELOG
update_changelog() {
    echo -e "${BLUE}📋 Aggiornamento CHANGELOG.md${NC}"
    echo ""
    echo "Che tipo di modifica vuoi registrare?"
    echo "1) Added (nuove feature)"
    echo "2) Changed (modifiche a feature esistenti)"
    echo "3) Fixed (bug fix)"
    echo "4) Security (fix vulnerabilità)"
    echo "5) Deprecated (feature deprecate)"
    echo "6) Removed (feature rimosse)"
    echo ""
    read -p "Scelta (1-6): " choice

    case $choice in
        1) change_type="Added" ;;
        2) change_type="Changed" ;;
        3) change_type="Fixed" ;;
        4) change_type="Security" ;;
        5) change_type="Deprecated" ;;
        6) change_type="Removed" ;;
        *) echo -e "${RED}Scelta non valida${NC}"; exit 1 ;;
    esac

    echo ""
    read -p "Descrivi la modifica: " description

    # Trova la sezione [Unreleased] e aggiungi l'entry
    CHANGELOG="$PROJECT_ROOT/CHANGELOG.md"

    # Crea backup
    cp "$CHANGELOG" "$CHANGELOG.bak"

    # Aggiungi entry sotto [Unreleased]
    awk -v type="$change_type" -v desc="- $description" '
        /## \[Unreleased\]/ {
            print;
            getline;
            print;
            if (index($0, "### " type) > 0) {
                print;
                getline;
                print desc;
                print;
            } else {
                print "### " type;
                print desc;
                print "";
            }
            next;
        }
        { print }
    ' "$CHANGELOG.bak" > "$CHANGELOG"

    rm "$CHANGELOG.bak"

    echo -e "${GREEN}✓ CHANGELOG.md aggiornato${NC}"
    echo ""
    echo "Entry aggiunta:"
    echo "  $change_type: $description"
    echo ""
}

# Funzione per aggiornare ARCHITECTURE
update_architecture() {
    echo -e "${BLUE}🏗️  Aggiornamento ARCHITECTURE.md${NC}"
    echo ""
    echo "Che sezione vuoi aggiornare?"
    echo "1) Database Schema (nuove tabelle/colonne)"
    echo "2) API Endpoints (nuovi endpoint)"
    echo "3) Componenti Sistema (nuovi servizi)"
    echo "4) Decisioni Architetturali (ADR)"
    echo "5) Altro (edit manuale)"
    echo ""
    read -p "Scelta (1-5): " choice

    ARCHITECTURE="$PROJECT_ROOT/ARCHITECTURE.md"

    case $choice in
        1|2|3|4)
            echo ""
            echo -e "${YELLOW}Nota: Aprirò il file per edit manuale${NC}"
            echo "Premi ENTER per continuare..."
            read
            ${EDITOR:-vi} "$ARCHITECTURE"
            ;;
        5)
            ${EDITOR:-vi} "$ARCHITECTURE"
            ;;
        *)
            echo -e "${RED}Scelta non valida${NC}"
            exit 1
            ;;
    esac

    # Aggiorna timestamp
    sed -i.bak "s/\*\*Ultimo Aggiornamento\*\*: .*/\*\*Ultimo Aggiornamento\*\*: $(get_date)/" "$ARCHITECTURE"
    rm "$ARCHITECTURE.bak"

    echo -e "${GREEN}✓ ARCHITECTURE.md aggiornato${NC}"
    echo ""
}

# Funzione per aggiornare README
update_readme() {
    echo -e "${BLUE}📖 Aggiornamento README.md${NC}"
    echo ""
    echo "Aggiornamento automatico timestamp..."

    README="$PROJECT_ROOT/README.md"

    # Aggiorna data ultimo aggiornamento
    sed -i.bak "s/\*\*Ultimo Aggiornamento\*\*: .*/\*\*Ultimo Aggiornamento\*\*: $(get_date)/" "$README"
    rm "$README.bak"

    echo -e "${GREEN}✓ README.md aggiornato${NC}"
    echo ""
}

# Funzione per aggiornare tutto
update_all() {
    echo -e "${YELLOW}════════════════════════════════════════${NC}"
    echo -e "${YELLOW}  Aggiornamento Completo Documentazione${NC}"
    echo -e "${YELLOW}════════════════════════════════════════${NC}"
    echo ""

    update_changelog
    echo ""
    read -p "Vuoi aggiornare anche ARCHITECTURE.md? (y/N) " -n 1 -r
    echo ""
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        update_architecture
    fi

    update_readme

    echo ""
    echo -e "${GREEN}════════════════════════════════════════${NC}"
    echo -e "${GREEN}  ✓ Documentazione aggiornata con successo!${NC}"
    echo -e "${GREEN}════════════════════════════════════════${NC}"
    echo ""
    echo "File modificati:"
    echo "  - CHANGELOG.md"
    echo "  - README.md"
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo "  - ARCHITECTURE.md"
    fi
    echo ""
    echo "Prossimo step:"
    echo "  git add CHANGELOG.md README.md ARCHITECTURE.md"
    echo "  git commit -m \"docs: aggiorna documentazione\""
    echo ""
}

# Main
case "${1:-all}" in
    changelog)
        update_changelog
        ;;
    architecture)
        update_architecture
        ;;
    readme)
        update_readme
        ;;
    all)
        update_all
        ;;
    *)
        echo "Uso: $0 [changelog|architecture|readme|all]"
        echo ""
        echo "Esempi:"
        echo "  $0 changelog     # Aggiorna solo CHANGELOG.md"
        echo "  $0 architecture  # Aggiorna solo ARCHITECTURE.md"
        echo "  $0 readme        # Aggiorna solo README.md"
        echo "  $0 all           # Aggiorna tutto (default)"
        exit 1
        ;;
esac
