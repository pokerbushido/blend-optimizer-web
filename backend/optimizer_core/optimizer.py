"""
OPTIMIZER v3.3 - Blend Optimization Engine
Algoritmo di ottimizzazione miscele con scoring multi-criterio

v3.3.8 - Esclusione materiali grezzi:
- Filtro automatico materiali grezzi (group='G') dalle miscele
- Solo prodotti finiti ammessi come candidati

v3.3.6 - Preservazione materiali premium:
- Ordinamento candidati con penalità DC overqualification
- Preservazione automatica lotti con duck basso (<50% target)
- Range accettabile duck: 50-200% del target
"""

import itertools
import numpy as np
import random  # FIX v3.3.5: per diversificazione soluzioni
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from inventory import LotData, InventoryManager
from compatibility import CompatibilityManager, parse_product_code
from config import (
    SCORING_WEIGHTS,
    DEFAULT_TOLERANCES,
    OPERATIONAL_LIMITS,
    SEARCH_PARAMS
)


@dataclass
class BlendSolution:
    """Rappresenta una soluzione di miscela"""
    lots: List[Tuple[LotData, float]]  # (lot, kg_used)
    requirements: Dict
    
    # Metriche calcolate
    total_kg: float = 0
    dc_average: float = 0
    fp_average: float = 0
    duck_average: float = 0
    oe_average: float = 0
    feather_average: float = 0
    
    total_cost: float = 0
    cost_per_kg: float = 0
    
    # Scoring
    score: float = 0
    score_breakdown: Dict = field(default_factory=dict)
    
    # Conformità
    meets_dc_target: bool = False
    meets_fp_target: bool = False
    meets_duck_target: bool = False
    meets_oe_target: bool = False

    def __post_init__(self):
        """Calcola metriche dopo inizializzazione"""
        self._calculate_metrics()
        self._check_conformity()
    
    def _calculate_metrics(self):
        """Calcola tutte le metriche della miscela"""
        if not self.lots:
            return

        self.total_kg = sum(kg for _, kg in self.lots)

        if self.total_kg == 0:
            return

        # Medie ponderate - CORRETTO: dividere per kg con valore non-None

        # DC average
        dc_kg_total = sum(kg for lot, kg in self.lots if lot.dc_real is not None)
        if dc_kg_total > 0:
            self.dc_average = sum(
                lot.dc_real * kg for lot, kg in self.lots if lot.dc_real is not None
            ) / dc_kg_total
        else:
            self.dc_average = 0

        # FP average
        fp_kg_total = sum(kg for lot, kg in self.lots if lot.fp_real is not None)
        if fp_kg_total > 0:
            self.fp_average = sum(
                lot.fp_real * kg for lot, kg in self.lots if lot.fp_real is not None
            ) / fp_kg_total
        else:
            self.fp_average = 0

        # Duck average
        duck_kg_total = sum(kg for lot, kg in self.lots if lot.duck_real is not None)
        if duck_kg_total > 0:
            self.duck_average = sum(
                lot.duck_real * kg for lot, kg in self.lots if lot.duck_real is not None
            ) / duck_kg_total
        else:
            self.duck_average = 0

        # OE average
        oe_kg_total = sum(kg for lot, kg in self.lots if lot.other_elements_real is not None)
        if oe_kg_total > 0:
            self.oe_average = sum(
                lot.other_elements_real * kg for lot, kg in self.lots
                if lot.other_elements_real is not None
            ) / oe_kg_total
        else:
            self.oe_average = 0

        # Feather average
        feather_kg_total = sum(kg for lot, kg in self.lots if lot.feather_real is not None)
        if feather_kg_total > 0:
            self.feather_average = sum(
                lot.feather_real * kg for lot, kg in self.lots
                if lot.feather_real is not None
            ) / feather_kg_total
        else:
            self.feather_average = 0

        # Costi
        self.total_cost = sum(
            lot.cost_per_kg * kg for lot, kg in self.lots
            if lot.cost_per_kg is not None
        )

        if self.total_kg > 0:
            self.cost_per_kg = self.total_cost / self.total_kg
    
    def _check_conformity(self):
        """Verifica conformità ai target"""
        req = self.requirements

        # DC target
        if 'dc_target' in req and req['dc_target'] is not None:
            tolerance = req.get('dc_tolerance', DEFAULT_TOLERANCES['dc_tolerance'])
            self.meets_dc_target = abs(self.dc_average - req['dc_target']) <= tolerance
        else:
            self.meets_dc_target = True

        # FP target
        if 'fp_target' in req and req['fp_target'] is not None:
            tolerance = req.get('fp_tolerance', DEFAULT_TOLERANCES['fp_tolerance'])
            self.meets_fp_target = abs(self.fp_average - req['fp_target']) <= tolerance
        else:
            self.meets_fp_target = True

        # Duck target
        if 'duck_target' in req and req['duck_target'] is not None:
            tolerance = req.get('duck_tolerance', DEFAULT_TOLERANCES['duck_tolerance'])
            self.meets_duck_target = abs(self.duck_average - req['duck_target']) <= tolerance
        else:
            self.meets_duck_target = True

        # OE max (maximum constraint, not target)
        if 'max_oe' in req and req['max_oe'] is not None:
            self.meets_oe_target = self.oe_average <= req['max_oe']
        else:
            self.meets_oe_target = True
    
    def is_valid(self) -> bool:
        """Verifica se la soluzione è valida"""
        # FIX v3.3.5: Aggiungi controllo quantità minima richiesta
        target_kg = self.requirements.get('quantity_kg', 100)
        min_acceptable = target_kg * 0.9  # Almeno 90% della quantità richiesta

        return all([
            self.meets_dc_target,
            self.meets_fp_target,
            self.meets_duck_target,
            self.meets_oe_target,
            self.total_kg >= min_acceptable,  # FIX: era solo > 0, ora richiede >= 90% target
            len(self.lots) > 0
        ])
    
    def get_summary(self) -> Dict:
        """Ritorna riepilogo soluzione"""
        return {
            'num_lots': len(self.lots),
            'total_kg': round(self.total_kg, 2),
            'dc_average': round(self.dc_average, 2),
            'fp_average': round(self.fp_average, 2),
            'duck_average': round(self.duck_average, 2),
            'oe_average': round(self.oe_average, 2),
            'total_cost': round(self.total_cost, 2),
            'cost_per_kg': round(self.cost_per_kg, 2),
            'score': round(self.score, 2),
            'meets_dc': self.meets_dc_target,
            'meets_fp': self.meets_fp_target,
            'meets_duck': self.meets_duck_target,
            'meets_oe': self.meets_oe_target,
            'valid': self.is_valid()
        }


