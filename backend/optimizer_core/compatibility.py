"""
OPTIMIZER v3.3 - Product Compatibility Manager
Gestione regole di compatibilità tra articoli
"""

import re
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from config import (
    MATERIAL_STATE_CODES,
    SPECIES_CODES,
    COLOR_CODES,
    COLOR_COMPATIBILITY_MATRIX,
    SPECIES_COMPATIBILITY,
    WATER_REPELLENT_RULES,
    SPECIAL_ARTICLE_CODES
)


@dataclass
class ProductCode:
    """Rappresenta un codice articolo decodificato"""
    raw_code: str
    group: Optional[str] = None
    state: Optional[str] = None  # P, M, S, O
    species: Optional[str] = None  # O, A, OA, C
    color: Optional[str] = None  # PW, NPW, B, G
    certification: Optional[str] = None
    
    def __post_init__(self):
        """Decodifica automatica del codice"""
        if self.raw_code and not self.state:
            self._parse_code()
    
    def _parse_code(self):
        """
        Parse codice formato: [G]|{STATO}{SPECIE}{COLORE}|[CERT]
        Esempi: 3|POB, 3|PAB, G|POAG|GWR, 3|PABPW

        OPPURE formato semplice senza gruppo: {STATO}{SPECIE}{COLORE}
        Esempi: POB, PAB, POAG

        OPPURE codici speciali (PGR, PBR) che vengono mappati a equivalenti standard

        Parsing flessibile:
        - Accetta sia formato con gruppo (3|PAB) che senza gruppo (PAB)
        - Gestisce codici speciali (PGR→POAG, PBR→POAB)
        - Estrae stato (P/M/S/O)
        - Estrae specie (O/A/OA/C)
        - Estrae colore (anche varianti come BPW, BNPW)
        - Se colore non è nei code, normalizza al colore base
        """
        parts = self.raw_code.split('|')

        # GESTIONE CODICI SPECIALI (PGR, PBR, ecc.)
        # Estrai main_code provvisorio per controllare se è speciale
        temp_main_code = parts[1] if len(parts) >= 2 else parts[0]

        # Controlla se il codice CONTIENE uno dei codici speciali
        # Questo gestisce varianti con suffissi (es: PGR.GRS, PBR.GRS, PGR.XXX)
        # Ordina per lunghezza decrescente per evitare match parziali indesiderati
        special_match = None
        for special_code in sorted(SPECIAL_ARTICLE_CODES.keys(), key=len, reverse=True):
            if special_code in temp_main_code:
                special_match = special_code
                break

        if special_match:
            special_info = SPECIAL_ARTICLE_CODES[special_match]

            # Mappa direttamente alle proprietà dell'equivalente
            self.state = special_info['state']
            self.species = special_info['species']
            self.color = special_info['color']

            # Gestisci gruppo se presente nel formato originale
            if len(parts) >= 2:
                self.group = parts[0]
            else:
                self.group = None

            # Gestisci certificazione se presente
            if len(parts) >= 3:
                self.certification = parts[2]
            else:
                self.certification = None

            return  # Parsing completato per codice speciale

        # CASO 1: Formato con gruppo (3|PAB|GWR o 3|PAB)
        if len(parts) >= 2:
            self.group = parts[0]
            main_code = parts[1]

            # Certificazione (se presente)
            if len(parts) >= 3:
                self.certification = parts[2]

        # CASO 2: Formato semplice senza gruppo (PAB, POAG)
        elif len(parts) == 1:
            main_code = parts[0]
            self.group = None
            self.certification = None

        else:
            # Formato non riconosciuto
            return

        # Parse main_code: {STATO}{SPECIE}{COLORE}
        if len(main_code) >= 3:
            self.state = main_code[0]  # Prima lettera: P, M, S, O

            # Specie: può essere O, A, OA (2 lettere), C
            if len(main_code) >= 4 and main_code[1:3] == 'OA':
                self.species = 'OA'
                color_part = main_code[3:] if len(main_code) > 3 else None
            else:
                self.species = main_code[1]
                color_part = main_code[2:] if len(main_code) > 2 else None

            # Parsing colore flessibile
            if color_part:
                self.color = self._parse_color_flexible(color_part)

    def _parse_color_flexible(self, color_str: str) -> Optional[str]:
        """
        Parse colore in modo flessibile

        Gestisce:
        - Colori esatti (B, G, PW, NPW, BPW, etc.)
        - Colori con suffissi (B.FM, BPW.RDS, G.CINA)
        - Normalizzazione a colore base se non trovato

        Returns:
            Codice colore normalizzato
        """
        if not color_str:
            return None

        # Se è esattamente nei COLOR_CODES, usa quello
        if color_str in COLOR_CODES:
            return color_str

        # Prova a estrarre parte prima del punto (es: B.FM -> B)
        if '.' in color_str:
            base_color = color_str.split('.')[0]
            if base_color in COLOR_CODES:
                return base_color

        # Prova varianti comuni
        # BPW -> se non riconosciuto, prova solo i primi caratteri
        if len(color_str) >= 3:
            # Prova primi 3 caratteri (es: BPW)
            if color_str[:3] in COLOR_CODES:
                return color_str[:3]

        if len(color_str) >= 2:
            # Prova primi 2 (es: PW, NPW)
            if color_str[:2] in COLOR_CODES:
                return color_str[:2]

        # Fallback: primo carattere (B, G, R)
        if len(color_str) >= 1:
            if color_str[0] in COLOR_CODES:
                return color_str[0]

        # Se nessun match, ritorna il colore originale
        # (sarà segnalato come non valido ma almeno non perdiamo info)
        return color_str

    def is_valid(self) -> bool:
        """Verifica validità del codice"""
        if not all([self.state, self.species, self.color]):
            return False
        
        return (
            self.state in MATERIAL_STATE_CODES and
            self.species in SPECIES_CODES and
            self.color in COLOR_CODES
        )
    
    def is_water_repellent(self) -> bool:
        """Verifica se ha trattamento water repellent"""
        if not self.certification:
            return False
        return self.certification in WATER_REPELLENT_RULES['equivalent_treatments']
    
    def get_quality_rank(self) -> int:
        """Ritorna rank qualità colore (1=migliore, 4=peggiore)"""
        if self.color in COLOR_CODES:
            return COLOR_CODES[self.color]['quality_rank']
        return 999


