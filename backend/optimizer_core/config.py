"""
OPTIMIZER v3.3 - Configurazione
Sistema di ottimizzazione miscele piume e piumini
"""

# ==============================================================================
# SISTEMA DI CODIFICA ARTICOLI
# ==============================================================================

MATERIAL_STATE_CODES = {
    'P': {
        'name': 'Piumino (Down)',
        'dc_range': (50, 100),
        'usage': 'Utilizzabile in QUALSIASI miscela',
        'restrictions': None
    },
    'M': {
        'name': 'Mezzo piumino',
        'dc_range': (30, 50),
        'usage': 'Solo per miscele con DC target ≤50%',
        'restrictions': 'dc_target_max_50'
    },
    'S': {
        'name': 'Piuma/Spiumata',
        'dc_range': (0, 30),
        'usage': 'Solo per miscele basso DC',
        'restrictions': 'dc_target_max_30'
    },
    'O': {
        'name': 'Originale',
        'dc_range': (0, 100),
        'usage': 'Non per miscele standard',
        'restrictions': 'special'
    }
}

SPECIES_CODES = {
    'O': 'Oca (Goose)',
    'A': 'Anatra (Duck)',
    'OA': 'Misto Oca-Anatra',
    'C': 'Couché'
}

# ==============================================================================
# CODICI ARTICOLO SPECIALI
# ==============================================================================
# Codici che non seguono il formato standard ma devono essere mappati a equivalenti
#
# IMPORTANTE: Il sistema usa match "contains" invece di match esatto.
# Questo permette di gestire varianti con suffissi automaticamente:
#   - "PGR"     → riconosciuto ✅
#   - "PGR.GRS" → riconosciuto ✅ (contiene "PGR")
#   - "PGR.XXX" → riconosciuto ✅ (contiene "PGR")
#
# I suffissi (es: .GRS, .RDS) sono ignorati e non cambiano il comportamento.
# Il codice viene sempre mappato all'equivalente base (POAG o POAB).
#
SPECIAL_ARTICLE_CODES = {
    'PGR': {
        'equivalent': 'POAG',
        'description': 'Piumino grigio riciclato',
        'state': 'P',
        'species': 'OA',
        'color': 'G',
        'note': 'Riconosce PGR, PGR.GRS, PGR.XXX (match contains)'
    },
    'PBR': {
        'equivalent': 'POAB',
        'description': 'Piumino bianco riciclato',
        'state': 'P',
        'species': 'OA',
        'color': 'B',
        'note': 'Riconosce PBR, PBR.GRS, PBR.XXX (match contains)'
    }
}

# ==============================================================================
# IMPORTANTE: GESTIONE DATI NON TESTATI
# ==============================================================================
#
# 1. DUCK CONTENT per articoli ANATRA:
#    - Negli articoli con species='A' (anatra pura), SCO_Duck è spesso 0 o vuoto
#    - Il sistema imputa automaticamente 100% (è ovvio che anatra = 100% duck)
#    - Vedi inventory.py:289-295
#
# 2. DC e FP NON TESTATI (valori = 0):
#    - Quando DC_real = 0 o FP_real = 0, significa "non ancora testato"
#    - Il sistema usa i valori NOMINALI (DC_nominal, FP_nominal) come stima
#    - Questi lotti sono marcati come "is_estimated = True"
#    - Vedi inventory.py:279-287
#
# 3. STRATEGIA A CASCATA (default):
#    - Sistema PROVA PRIMA con SOLO dati misurati (allow_estimated=False)
#    - Se NON trova soluzioni, AVVISA e chiede APPROVAZIONE per usare dati stimati
#    - Utente deve ESPLICITAMENTE approvare con allow_estimated=True
#    - Questo garantisce che i dati stimati siano usati solo se necessario
#
# 4. AFFIDABILITÀ VALORI NOMINALI:
#    - I valori nominali (DC_nom, FP_nom) sono dichiarazioni dell'articolo
#    - Sono generalmente affidabili ma non verificati in laboratorio
#    - Usare con cautela e preferire sempre dati misurati quando disponibili
# ==============================================================================