class BlendOptimizer:
    """Motore di ottimizzazione miscele"""
    
    def __init__(self, inventory: InventoryManager):
        self.inventory = inventory
        self.compatibility = CompatibilityManager()
    
    def optimize(
        self,
        requirements: Dict,
        num_solutions: int = 3,
        allow_estimated: bool = False
    ) -> List[BlendSolution]:
        """
        Ottimizza miscela secondo requisiti

        Args:
            requirements: Dict con parametri richiesta
            num_solutions: Numero soluzioni da ritornare
            allow_estimated: Permetti uso dati stimati

        Returns:
            Lista di BlendSolution ordinate per score
        """
        # Step 1: Filtra candidati
        candidates = self._filter_candidates(requirements, allow_estimated)

        if not candidates:
            return []

        # Step 2: Genera combinazioni DIVERSE (FIX v3.3.5: usa strategie multiple)
        combinations = self._generate_combinations_diverse(candidates, requirements, num_solutions)

        if not combinations:
            return []

        # Step 3: Calcola score per ogni combinazione con EARLY STOPPING
        # Ottimizzazione: smette quando ha trovato abbastanza ottime soluzioni
        solutions = []
        early_stop_threshold = num_solutions * 10  # Cerca 10x le soluzioni richieste

        for i, combo in enumerate(combinations[:SEARCH_PARAMS['max_combinations']]):
            # Quick validation PRIMA di calcolare score completo
            if not self._quick_validate_combination(combo, requirements):
                continue

            solution = self._evaluate_combination(combo, requirements)
            if solution and solution.is_valid():
                solutions.append(solution)

                # Early stopping: se ha già trovato molte ottime soluzioni, ferma
                if len(solutions) >= early_stop_threshold:
                    print(f"  [Early Stop] Trovate {len(solutions)} soluzioni valide dopo {i+1}/{len(combinations)} combinazioni")
                    break

        # Step 4: Ordina per score e ritorna top N
        solutions.sort(key=lambda s: s.score, reverse=True)

        return solutions[:num_solutions]

    def _calculate_duck_penalty(self, duck_real: Optional[float], duck_target: Optional[float]) -> float:
        """
        Calcola penalità per contenuto duck con preservazione materiali preziosi

        Logica:
        - Duck < 50% target → TROPPO PREZIOSO, preserva (penalità per evitare uso)
        - Duck tra 50% e 200% target → ACCETTABILE, usa (penalità 0)
        - Duck > 200% target → SPRECO, evita (penalità crescente)

        Args:
            duck_real: Percentuale duck reale del lotto
            duck_target: Percentuale duck target della miscela

        Returns:
            float: Penalità (0 = ideale, >0 = da evitare)
        """
        if duck_target is None or duck_real is None:
            return 0

        # Range accettabile: fino a 2x il target
        # Es: target 15% → accettabile fino a 30%
        acceptable_upper = duck_target * 2.0

        # Soglia preservazione: sotto 50% del target
        # Es: target 15% → preserva lotti sotto 7.5%
        preservation_threshold = duck_target * 0.5

        if duck_real < preservation_threshold:
            # Troppo prezioso (duck troppo basso) → alta penalità per preservare
            return (preservation_threshold - duck_real) ** 2.0

        elif duck_real <= acceptable_upper:
            # Nel range accettabile [50% target, 200% target] → USABILE
            return 0

        else:
            # Troppo alto (spreco) → penalità crescente
            excess = duck_real - acceptable_upper
            return excess ** 2.0

    def _filter_candidates(
        self,
        requirements: Dict,
        allow_estimated: bool
    ) -> List[LotData]:
        """
        Filtra lotti candidati secondo requisiti

        Approccio FLESSIBILE basato su valori reali:
        - Usa species/color del codice come filtro iniziale ampio
        - Affina usando valori reali dei lotti (duck_real, dc_real)
        - Accetta lotti "vicini" che hanno parametri reali compatibili
        """

        # Parametri base
        species_target = requirements.get('species')
        color_target = requirements.get('color')
        dc_target = requirements.get('dc_target')
        duck_target = requirements.get('duck_target')
        min_qty = OPERATIONAL_LIMITS['min_lot_usage_kg']

        # Range DC espanso per ricerca iniziale
        min_dc = None
        max_dc = None
        if dc_target is not None:
            range_pct = SEARCH_PARAMS['initial_dc_range']
            min_dc = max(0, dc_target - range_pct)
            max_dc = min(100, dc_target + range_pct)

        # Gestione water repellent
        exclude_wr = True
        if requirements.get('water_repellent'):
            exclude_wr = False

        # FILTRO INIZIALE AMPIO (senza species/color rigidi)
        # Prendiamo tutti i lotti e filtriamo manualmente
        all_candidates = self.inventory.filter_lots(
            species=None,  # NON filtrare per specie inizialmente
            color=None,    # NON filtrare per colore inizialmente
            min_dc=min_dc,
            max_dc=max_dc,
            min_qty=min_qty,
            exclude_water_repellent=exclude_wr,
            exclude_raw_materials=True,  # Esclude materiali grezzi (group='G')
            allow_estimated=allow_estimated
        )

        # FILTRO INTELLIGENTE basato su valori reali
        filtered = []
        for lot in all_candidates:
            # 1. Check compatibilità stato materiale
            compatible, reason = self.compatibility.check_material_state_compatibility(
                lot.product, dc_target
            )
            if not compatible:
                continue

            # 2. Filtro SPECIE basato su DUCK_REAL (approccio flessibile)
            if species_target:
                if not self._is_species_compatible_flexible(lot, species_target, duck_target):
                    continue

            # 3. Filtro COLORE basato su famiglia colore (approccio flessibile)
            if color_target:
                if not self._is_color_compatible_flexible(lot, color_target):
                    continue

            filtered.append(lot)

        # Ordina con PRESERVAZIONE MATERIALI PREMIUM (v3.3.6)
        # 1. Priorità 1: Penalità duck (preserva lotti con duck basso)
        # 2. Priorità 2: Penalità DC overqualification (preserva lotti con DC alto)
        # 3. Priorità 3: Quality score (smaltimento lotti brutti)
        # 4. Priorità 4: Costo
        #
        # LOGICA v3.3.6:
        # - Preserva materiali premium (DC alto, duck basso) per miscele future più esigenti
        # - Usa preferibilmente materiali "adatti" al target corrente
        # - Evita spreco di valore di opportunità

        if dc_target is not None:
            # Ordinamento con preservazione materiali premium
            duck_target = requirements.get('duck_target')

            filtered.sort(
                key=lambda l: (
                    # PRIORITÀ 1: Penalità duck (preserva lotti con duck basso)
                    self._calculate_duck_penalty(l.duck_real, duck_target),

                    # PRIORITÀ 2: Penalità DC overqualification
                    # Solo lotti SOPRA target sono penalizzati (preservati)
                    # Lotti sotto/al target hanno penalità 0 (preferiti)
                    max(0, l.dc_real - dc_target) ** 1.5 if l.dc_real is not None else 999,

                    # PRIORITÀ 3: Quality score (smaltimento lotti brutti)
                    -l.calculate_quality_score(),

                    # PRIORITÀ 4: Costo
                    l.cost_per_kg if l.cost_per_kg is not None else 999
                )
            )
        else:
            # Senza DC target: ordina per quality score (smaltimento) e costo
            filtered.sort(
                key=lambda l: (
                    -l.calculate_quality_score(),
                    l.cost_per_kg if l.cost_per_kg is not None else 999
                )
            )

        return filtered

    def _is_species_compatible_flexible(
        self,
        lot: 'LotData',
        species_target: str,
        duck_target: Optional[float]
    ) -> bool:
        """
        Verifica compatibilità specie in modo FLESSIBILE usando duck_real

        Per ANATRA:
        - Accetta lotti con duck_real > 80% (anche se codice dice "OA")
        - Blocca lotti con duck_real < 50%

        Per OCA:
        - Se c'è duck_target, accetta lotti con duck_real compatibile
        - Blocca lotti con duck_real > 95% (troppo anatra)

        Per MISTI (OA):
        - Accetta qualsiasi duck_real
        """
        lot_species = lot.product.species
        duck_real = lot.duck_real if lot.duck_real is not None else 0

        # Miscele ANATRA
        if species_target == 'A':
            # Blocco ASSOLUTO: no oca pura con duck basso
            if lot_species == 'O' and duck_real < 15:
                return False
            # Preferenza: duck_real alto
            if duck_real >= 80:
                return True  # Anatra pura o quasi
            if duck_real >= 50:
                return True  # Accettabile misto con prevalenza anatra
            if lot_species == 'A':
                return True  # Codice dice anatra, ok anche se duck_real basso
            return False

        # Miscele OCA
        elif species_target == 'O':
            # Se richiesto duck_target, verifica compatibilità
            if duck_target is not None and duck_target > 0:
                # Accetta lotti che aiutano a raggiungere il target
                if duck_real <= duck_target + 30:  # Range ampio
                    return True
                return False
            else:
                # Nessun duck target: preferire duck basso
                if duck_real > 95:
                    return False  # Troppo anatra
                return True

        # Miscele MISTE (OA)
        elif species_target == 'OA':
            return True  # Accetta tutto

        # Se specie nel codice matcha, ok
        if lot_species == species_target:
            return True

        # Default: no
        return False

    def _is_color_compatible_flexible(
        self,
        lot: 'LotData',
        color_target: str
    ) -> bool:
        """
        Verifica compatibilità colore in modo FLESSIBILE

        Accetta varianti dello stesso colore base:
        - Se target è "B", accetta B, BPW, BNPW, B.FM, etc.
        - Se target è "G", accetta G, G.CINA, G.FM, etc.
        - Se target è "BPW", accetta solo BPW e PW (no B standard)
        """
        lot_color = lot.product.color
        if not lot_color:
            return False

        # Match esatto
        if lot_color == color_target:
            return True

        # Estrai colore base (primo carattere o primi 2-3 char)
        def get_base_color(color_str):
            if not color_str:
                return None
            # Se contiene punto, prendi parte prima
            if '.' in color_str:
                color_str = color_str.split('.')[0]
            # Rimuovi suffissi comuni
            color_str = color_str.replace('PW', '').replace('NPW', '')
            return color_str[0] if color_str else None

        target_base = get_base_color(color_target)
        lot_base = get_base_color(lot_color)

        # Se basi coincidono, ok
        if target_base and lot_base and target_base == lot_base:
            # ECCETTO: se target richiede PW, non accettare B standard
            if 'PW' in color_target and 'PW' not in lot_color:
                # Target vuole Pure White, lotto è solo Bianco standard
                # Accettabile con penalità (gestita nello scoring)
                return True
            return True

        return False

    def _quick_validate_combination(
        self,
        combo: List[Tuple[LotData, float]],
        requirements: Dict
    ) -> bool:
        """
        Validazione veloce per scartare combinazioni ovviamente invalide
        PRIMA di calcolare score completo (ottimizzazione performance)

        Returns:
            True se combinazione potenzialmente valida, False altrimenti
        """
        if not combo:
            return False

        # Calcola medie pesate rapide
        total_kg = sum(kg for _, kg in combo)
        target_kg = requirements.get('quantity_kg', 100)

        # Scarta se quantità troppo lontana dal target (±30%)
        if total_kg < target_kg * 0.7 or total_kg > target_kg * 1.3:
            return False

        # Quick check DC (solo media, senza toleranze strette)
        dc_target = requirements.get('dc_target')
        if dc_target:
            dc_avg = sum(lot.dc_real * kg for lot, kg in combo if lot.dc_real) / total_kg
            # Range molto ampio (±10%) per non scartare combinazioni buone
            if abs(dc_avg - dc_target) > 10:
                return False

        return True

    def _generate_combinations_diverse(
        self,
        candidates: List[LotData],
        requirements: Dict,
        num_solutions: int = 3
    ) -> List[List[Tuple[LotData, float]]]:
        """
        FIX v3.3.5: Genera combinazioni DIVERSE usando strategie multiple
        con EARLY STOPPING per performance

        PROBLEMA RISOLTO: Le soluzioni erano troppo simili perché l'algoritmo
        era completamente deterministico e usava sempre lo stesso ordinamento.

        SOLUZIONE: Applica 4 strategie diverse per esplorare lo spazio delle soluzioni:
        1. Ordinamento per vicinanza al DC target (strategia originale)
        2. Ordinamento per COSTO (cerca soluzioni economiche)
        3. Ordinamento per QUANTITÀ disponibile (usa lotti grossi)
        4. Randomizzazione (esplora combinazioni casuali)

        OTTIMIZZAZIONE v3.3.8: Early stopping se ha già generato molte combinazioni

        Returns:
            Lista combinata di combinazioni diverse
        """
        all_combinations = []
        target_combinations = num_solutions * 5000  # Genera 5000x le soluzioni richieste

        # Strategia 1: Ordinamento DC (attuale - già ordinati così)
        print("  [Diversificazione] Strategia 1: Vicinanza DC target")
        combo1 = self._generate_combinations(candidates, requirements)
        all_combinations.extend(combo1)
        print(f"    → {len(combo1)} combinazioni")

        # Early stop se già abbastanza
        if len(all_combinations) >= target_combinations:
            print(f"  [Early Stop] Già {len(all_combinations)} combinazioni, skip strategie successive")
            return self._deduplicate_combinations(all_combinations)

        # Strategia 2: Ordinamento COSTO (preferisci materiali economici)
        print("  [Diversificazione] Strategia 2: Minimizzazione costo")
        candidates_by_cost = sorted(
            candidates,
            key=lambda l: l.cost_per_kg if l.cost_per_kg is not None else 999
        )
        combo2 = self._generate_combinations(candidates_by_cost[:300], requirements)
        all_combinations.extend(combo2)
        print(f"    → {len(combo2)} combinazioni")

        if len(all_combinations) >= target_combinations:
            print(f"  [Early Stop] Già {len(all_combinations)} combinazioni, skip strategie successive")
            return self._deduplicate_combinations(all_combinations)

        # Strategia 3: Ordinamento QUANTITÀ (usa lotti grossi per raggiungere target)
        print("  [Diversificazione] Strategia 3: Lotti con maggior quantità disponibile")
        candidates_by_qty = sorted(
            candidates,
            key=lambda l: -l.qty_available  # Ordine decrescente
        )
        combo3 = self._generate_combinations(candidates_by_qty[:300], requirements)
        all_combinations.extend(combo3)
        print(f"    → {len(combo3)} combinazioni")

        if len(all_combinations) >= target_combinations:
            print(f"  [Early Stop] Già {len(all_combinations)} combinazioni, skip random")
            return self._deduplicate_combinations(all_combinations)

        # Strategia 4: Randomizzazione (fino a 2 tentativi, con early stop)
        print("  [Diversificazione] Strategia 4: Randomizzazione (max 2 tentativi)")
        for i in range(2):
            if len(all_combinations) >= target_combinations:
                print(f"    → Skip tentativo {i+1}: già abbastanza combinazioni")
                break

            shuffled = candidates.copy()
            random.shuffle(shuffled)
            combo_rand = self._generate_combinations(shuffled[:200], requirements)
            all_combinations.extend(combo_rand)
            print(f"    → Tentativo {i+1}: {len(combo_rand)} combinazioni")

        return self._deduplicate_combinations(all_combinations)

    def _deduplicate_combinations(self, combinations: List) -> List:
        """Rimuove combinazioni duplicate"""
        print(f"  [Totale] {len(combinations)} combinazioni generate (con duplicati)")

        unique_combinations = []
        seen_lot_sets = set()

        for combo in combinations:
            # Crea signature univoca basata sui lotti usati
            lot_codes = tuple(sorted([lot.lot_code for lot, _ in combo]))
            if lot_codes not in seen_lot_sets:
                seen_lot_sets.add(lot_codes)
                unique_combinations.append(combo)

        print(f"  [Uniche] {len(unique_combinations)} combinazioni dopo rimozione duplicati")
        return unique_combinations

    def _generate_combinations(
        self,
        candidates: List[LotData],
        requirements: Dict
    ) -> List[List[Tuple[LotData, float]]]:
        """
        Genera combinazioni intelligenti di lotti
        
        Returns:
            Lista di combinazioni, dove ogni combinazione è
            lista di (LotData, kg_to_use)
        """
        target_kg = requirements.get('quantity_kg', 100)
        max_lots = requirements.get('max_lots', OPERATIONAL_LIMITS['max_lots_per_blend'])
        
        combinations = []

        # Strategia 1: Combinazioni con numero variabile di lotti (2 fino a max_lots)
        # Inizia con pochi lotti e incrementa gradualmente
        max_candidates_to_try = min(300, len(candidates))  # FIX v3.3.5: 300 candidati (era 100)

        for n_lots in range(2, max_lots + 1):  # RIMOSSO limite min(6, ...)
            # Limita numero combinazioni per evitare esplosione computazionale
            # Per tanti lotti (>6), usa meno candidati
            if n_lots <= 5:
                candidate_pool = candidates[:max_candidates_to_try]  # 300
            elif n_lots <= 7:
                candidate_pool = candidates[:200]  # FIX v3.3.5: 200 (era 60)
            else:
                candidate_pool = candidates[:150]  # FIX v3.3.5: 150 (era 40)

            for lot_combo in itertools.combinations(candidate_pool, n_lots):
                # Calcola kg ottimali per ogni lotto
                allocation = self._calculate_optimal_allocation(
                    list(lot_combo), target_kg, requirements
                )
                if allocation:
                    combinations.append(allocation)

                # Limite sicurezza per evitare troppi calcoli
                if len(combinations) >= SEARCH_PARAMS['max_combinations']:
                    break

            if len(combinations) >= SEARCH_PARAMS['max_combinations']:
                break

        # Strategia 2: Combinazioni greedy (aggiungi lotti fino a target)
        for start_lot in candidates[:100]:  # FIX v3.3.5: 100 tentativi greedy (era 30)
            combo = self._greedy_combination(
                start_lot, candidates, target_kg, requirements, max_lots
            )
            if combo:
                combinations.append(combo)
        
        return combinations
    
    def _calculate_optimal_allocation(
        self,
        lots: List[LotData],
        target_kg: float,
        requirements: Dict
    ) -> Optional[List[Tuple[LotData, float]]]:
        """
        Calcola allocazione ottimale kg per lista di lotti
        Obiettivo: raggiungere target_kg rispettando DC target

        VERSIONE v3.3.4: Algoritmo intelligente che bilancia i lotti
        per raggiungere il DC target usando ottimizzazione iterativa
        """
        if not lots:
            return None

        dc_target = requirements.get('dc_target')

        # Se non c'è DC target, usa allocazione semplice
        if dc_target is None:
            return self._simple_allocation(lots, target_kg)

        # Filtra lotti con DC valido
        valid_lots = [l for l in lots if l.dc_real is not None]
        if not valid_lots:
            return None

        # ALGORITMO ITERATIVO per bilanciare verso DC target
        # Strategia: alloca proporzioni che minimizzano distanza da DC target

        # Calcola DC medio e range
        dc_values = [l.dc_real for l in valid_lots]
        dc_min = min(dc_values)
        dc_max = max(dc_values)

        # Se tutti i lotti hanno DC simile, alloca uniformemente
        if dc_max - dc_min < 2:
            return self._uniform_allocation(valid_lots, target_kg)

        # Se DC target è fuori range, usa allocazione semplice
        if dc_target < dc_min - 5 or dc_target > dc_max + 5:
            return self._simple_allocation(valid_lots, target_kg)

        # Alloca usando ottimizzazione iterativa
        best_allocation = None
        best_dc_diff = 999

        # Prova diverse strategie di allocazione
        for strategy in ['balanced', 'weighted', 'greedy']:
            allocation = self._allocate_with_strategy(
                valid_lots, target_kg, dc_target, strategy
            )

            if allocation:
                # Calcola DC risultante
                total = sum(qty for _, qty in allocation)
                if total > 0:
                    dc_result = sum(lot.dc_real * qty for lot, qty in allocation) / total
                    dc_diff = abs(dc_result - dc_target)

                    # Se migliore, salva
                    if dc_diff < best_dc_diff:
                        best_dc_diff = dc_diff
                        best_allocation = allocation

        return best_allocation

    def _allocate_with_strategy(
        self,
        lots: List[LotData],
        target_kg: float,
        dc_target: float,
        strategy: str
    ) -> Optional[List[Tuple[LotData, float]]]:
        """Alloca kg usando una specifica strategia"""

        if strategy == 'balanced':
            # Strategia bilanciata: proporzioni per raggiungere DC target
            return self._balanced_allocation(lots, target_kg, dc_target)

        elif strategy == 'weighted':
            # Strategia pesata: più kg ai lotti vicini al target
            return self._weighted_allocation_v2(lots, target_kg, dc_target)

        elif strategy == 'greedy':
            # Strategia greedy: inizia con lotto più vicino e bilancia
            return self._greedy_balanced_allocation(lots, target_kg, dc_target)

        return None

    def _balanced_allocation(
        self,
        lots: List[LotData],
        target_kg: float,
        dc_target: float
    ) -> Optional[List[Tuple[LotData, float]]]:
        """
        Allocazione bilanciata per raggiungere DC target
        Usa approccio iterativo per trovare proporzioni ottimali
        """
        n_lots = len(lots)
        if n_lots == 0:
            return None

        # Inizia con proporzioni uguali
        proportions = [1.0 / n_lots] * n_lots

        # Ottimizzazione iterativa (max 50 iterazioni)
        for iteration in range(50):
            # Calcola DC risultante con proporzioni correnti
            dc_result = sum(lots[i].dc_real * proportions[i] for i in range(n_lots))

            # Se abbastanza vicino, esci
            if abs(dc_result - dc_target) < 0.1:
                break

            # Aggiusta proporzioni per avvicinarsi al target
            # Se DC troppo alto, aumenta lotti con DC basso
            # Se DC troppo basso, aumenta lotti con DC alto
            if dc_result > dc_target:
                # Serve più DC basso
                for i in range(n_lots):
                    if lots[i].dc_real < dc_target:
                        proportions[i] *= 1.1
                    elif lots[i].dc_real > dc_target:
                        proportions[i] *= 0.9
            else:
                # Serve più DC alto
                for i in range(n_lots):
                    if lots[i].dc_real > dc_target:
                        proportions[i] *= 1.1
                    elif lots[i].dc_real < dc_target:
                        proportions[i] *= 0.9

            # Normalizza proporzioni
            total_prop = sum(proportions)
            if total_prop > 0:
                proportions = [p / total_prop for p in proportions]

        # Converti proporzioni in kg
        allocation = []
        for i, lot in enumerate(lots):
            kg = target_kg * proportions[i]
            max_usable = lot.qty_available * 0.95

            # Rispetta disponibilità
            if kg > max_usable:
                kg = max_usable

            # Rispetta minimo
            if kg >= OPERATIONAL_LIMITS['min_lot_usage_kg']:
                allocation.append((lot, kg))

        # Verifica quantità totale
        total = sum(qty for _, qty in allocation)
        if total < target_kg * 0.9:  # FIX v3.3.5: soglia 90% invece di 70%
            return None

        return allocation if allocation else None

    def _weighted_allocation_v2(
        self,
        lots: List[LotData],
        target_kg: float,
        dc_target: float
    ) -> Optional[List[Tuple[LotData, float]]]:
        """Allocazione pesata basata su vicinanza al DC target"""

        # Calcola pesi (più peso = più vicino al target)
        weights = []
        for lot in lots:
            distance = abs(lot.dc_real - dc_target)
            # Peso inversamente proporzionale alla distanza
            weight = 1.0 / (1.0 + distance / 10.0)
            weights.append(weight)

        # Normalizza pesi
        total_weight = sum(weights)
        if total_weight == 0:
            return None

        proportions = [w / total_weight for w in weights]

        # Alloca kg
        allocation = []
        for i, lot in enumerate(lots):
            kg = target_kg * proportions[i]
            max_usable = lot.qty_available * 0.95

            if kg > max_usable:
                kg = max_usable

            if kg >= OPERATIONAL_LIMITS['min_lot_usage_kg']:
                allocation.append((lot, kg))

        total = sum(qty for _, qty in allocation)
        if total < target_kg * 0.9:  # FIX v3.3.5: soglia 90% invece di 70%
            return None

        return allocation if allocation else None

    def _greedy_balanced_allocation(
        self,
        lots: List[LotData],
        target_kg: float,
        dc_target: float
    ) -> Optional[List[Tuple[LotData, float]]]:
        """Allocazione greedy con bilanciamento"""

        # Ordina per vicinanza al target
        sorted_lots = sorted(lots, key=lambda l: abs(l.dc_real - dc_target))

        allocation = []
        remaining = target_kg
        current_dc = 0

        for lot in sorted_lots:
            if remaining <= 0:
                break

            # Calcola quanto allocare
            if len(allocation) == 0:
                # Primo lotto: usa circa 40-60% del target
                kg = min(remaining * 0.5, lot.qty_available * 0.95)
            else:
                # Lotti successivi: bilancia per raggiungere DC target
                current_dc = sum(l.dc_real * q for l, q in allocation) / sum(q for _, q in allocation)

                if abs(current_dc - dc_target) < 1:
                    # Vicino al target, usa poco
                    kg = min(remaining * 0.3, lot.qty_available * 0.95)
                else:
                    # Lontano, usa di più
                    kg = min(remaining * 0.5, lot.qty_available * 0.95)

            if kg >= OPERATIONAL_LIMITS['min_lot_usage_kg']:
                allocation.append((lot, kg))
                remaining -= kg

        total = sum(qty for _, qty in allocation)
        if total < target_kg * 0.9:  # FIX v3.3.5: soglia 90% invece di 70%
            return None

        return allocation if allocation else None

    def _simple_allocation(
        self,
        lots: List[LotData],
        target_kg: float
    ) -> Optional[List[Tuple[LotData, float]]]:
        """Allocazione semplice senza DC target"""

        allocation = []
        remaining = target_kg

        for lot in lots:
            if remaining <= 0:
                break

            kg = min(remaining * 1.2, lot.qty_available * 0.95)

            if kg >= OPERATIONAL_LIMITS['min_lot_usage_kg']:
                allocation.append((lot, kg))
                remaining -= kg

        total = sum(qty for _, qty in allocation)
        if total < target_kg * 0.9:  # FIX v3.3.5: soglia 90% invece di 70%
            return None

        return allocation if allocation else None

    def _uniform_allocation(
        self,
        lots: List[LotData],
        target_kg: float
    ) -> Optional[List[Tuple[LotData, float]]]:
        """Allocazione uniforme tra lotti"""

        n = len(lots)
        kg_per_lot = target_kg / n

        allocation = []
        for lot in lots:
            kg = min(kg_per_lot, lot.qty_available * 0.95)

            if kg >= OPERATIONAL_LIMITS['min_lot_usage_kg']:
                allocation.append((lot, kg))

        total = sum(qty for _, qty in allocation)
        if total < target_kg * 0.9:  # FIX v3.3.5: soglia 90% invece di 70%
            return None

        return allocation if allocation else None

    def _weighted_allocation(
        self,
        lots: List[LotData],
        target_kg: float,
        dc_target: float
    ) -> Optional[List[Tuple[LotData, float]]]:
        """Allocazione pesata per avvicinarsi a DC target"""
        
        # Calcola pesi per bilanciare verso DC target
        weights = []
        for lot in lots:
            if lot.dc_real is None:
                weights.append(0.5)
            else:
                # Peso inversamente proporzionale alla distanza da target
                distance = abs(lot.dc_real - dc_target)
                weight = 1.0 / (1.0 + distance)
                weights.append(weight)
        
        # Normalizza pesi
        total_weight = sum(weights)
        if total_weight == 0:
            return None
        
        normalized_weights = [w / total_weight for w in weights]
        
        # Alloca kg proporzionalmente ai pesi
        allocation = []
        for lot, weight in zip(lots, normalized_weights):
            kg_to_use = target_kg * weight
            
            # Rispetta disponibilità
            kg_to_use = min(
                kg_to_use,
                lot.qty_available * OPERATIONAL_LIMITS['max_lot_usage_pct'] / 100
            )
            
            # Rispetta minimo
            if kg_to_use >= OPERATIONAL_LIMITS['min_lot_usage_kg']:
                allocation.append((lot, kg_to_use))
        
        return allocation if allocation else None
    
    def _greedy_combination(
        self,
        start_lot: LotData,
        candidates: List[LotData],
        target_kg: float,
        requirements: Dict,
        max_lots: int
    ) -> Optional[List[Tuple[LotData, float]]]:
        """Combinazione greedy: aggiungi lotti finché raggiungi target"""
        
        combo = [(start_lot, min(target_kg * 0.3, start_lot.qty_available * 0.9))]
        current_kg = combo[0][1]
        current_dc_sum = start_lot.dc_real * current_kg if start_lot.dc_real else 0
        
        dc_target = requirements.get('dc_target')
        
        for lot in candidates:
            if lot == start_lot:
                continue
            
            if len(combo) >= max_lots:
                break
            
            if current_kg >= target_kg:
                break
            
            # Calcola quanto aggiungere
            remaining_kg = target_kg - current_kg
            kg_to_add = min(
                remaining_kg,
                lot.qty_available * 0.9,
                target_kg * 0.3
            )
            
            if kg_to_add < OPERATIONAL_LIMITS['min_lot_usage_kg']:
                continue
            
            # Verifica se migliora DC average
            if dc_target and lot.dc_real:
                new_kg = current_kg + kg_to_add
                new_dc_sum = current_dc_sum + (lot.dc_real * kg_to_add)
                new_dc_avg = new_dc_sum / new_kg

                # Calcola DC corrente (evita division by zero)
                current_dc_avg = current_dc_sum / current_kg if current_kg > 0 else 0

                # Aggiungi solo se migliora o mantiene DC target
                if abs(new_dc_avg - dc_target) <= abs(current_dc_avg - dc_target) + 5:
                    combo.append((lot, kg_to_add))
                    current_kg = new_kg
                    current_dc_sum = new_dc_sum
            else:
                combo.append((lot, kg_to_add))
                current_kg += kg_to_add
                if lot.dc_real:
                    current_dc_sum += lot.dc_real * kg_to_add
        
        return combo if len(combo) >= 2 else None
    
    def _evaluate_combination(
        self,
        combination: List[Tuple[LotData, float]],
        requirements: Dict
    ) -> Optional[BlendSolution]:
        """Valuta combinazione e calcola score"""
        
        solution = BlendSolution(
            lots=combination,
            requirements=requirements
        )
        
        # Calcola score
        score = 0
        breakdown = {}
        
        # 1. Conformità DC target
        if 'dc_target' in requirements and requirements['dc_target'] is not None:
            dc_score = self._score_dc_match(solution, requirements)
            score += dc_score
            breakdown['dc_match'] = dc_score
        
        # 2. Conformità FP target
        if 'fp_target' in requirements and requirements['fp_target'] is not None:
            fp_score = self._score_fp_match(solution, requirements)
            score += fp_score
            breakdown['fp_match'] = fp_score
        
        # 3. Conformità Duck target (CRITICO per economia)
        if 'duck_target' in requirements and requirements['duck_target'] is not None:
            duck_score = self.compatibility.calculate_duck_content_score(
                solution.duck_average,
                requirements['duck_target'],
                requirements.get('duck_tolerance', DEFAULT_TOLERANCES['duck_tolerance'])
            )
            score += duck_score
            breakdown['duck_match'] = duck_score
        
        # 4. Bonus smaltimento materiali brutti
        disposal_score = self._score_disposal_priority(solution)
        score += disposal_score
        breakdown['disposal'] = disposal_score
        
        # 5. Penalità numero lotti
        lot_penalty = self._score_lot_count(solution)
        score += lot_penalty
        breakdown['lot_count'] = lot_penalty
        
        # 6. Compatibilità specie
        species_score = self._score_species_compatibility(solution, requirements)
        score += species_score
        breakdown['species_compat'] = species_score
        
        # 7. Penalità dati stimati (solo per parametri richiesti)
        estimated_penalty = self._score_estimated_data(solution, requirements)
        score += estimated_penalty
        breakdown['estimated_penalty'] = estimated_penalty

        # 8. Penalità DC overqualification (preserva valore di opportunità materiale premium)
        dc_overqual_penalty = self._score_dc_overqualification(solution, requirements)
        score += dc_overqual_penalty
        breakdown['dc_overqualification'] = dc_overqual_penalty

        solution.score = score
        solution.score_breakdown = breakdown

        return solution
    
    def _score_dc_match(self, solution: BlendSolution, requirements: Dict) -> float:
        """Score per match DC target"""
        dc_target = requirements['dc_target']
        tolerance = requirements.get('dc_tolerance', DEFAULT_TOLERANCES['dc_tolerance'])
        
        deviation = abs(solution.dc_average - dc_target)
        
        if deviation <= tolerance:
            # Dentro tolleranza: bonus proporzionale
            bonus_factor = 1 - (deviation / tolerance)
            return SCORING_WEIGHTS['dc_target_match'] * bonus_factor
        else:
            # Fuori tolleranza: penalità crescente
            penalty_factor = (deviation - tolerance) / tolerance
            return -SCORING_WEIGHTS['dc_target_match'] * penalty_factor
    
    def _score_fp_match(self, solution: BlendSolution, requirements: Dict) -> float:
        """Score per match FP target"""
        fp_target = requirements['fp_target']
        tolerance = requirements.get('fp_tolerance', DEFAULT_TOLERANCES['fp_tolerance'])
        
        deviation = abs(solution.fp_average - fp_target)
        
        if deviation <= tolerance:
            bonus_factor = 1 - (deviation / tolerance)
            return SCORING_WEIGHTS['fp_target_match'] * bonus_factor
        else:
            penalty_factor = (deviation - tolerance) / tolerance
            return -SCORING_WEIGHTS['fp_target_match'] * penalty_factor
    
    def _score_disposal_priority(self, solution: BlendSolution) -> float:
        """Bonus per smaltimento lotti brutti"""
        score = 0
        
        for lot, kg_used in solution.lots:
            # Usa quality score del lotto (più alto = più brutto)
            lot_quality_score = lot.calculate_quality_score()
            
            # Peso proporzionale a kg usati
            weight = kg_used / solution.total_kg
            
            # Bonus per usare lotti brutti
            score += lot_quality_score * weight * 0.5
        
        return score
    
    def _score_lot_count(self, solution: BlendSolution) -> float:
        """
        Penalità progressiva per numero lotti

        Strategia più flessibile:
        - 2-5 lotti: nessuna penalità (ideale)
        - 6-7 lotti: penalità leggera (-25 per lotto)
        - 8-9 lotti: penalità media (-50 per lotto)
        - 10+ lotti: penalità alta (-100 per lotto)
        """
        num_lots = len(solution.lots)
        ideal = OPERATIONAL_LIMITS['ideal_lots_per_blend']

        if num_lots <= ideal:
            return 0

        penalty = 0

        # Penalità progressiva
        for n in range(ideal + 1, num_lots + 1):
            if n <= 7:
                penalty += -25  # Penalità leggera per lotti 6-7
            elif n <= 9:
                penalty += -50  # Penalità media per lotti 8-9
            else:
                penalty += -100  # Penalità alta per lotti 10+

        return penalty
    
    def _score_species_compatibility(
        self,
        solution: BlendSolution,
        requirements: Dict
    ) -> float:
        """Score compatibilità specie"""
        score = 0
        
        blend_species = requirements.get('species')
        duck_target = requirements.get('duck_target')
        
        if not blend_species:
            return 0
        
        # Per miscele oca con duck target
        if blend_species == 'O' and duck_target and duck_target > 0:
            for lot, kg_used in solution.lots:
                weight = kg_used / solution.total_kg
                
                if lot.product.species == 'OA':
                    # PREFERIBILE: misto per raggiungere duck target
                    score += SCORING_WEIGHTS['species_optimization_bonus'] * weight
                elif lot.product.species == 'A':
                    # ACCETTABILE: anatra pura
                    score += SCORING_WEIGHTS['species_mismatch_penalty'] * weight * 0.5
        
        return score
    
    def _score_estimated_data(self, solution: BlendSolution, requirements: Dict) -> float:
        """
        Penalità per dati stimati - SOLO per parametri effettivamente richiesti

        LOGICA CORRETTA v3.3.3:
        - Penalizza SOLO se il parametro è sia RICHIESTO che STIMATO
        - Se DC è richiesto e DC è stimato → penalità
        - Se FP è richiesto e FP è stimato → penalità
        - Se DC è reale ma FP è stimato, e solo DC è richiesto → NESSUNA penalità

        Esempio:
        - Lotto con DC reale ma FP stimato
        - Miscela richiede solo DC target (non FP target)
        - Risultato: NESSUNA penalità (il parametro stimato non è richiesto)
        """
        penalty = 0

        # Verifica quali parametri sono richiesti
        dc_required = 'dc_target' in requirements and requirements['dc_target'] is not None
        fp_required = 'fp_target' in requirements and requirements['fp_target'] is not None

        for lot, kg_used in solution.lots:
            lot_penalty = 0
            weight = kg_used / solution.total_kg if solution.total_kg > 0 else 0

            # Penalità per DC stimato SOLO se DC è richiesto
            if dc_required and lot.dc_was_imputed:
                lot_penalty += SCORING_WEIGHTS['estimated_data_penalty']

            # Penalità per FP stimato SOLO se FP è richiesto
            if fp_required and lot.fp_was_imputed:
                lot_penalty += SCORING_WEIGHTS['estimated_data_penalty']

            penalty += lot_penalty * weight

        return penalty

    def _score_dc_overqualification(self, solution: BlendSolution, requirements: Dict) -> float:
        """
        Penalità per "DC Overqualification" - preserva valore di opportunità materiale premium

        PRINCIPIO: Il valore del DC cresce in modo NON LINEARE. Un lotto con DC 90% è molto
        più prezioso per miscele con target 85%+ rispetto che per miscele con target 75%.

        LOGICA:
        - Calcola il "DC surplus" per ogni lotto: surplus = DC_lotto - DC_target
        - Se surplus > soglia (default 5%), applica penalità crescente esponenzialmente
        - Formula: penalità = (surplus)^2 * peso_penalità
        - La penalità cresce più rapidamente sopra il 10% di surplus

        ESEMPIO:
        - Target DC 75%, lotto DC 89% → surplus 14% → penalità alta (spreco materiale premium)
        - Target DC 75%, lotto DC 78% → surplus 3% → nessuna penalità (ottimale)
        - Target DC 85%, lotto DC 89% → surplus 4% → nessuna penalità (uso appropriato)

        Returns:
            float: Penalità negativa (riduce score se usi materiale troppo buono)
        """
        dc_target = requirements.get('dc_target')

        # Se non c'è target DC, nessuna penalità
        if dc_target is None:
            return 0

        penalty = 0
        threshold = SCORING_WEIGHTS.get('dc_overqualification_threshold', 5.0)
        penalty_weight = SCORING_WEIGHTS.get('dc_overqualification_penalty_weight', 1.0)

        for lot, kg_used in solution.lots:
            if lot.dc_real is None:
                continue

            # Calcola surplus DC
            surplus = lot.dc_real - dc_target

            # Applica penalità solo se surplus supera soglia
            if surplus > threshold:
                # Penalità esponenziale: cresce col quadrato del surplus
                # Maggiore il surplus, maggiore lo spreco di valore di opportunità
                lot_penalty = -(surplus ** 2) * penalty_weight

                # Peso proporzionale all'uso del lotto nella miscela
                weight = kg_used / solution.total_kg if solution.total_kg > 0 else 0

                penalty += lot_penalty * weight

        return penalty
    
    def simulate_blend(
        self,
        lot_composition: Dict[str, float],
        requirements: Dict
    ) -> Dict:
        """
        Simula risultato miscela proposta
        
        Args:
            lot_composition: Dict {lot_code: kg_quantity}
            requirements: Requisiti da verificare
        
        Returns:
            Dict con risultati simulazione
        """
        # Trova lotti
        lots_with_kg = []
        for lot_code, kg in lot_composition.items():
            lot = self.inventory.find_lot_by_code(lot_code)
            if lot:
                lots_with_kg.append((lot, kg))
            else:
                return {'error': f'Lotto {lot_code} non trovato'}
        
        # Crea soluzione
        solution = BlendSolution(
            lots=lots_with_kg,
            requirements=requirements
        )
        
        # Valuta
        evaluated = self._evaluate_combination(lots_with_kg, requirements)
        
        return {
            'valid': evaluated.is_valid() if evaluated else False,
            'summary': evaluated.get_summary() if evaluated else {},
            'score_breakdown': evaluated.score_breakdown if evaluated else {}
        }