class CompatibilityManager:
    """Gestisce tutte le regole di compatibilità per l'ottimizzazione"""
    
    def __init__(self):
        self.species_rules = SPECIES_COMPATIBILITY
        self.color_matrix = COLOR_COMPATIBILITY_MATRIX
        self.wr_rules = WATER_REPELLENT_RULES
    
    def check_material_state_compatibility(
        self,
        product: ProductCode,
        dc_target: Optional[float]
    ) -> Tuple[bool, Optional[str]]:
        """
        Verifica compatibilità stato materiale con DC target
        
        Returns:
            (compatible, reason)
        """
        if not product.state or product.state not in MATERIAL_STATE_CODES:
            return False, "Stato materiale sconosciuto"
        
        state_info = MATERIAL_STATE_CODES[product.state]
        
        # P-type: sempre utilizzabile
        if product.state == 'P':
            return True, None
        
        # M-type: solo per DC ≤50%
        if product.state == 'M':
            if dc_target is not None and dc_target > 50:
                return False, f"M-type non utilizzabile per DC target {dc_target}% (>50%)"
            return True, None
        
        # S-type: solo per DC molto basso
        if product.state == 'S':
            if dc_target is not None and dc_target > 30:
                return False, f"S-type non utilizzabile per DC target {dc_target}% (>30%)"
            return True, None
        
        # O-type: casi speciali
        if product.state == 'O':
            return False, "O-type non utilizzabile per miscele standard"
        
        return True, None
    
    def check_species_compatibility(
        self,
        lot_species: str,
        blend_species: str,
        duck_target: Optional[float] = None
    ) -> Tuple[bool, float]:
        """
        Verifica compatibilità specie e calcola penalità
        
        Returns:
            (compatible, penalty_score)
        """
        # Miscele anatra: NO oca pura
        if blend_species == 'A':
            if lot_species == 'O':
                return False, SPECIES_COMPATIBILITY['duck_blend']['penalties']['using_O_in_duck']
            return True, 0
        
        # Miscele oca: strategia basata su duck target
        if blend_species == 'O':
            # Se c'è duck target, preferire misti OA
            if duck_target and duck_target > 0:
                if lot_species == 'OA':
                    # PREFERIBILE: misto per raggiungere duck target
                    return True, SPECIES_COMPATIBILITY['goose_blend_with_duck_target']['penalties']['using_OA_in_goose']
                elif lot_species == 'A':
                    # ACCETTABILE: anatra pura se necessario
                    return True, SPECIES_COMPATIBILITY['goose_blend_with_duck_target']['penalties']['using_A_in_goose']
                elif lot_species == 'O':
                    # OK: oca pura
                    return True, 0
            else:
                # Nessun duck target: preferire oca pura
                if lot_species == 'O':
                    return True, 0
                elif lot_species == 'OA':
                    return True, -30  # Penalità lieve
                elif lot_species == 'A':
                    return True, -100  # Penalità media
        
        # Misti OA: accettano tutto
        if blend_species == 'OA':
            return True, 0
        
        return True, 0
    
    def check_color_compatibility(
        self,
        lot_color: str,
        blend_color: str
    ) -> Tuple[bool, float]:
        """
        Verifica compatibilità colore e calcola penalità
        
        Returns:
            (compatible, penalty_score)
        """
        if lot_color not in self.color_matrix:
            return False, -10000
        
        if blend_color not in self.color_matrix[lot_color]:
            return False, -10000
        
        penalty = self.color_matrix[lot_color][blend_color]
        
        # Se penalità è altissima (-10000), è incompatibile
        if penalty <= -10000:
            return False, penalty
        
        return True, penalty
    
    def check_water_repellent_compatibility(
        self,
        lot_is_wr: bool,
        blend_requires_wr: bool,
        allow_mixing: bool = False
    ) -> bool:
        """
        Verifica compatibilità water repellent
        
        Args:
            lot_is_wr: Il lotto ha trattamento WR?
            blend_requires_wr: La miscela richiede WR?
            allow_mixing: Permetti mixing WR con normali?
        """
        # Miscela richiede WR
        if blend_requires_wr:
            if lot_is_wr:
                return True  # WR per miscela WR: OK
            else:
                return allow_mixing  # Normale per miscela WR: solo se mixing permesso
        
        # Miscela non richiede WR
        else:
            if lot_is_wr:
                return allow_mixing  # WR per miscela normale: solo se mixing permesso
            else:
                return True  # Normale per miscela normale: OK
    
    def calculate_duck_content_score(
        self,
        actual_duck: float,
        duck_target: Optional[float],
        duck_tolerance: float = 5.0
    ) -> float:
        """
        Calcola score basato su duck content vs target
        CRITICO per ottimizzazione economica
        
        Returns:
            score (più alto = migliore)
        """
        if duck_target is None:
            return 0
        
        deviation = abs(actual_duck - duck_target)
        score = 0
        
        # CRITICO: Forte penalità se sotto target (spreco denaro)
        if actual_duck < (duck_target - duck_tolerance):
            penalty_factor = (duck_target - actual_duck) / duck_target
            score -= 500 * penalty_factor
        
        # Penalità media se sopra target
        elif actual_duck > (duck_target + duck_tolerance):
            penalty_factor = (actual_duck - duck_target) / duck_target
            score -= 200 * penalty_factor
        
        # Bonus se nel range ottimale
        else:
            bonus_factor = 1 - (deviation / duck_tolerance)
            score += 600 * bonus_factor
        
        return score
    
    def get_species_mixing_strategy(
        self,
        blend_species: str,
        duck_target: Optional[float]
    ) -> Dict[str, any]:
        """
        Ritorna strategia di mixing ottimale per specie
        """
        if blend_species == 'O' and duck_target and duck_target > 0:
            return {
                'strategy': 'optimize_duck_target',
                'preferred_order': ['OA', 'O', 'A'],
                'reasoning': f'Prioritizzare misti OA per raggiungere duck target {duck_target}%',
                'penalties': SPECIES_COMPATIBILITY['goose_blend_with_duck_target']['penalties']
            }
        elif blend_species == 'O':
            return {
                'strategy': 'maximize_quality',
                'preferred_order': ['O', 'OA', 'A'],
                'reasoning': 'Nessun duck target: preferire oca pura per massimizzare qualità',
                'penalties': {'using_A': -100}
            }
        elif blend_species == 'A':
            return {
                'strategy': 'duck_only',
                'preferred_order': ['A', 'OA'],
                'reasoning': 'Miscela anatra: no oca pura',
                'penalties': {'using_O': -1000}
            }
        else:
            return {
                'strategy': 'mixed',
                'preferred_order': ['OA', 'O', 'A'],
                'reasoning': 'Miscela mista: tutti accettabili',
                'penalties': {}
            }


