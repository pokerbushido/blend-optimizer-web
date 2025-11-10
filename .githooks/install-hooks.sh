#!/bin/bash
# Script: Installazione Git Hooks
# Copia gli hooks dalla directory .githooks/hooks a .git/hooks

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
HOOKS_SOURCE="$SCRIPT_DIR/hooks"
HOOKS_DEST="$PROJECT_ROOT/.git/hooks"

# Colori
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${BLUE}════════════════════════════════════════${NC}"
echo -e "${BLUE}  Git Hooks Installation${NC}"
echo -e "${BLUE}════════════════════════════════════════${NC}"
echo ""

# Verifica che .git esista
if [ ! -d "$PROJECT_ROOT/.git" ]; then
    echo -e "${YELLOW}⚠️  Questo non sembra essere un repository git${NC}"
    echo "Esegui 'git init' prima di installare gli hooks"
    exit 1
fi

# Copia tutti gli hooks
INSTALLED_COUNT=0
for hook_file in "$HOOKS_SOURCE"/*; do
    if [ -f "$hook_file" ]; then
        hook_name=$(basename "$hook_file")
        dest_file="$HOOKS_DEST/$hook_name"

        # Backup se esiste già
        if [ -f "$dest_file" ]; then
            echo -e "${YELLOW}⚠️  Backup esistente hook: $hook_name${NC}"
            cp "$dest_file" "$dest_file.backup.$(date +%Y%m%d_%H%M%S)"
        fi

        # Copia e rendi eseguibile
        cp "$hook_file" "$dest_file"
        chmod +x "$dest_file"

        echo -e "${GREEN}✓${NC} Installato: $hook_name"
        ((INSTALLED_COUNT++))
    fi
done

echo ""
echo -e "${GREEN}════════════════════════════════════════${NC}"
echo -e "${GREEN}  ✓ Installazione completata!${NC}"
echo -e "${GREEN}════════════════════════════════════════${NC}"
echo ""
echo "Hook installati: $INSTALLED_COUNT"
echo ""
echo "Gli hooks sono attivi e verranno eseguiti automaticamente."
echo "Per maggiori dettagli, consulta .githooks/README.md"
echo ""