COLOR_CODES = {
    'PW': {'name': 'Pure White', 'quality_rank': 1},
    'BPW': {'name': 'Bianco Pure White', 'quality_rank': 1},  # Variante B+PW
    'NPW': {'name': 'Nearly Pure White', 'quality_rank': 2},
    'BNPW': {'name': 'Bianco Nearly Pure White', 'quality_rank': 2},  # Variante B+NPW
    'B': {'name': 'Bianco Standard', 'quality_rank': 3},
    'G': {'name': 'Grigio', 'quality_rank': 4},
    'R': {'name': 'Riciclato/Generico', 'quality_rank': 5}  # Riciclato
}

# ==============================================================================
# REGOLE DI COMPATIBILITÀ
# ==============================================================================

# Compatibilità Specie - AGGIORNATA v3.3
SPECIES_COMPATIBILITY = {
    'goose_blend_with_duck_target': {
        'description': 'Miscele di oca CON duck target specificato',
        'preferred_order': ['O', 'OA', 'A'],
        'strategy': 'Preferire OA (misto) per raggiungere duck target economico',
        'penalties': {
            'using_OA_in_goose': -50,      # Penalità bassa (preferibile)
            'using_A_in_goose': -150,      # Penalità media (accettabile)
            'duck_below_target': -500,     # FORTE penalità se duck < target
            'duck_above_target': -200      # Penalità se duck > target+5%
        }
    },
    'duck_blend': {
        'description': 'Miscele di anatra',
        'allowed': ['A', 'OA'],
        'forbidden': ['O'],
        'penalties': {
            'using_O_in_duck': -1000  # Blocco totale: spreco inaccettabile
        }
    }
}

# Compatibilità Colore - matrice penalità
COLOR_COMPATIBILITY_MATRIX = {
    'PW': {
        'PW': 0,
        'NPW': -10000,  # Bloccato
        'B': -10000,    # Bloccato
        'G': -10000     # Bloccato
    },
    'NPW': {
        'PW': -50,      # Penalità bassa
        'NPW': 0,
        'B': -10000,    # Bloccato
        'G': -10000     # Bloccato
    },
    'B': {
        'PW': -150,     # Penalità media
        'NPW': -80,     # Penalità bassa
        'B': 0,
        'G': -10000     # Bloccato
    },
    'G': {
        'PW': -300,     # Penalità alta
        'NPW': -200,    # Penalità media
        'B': -100,      # Penalità bassa
        'G': 0
    }
}

# Trattamenti Water Repellent - CORRETTI v3.3
WATER_REPELLENT_RULES = {
    'equivalent_treatments': ['GWR', 'NWR'],  # Intercambiabili
    'default_behavior': 'exclude',  # Default: escludi da miscele normali
    'mixing_allowed': False,  # Default: non mescolare con normali
    'compatibility': 'GWR = NWR (completamente intercambiabili)',
    'detection': {
        'locations': [
            'certification (terza parte codice articolo: 3|POB|GWR)',
            'quality_nominal (campo SCO_Quality_Nom dal CSV)'
        ],
        'note': 'Il sistema controlla ENTRAMBI i posti per identificare lotti water repellent'
    }
}

# ==============================================================================
# PARAMETRI DI OTTIMIZZAZIONE
# ==============================================================================

# Tolleranze default
DEFAULT_TOLERANCES = {
    'dc_tolerance': 3.0,      # ±3% per Down Cluster
    'fp_tolerance': 5.0,      # ±5% per Fill Power
    'duck_tolerance': 5.0,    # ±5% per Duck content
    'oe_tolerance': 2.0       # ±2% per Other Elements
}

# Pesi di scoring multi-criterio
SCORING_WEIGHTS = {
    # Conformità ai target (massima priorità)
    'dc_target_match': 1000,
    'fp_target_match': 800,
    'duck_target_match': 600,  # CRITICO per ottimizzazione economica

    # Smaltimento materiali brutti
    'low_dc_disposal': 500,
    'high_duck_disposal': 400,  # Solo per miscele oca
    'high_oe_disposal': 250,

    # Efficienza miscela
    'lot_count_penalty': -50,   # Per ogni lotto oltre il 5°
    'estimated_data_penalty': -100,  # Penalità per dati stimati

    # Compatibilità specie
    'species_optimization_bonus': 50,   # Bonus per OA in goose
    'species_mismatch_penalty': -150,    # Penalità per A in goose

    # Valore di opportunità DC (NEW v3.3.1)
    'dc_overqualification_penalty_weight': 1.0,  # Peso penalità per DC surplus
    'dc_overqualification_threshold': 5.0  # Soglia minima surplus (%) prima di applicare penalità
}

