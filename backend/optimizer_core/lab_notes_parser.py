"""
OPTIMIZER v3.3 - Lab Notes Parser
Parser intelligente per estrarre informazioni dalle note laboratorio
"""

import re
from typing import Optional, Dict, Tuple
from dataclasses import dataclass


@dataclass
class LabEstimates:
    """Stime estratte dalle note laboratorio"""
    dc_estimate: Optional[float] = None  # DC stimato (media del range)
    dc_range: Optional[Tuple[float, float]] = None  # Range DC (min, max)
    fp_estimate: Optional[float] = None  # FP stimato
    oe_class: Optional[int] = None  # CL1-CL4 (Classe Other Elements)
    oe_estimate: Optional[float] = None  # Other Elements stimato
    broken_estimate: Optional[float] = None  # Broken stimato
    confidence: float = 0.0  # Confidenza stima (0-1)
    source: str = ""  # Testo originale da cui estratto


class LabNotesParser:
    """Parser per note laboratorio"""

    # Mapping FP qualitativo → valore numerico approssimativo
    FP_QUALITATIVE_MAP = {
        'molto alto': 800,
        'alto': 750,
        'medio-alto': 700,
        'medio alto': 700,
        'medio': 650,
        'medio-basso': 600,
        'medio basso': 600,
        'basso': 550,
        'molto basso': 500,
        'buona resa': 680,  # Indica FP discreto
        'ottima resa': 720,
    }

    # Mapping CL (Class) → % Other Elements
    # CL indica la CLASSE di qualità del prodotto basata su Other Elements
    CLASS_TO_OE = {
        1: 5.0,   # CL1 / Class 1 → ~5% Other Elements (migliore)
        2: 12.0,  # CL2 / Class 2 → ~12% Other Elements
        3: 20.0,  # CL3 / Class 3 → ~20% Other Elements
        4: 30.0   # CL4 / Class 4 → ~30%+ Other Elements (peggiore)
    }

    # Mapping presenza broken/fibre → % stimata Other Elements
    # Questi vengono usati SOLO se non c'è CL
    OE_INDICATORS = {
        'assenza': 0.5,
        'bassa presenza': 2.0,
        'media presenza': 4.0,
        'alta presenza': 6.0,
        'molto alta presenza': 8.0,
    }

    def parse(self, lab_note: str) -> LabEstimates:
        """
        Parse note laboratorio ed estrae stime

        Args:
            lab_note: Testo note laboratorio

        Returns:
            LabEstimates con valori estratti
        """
        if not lab_note or len(str(lab_note).strip()) < 5:
            return LabEstimates()

        note = str(lab_note).lower()
        estimates = LabEstimates(source=lab_note[:100])

        # Estrai DC
        dc_info = self._extract_dc(note)
        if dc_info:
            estimates.dc_estimate = dc_info['estimate']
            estimates.dc_range = dc_info.get('range')
            estimates.confidence += 0.4  # DC è info più importante

        # Estrai Class (CL) → Other Elements
        # CL è l'indicatore PRINCIPALE di Other Elements
        cl = self._extract_class(note)
        if cl:
            estimates.oe_class = cl
            estimates.oe_estimate = self.CLASS_TO_OE.get(cl)
            estimates.confidence += 0.3  # CL è molto affidabile

        # Estrai Fill Power
        fp = self._extract_fill_power(note)
        if fp:
            estimates.fp_estimate = fp
            estimates.confidence += 0.2

        # Estrai Other Elements da broken/fibre (SOLO se non c'è già CL)
        if not cl:
            oe = self._extract_other_elements_from_indicators(note)
            if oe is not None:
                estimates.oe_estimate = oe
                estimates.confidence += 0.1  # Meno affidabile di CL

        return estimates

    def _extract_dc(self, note: str) -> Optional[Dict]:
        """
        Estrae DC da note laboratorio

        Pattern supportati:
        - "DC 35-40%"
        - "DC 10-12%"
        - "DC 3-5%"
        - "circa un 18-20% di piumino"
        - "visivamente circa un 18-20%"
        - "DC 68%"
        """
        # Pattern 1: "DC XX-YY%"
        pattern1 = r'dc[:\s]+(\d+(?:\.\d+)?)\s*-\s*(\d+(?:\.\d+)?)\s*%'
        match = re.search(pattern1, note)
        if match:
            min_dc = float(match.group(1))
            max_dc = float(match.group(2))
            avg_dc = (min_dc + max_dc) / 2
            return {
                'estimate': avg_dc,
                'range': (min_dc, max_dc),
                'confidence': 0.9
            }

        # Pattern 2: "DC XX%"
        pattern2 = r'dc[:\s]+(\d+(?:\.\d+)?)\s*%'
        match = re.search(pattern2, note)
        if match:
            dc = float(match.group(1))
            return {
                'estimate': dc,
                'range': (dc - 2, dc + 2),  # Tolleranza ±2%
                'confidence': 0.85
            }

        # Pattern 3: "circa un XX-YY% di piumino"
        pattern3 = r'circa\s+un?\s+(\d+)\s*-\s*(\d+)\s*%\s*(di\s+)?piumino'
        match = re.search(pattern3, note)
        if match:
            min_dc = float(match.group(1))
            max_dc = float(match.group(2))
            avg_dc = (min_dc + max_dc) / 2
            return {
                'estimate': avg_dc,
                'range': (min_dc, max_dc),
                'confidence': 0.8  # Leggermente meno preciso
            }

        # Pattern 4: "visivamente circa un XX%"
        pattern4 = r'visivamente\s+circa\s+un?\s+(\d+)\s*%'
        match = re.search(pattern4, note)
        if match:
            dc = float(match.group(1))
            return {
                'estimate': dc,
                'range': (dc - 3, dc + 3),  # Tolleranza maggiore per stime visive
                'confidence': 0.7
            }

        return None

    def _extract_class(self, note: str) -> Optional[int]:
        """
        Estrae Class (CL1-CL4) che indica livello Other Elements

        CL indica la CLASSE di qualità del prodotto:
        - CL1 / Class 1: ~5% Other Elements (migliore qualità)
        - CL2 / Class 2: ~12% Other Elements
        - CL3 / Class 3: ~20% Other Elements
        - CL4 / Class 4: ~30%+ Other Elements (qualità inferiore)
        """
        # Pattern 1: "CL1", "CL2", etc.
        pattern1 = r'cl\s*(\d)'
        match = re.search(pattern1, note)
        if match:
            cl = int(match.group(1))
            if 1 <= cl <= 4:
                return cl

        # Pattern 2: "Class 1", "Class 2", etc.
        pattern2 = r'class\s*(\d)'
        match = re.search(pattern2, note)
        if match:
            cl = int(match.group(1))
            if 1 <= cl <= 4:
                return cl

        return None

    def _extract_fill_power(self, note: str) -> Optional[float]:
        """
        Estrae Fill Power da indicazioni qualitative

        Pattern:
        - "FP alla mano medio-alto" → 700
        - "FP alla mano basso" → 550
        - "buona resa" → 680
        """
        # Cerca indicatori qualitativi
        for indicator, fp_value in self.FP_QUALITATIVE_MAP.items():
            if indicator in note:
                # Se trova anche "fp" vicino, aumenta confidenza
                if re.search(rf'fp\s+.*{re.escape(indicator)}', note):
                    return fp_value
                # Anche senza "fp", se trova "resa" è valido
                if 'resa' in indicator and indicator in note:
                    return fp_value
                # Pattern generico
                if 'fp' in note:
                    return fp_value

        return None

    def _extract_other_elements_from_indicators(self, note: str) -> Optional[float]:
        """
        Estrae stima Other Elements da menzioni di broken, fibre, ecc.

        NOTA: Questo metodo viene usato SOLO se non è presente CL (Class)
        CL è l'indicatore primario e più affidabile di Other Elements.

        Combina indicatori di:
        - Broken
        - Fibre di piumino
        - Polvere
        """
        oe_estimate = 0.0
        indicators_found = 0

        # Cerca indicatori di broken
        for indicator, oe_value in self.OE_INDICATORS.items():
            if indicator in note and 'broken' in note:
                oe_estimate += oe_value
                indicators_found += 1
                break

        # Cerca indicatori di fibre
        for indicator, oe_value in self.OE_INDICATORS.items():
            if indicator in note and 'fibr' in note:
                oe_estimate += oe_value * 0.7  # Peso minore per fibre
                indicators_found += 1
                break

        # Cerca "polvere"
        if 'polvere' in note:
            oe_estimate += 1.5
            indicators_found += 1

        if indicators_found > 0:
            # Normalizza se ha trovato più indicatori
            if indicators_found > 1:
                oe_estimate = oe_estimate * 0.7  # Evita sovrastima
            return min(oe_estimate, 15.0)  # Cap massimo 15%

        return None


def parse_lab_notes(lab_note: str) -> LabEstimates:
    """Helper function per parsing veloce"""
    parser = LabNotesParser()
    return parser.parse(lab_note)