def parse_product_code(code: str) -> ProductCode:
    """Helper function per creare ProductCode da stringa"""
    return ProductCode(raw_code=code)


def is_compatible_combination(
    lot_codes: List[str],
    requirements: Dict
) -> Tuple[bool, List[str]]:
    """
    Verifica se una combinazione di lotti è compatibile
    
    Returns:
        (compatible, list_of_reasons)
    """
    manager = CompatibilityManager()
    reasons = []
    
    products = [parse_product_code(code) for code in lot_codes]
    
    # Verifica validità codici
    for p in products:
        if not p.is_valid():
            reasons.append(f"Codice invalido: {p.raw_code}")
            return False, reasons
    
    # Verifica compatibilità colori
    blend_color = requirements.get('color')
    if blend_color:
        for p in products:
            compatible, _ = manager.check_color_compatibility(p.color, blend_color)
            if not compatible:
                reasons.append(f"Colore {p.color} incompatibile con {blend_color}")
    
    # Verifica compatibilità specie
    blend_species = requirements.get('species')
    duck_target = requirements.get('duck_target')
    if blend_species:
        for p in products:
            compatible, _ = manager.check_species_compatibility(
                p.species, blend_species, duck_target
            )
            if not compatible:
                reasons.append(f"Specie {p.species} incompatibile con {blend_species}")
    
    # Se ci sono ragioni di incompatibilità, ritorna False
    if reasons:
        return False, reasons
    
    return True, ["Combinazione compatibile"]