# Limiti operativi
OPERATIONAL_LIMITS = {
    'max_lots_per_blend': 10,    # Massimo lotti in una miscela (flessibile, sistema può usare fino a 10)
    'ideal_lots_per_blend': 5,   # Numero ideale di lotti (2-5: nessuna penalità, 6-7: penalità leggera)
    'min_lot_usage_kg': 10,      # Minimo utilizzo per lotto (kg)
    'max_lot_usage_pct': 95      # Massimo utilizzo disponibilità (%)
}

# ==============================================================================
# FORMATO OUTPUT EXCEL
# ==============================================================================

OUTPUT_EXCEL_COLUMNS = [
    # Identificazione articolo
    'Codice Art',
    'Variante DC Nominale',
    'Variante Quality nominale',
    'Variante Std nominale',
    'Variante FP nominale',
    
    # Identificazione lotto
    'Codice Lotto',
    'Descrizione lotto',
    'Note Laboratorio',
    
    # Valori reali misurati
    'DC reale',
    'Other Elements reale',
    'Feather reale',
    'FP reale',
    'Duck reale',
    'Stimato si/no',
    'Ossigeno reale O2',
    'Turbidità reale',
    
    # Disponibilità e costi
    'Quantità disponibile a magazzino',
    'Costo euro/kg',
    
    # Qualità dettaglio
    'Total Fibres',
    'Broken',
    'Landfowl',
    
    # Utilizzo in miscela
    'Kg tot usati in miscela',
    '% di miscela'
]

# Mapping colonne CSV -> Output Excel
CSV_TO_EXCEL_MAPPING = {
    'SCO_ART': 'Codice Art',
    'SCO_LOTT': 'Codice Lotto',
    'SCO_DownCluster_Real': 'DC reale',
    'SCO_OtherElements_Real': 'Other Elements reale',
    'SCO_Feather_Real': 'Feather reale',
    'SCO_FillPower_Real': 'FP reale',
    'SCO_Duck_Real': 'Duck reale',
    'SCO_Ossigeno_Real': 'Ossigeno reale O2',
    'SCO_Torbidita_Real': 'Turbidità reale',
    'SCO_TotalFibres_Real': 'Total Fibres',
    'SCO_Broken_Real': 'Broken',
    'SCO_Landfowl_Real': 'Landfowl',
    'SCO_Qty': 'Quantità disponibile a magazzino',
    'SCO_CostoKg': 'Costo euro/kg'
}

# Colori per formattazione Excel
EXCEL_COLORS = {
    'header': '2B5797',        # Blu scuro per header
    'optimal': '70AD47',       # Verde per valori ottimali
    'acceptable': 'FFC000',    # Giallo per valori accettabili
    'critical': 'FF0000',      # Rosso per valori critici
    'estimated': 'FFFF00',     # Giallo chiaro per dati stimati
    'wr_special': '00B0F0'     # Blu per water repellent
}

# Indicatori visuali
VISUAL_INDICATORS = {
    'optimal': '✅',
    'acceptable': '⚠️',
    'critical': '❌'
}

# ==============================================================================
# STANDARD INTERNAZIONALI
# ==============================================================================

INTERNATIONAL_STANDARDS = {
    'US': 'USA-2000',
    'EN': 'EN12934',
    'KS': 'Korean Standard',
    'GB': 'GB/T',
    'J': 'JIS (Japanese)'
}

# ==============================================================================
# PARAMETRI DI RICERCA
# ==============================================================================

SEARCH_PARAMS = {
    'initial_dc_range': 15,    # ±15% per ricerca iniziale candidati
    'final_dc_tolerance': 3,   # ±3% per validazione finale
    'fp_range': 10,            # ±10 cuin/oz per Fill Power
    'max_combinations': 25000  # Ridotto per evitare timeout MCP (4 min limit Claude Desktop)
}

# ==============================================================================
# CONFIGURAZIONE INVENTARIO
# ==============================================================================

INVENTORY_CONFIG = {
    'default_csv_path': '/Users/carlocassigoli/CODE-progetti-Claude/Claude/MCP_ATTIVI/Inventario_WMS/lotti.csv',
    'auto_load_on_start': True,  # Auto-carica inventario all'avvio server
    'csv_separator': ',',
    'csv_encoding': 'utf-8'
}
