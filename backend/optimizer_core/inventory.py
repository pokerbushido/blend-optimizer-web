"""
OPTIMIZER v3.3 - Inventory Manager
Gestione caricamento e preprocessing inventario
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional
from dataclasses import dataclass, field
from compatibility import ProductCode, parse_product_code
from lab_notes_parser import parse_lab_notes


@dataclass
class LotData:
    """Rappresenta un lotto di materiale"""
    lot_code: str
    article_code: str
    product: ProductCode = field(init=False)
    
    # Parametri qualità reali
    dc_real: Optional[float] = None
    fp_real: Optional[float] = None
    duck_real: Optional[float] = None
    other_elements_real: Optional[float] = None
    feather_real: Optional[float] = None
    oxygen_real: Optional[float] = None
    turbidity_real: Optional[float] = None
    total_fibres_real: Optional[float] = None
    broken_real: Optional[float] = None
    landfowl_real: Optional[float] = None
    
    # Disponibilità e costi
    qty_available: float = 0
    cost_per_kg: Optional[float] = None
    
    # Metadati
    description: str = ""
    lab_notes: str = ""
    is_estimated: bool = False

    # Valori nominali (dichiarati)
    dc_nominal: Optional[float] = None
    quality_nominal: Optional[str] = None
    standard_nominal: Optional[str] = None
    fp_nominal: Optional[float] = None

    # Flag per tracciare imputazioni del sistema (IGNORARE colonna "Stimato" WMS)
    dc_was_imputed: bool = False  # True se DC_real imputato da DC_nominal (era 0 nel CSV)
    fp_was_imputed: bool = False  # True se FP_real imputato da FP_nominal (era 0 nel CSV)

    # Assegnazione Range (NUOVO - per sistema cascata)
    dc_range_assigned: Optional[str] = None  # Range DC assegnato (es: 'DC85', 'DC90+')
    dc_assignment_source: str = 'unknown'  # Fonte: 'dc_real', 'note_labo', 'nominale', 'unknown'
    duck_range_assigned: Optional[str] = None  # Range Duck assegnato (es: 'DUCK_0-5', 'DUCK_5-10')
    duck_assignment_source: str = 'unknown'  # Fonte dell'assegnazione Duck
    fp_range_assigned: Optional[str] = None  # Range Fill Power assegnato (es: 'FP800+', 'FP750-799')
    fp_assignment_source: str = 'unknown'  # Fonte dell'assegnazione Fill Power
    
    def __post_init__(self):
        """Inizializza ProductCode"""
        self.product = parse_product_code(self.article_code)

        # NOTA: _check_estimated_data() viene chiamato DOPO le correzioni
        # in _row_to_lot(), altrimenti marca come stimati lotti che poi
        # vengono corretti con valori nominali
    
    def _check_estimated_data(self):
        """
        Verifica se i dati sono stimati (imputati dal sistema)

        NUOVA LOGICA v3.3.4:
        Un lotto è "stimato" SOLO se il sistema ha imputato DC
        perché mancava nel CSV (valore era 0 o None).

        FP imputato NON rende il lotto stimato perché:
        - DC è il parametro critico per le miscele
        - FP è secondario e spesso stimabile con buona precisione dalle note lab

        NON considera più:
        - La coincidenza DC_real == DC_nominal (lotti da miscele precedenti!)
        - La colonna "Stimato" del WMS (ignoriamo completamente)

        Usa SOLO il flag dc_was_imputed settato durante caricamento.
        """
        # Lotto stimato SOLO se DC è stato imputato (parametro critico)
        # FP imputato è accettabile - non marca il lotto come stimato
        self.is_estimated = self.dc_was_imputed
    
    def has_sufficient_data(self) -> bool:
        """Verifica se ha dati sufficienti per l'uso"""
        # Almeno DC deve essere presente
        return self.dc_real is not None

    def is_water_repellent(self) -> bool:
        """
        Verifica se il lotto ha trattamento water repellent (GWR/NWR)

        IMPORTANTE: GWR/NWR può essere presente in DUE posti:
        1. Nel codice articolo come certificazione (es: 3|POB|GWR)
        2. Nel campo quality_nominal (SCO_Quality_Nom dal CSV)

        Questo metodo controlla ENTRAMBI i posti.

        Returns:
            True se il lotto ha trattamento GWR o NWR
        """
        # Controlla certificazione nel codice articolo
        if self.product.is_water_repellent():
            return True

        # Controlla quality_nominal (campo SCO_Quality_Nom)
        if self.quality_nominal:
            quality_upper = str(self.quality_nominal).upper().strip()
            if quality_upper in ['GWR', 'NWR']:
                return True

        return False
    
    def calculate_quality_score(self) -> float:
        """
        Calcola score qualità (INVERSO: valori alti = bassa qualità)
        Score più alto = lotto "più brutto" = priorità smaltimento
        """
        import math

        score = 0

        # Helper per verificare valore valido (non None e non NaN)
        def is_valid(value):
            return value is not None and not (isinstance(value, float) and math.isnan(value))

        # DC basso = score alto (vuoi smaltirlo)
        if is_valid(self.dc_real):
            score += (100 - self.dc_real) * 2

        # Duck alto = score alto (per miscele oca)
        if is_valid(self.duck_real):
            score += self.duck_real * 1.5

        # Other Elements alto = score alto
        if is_valid(self.other_elements_real):
            score += self.other_elements_real * 3

        # Feather alto = score alto
        if is_valid(self.feather_real):
            score += self.feather_real * 1.0

        # Altri parametri negativi
        if is_valid(self.total_fibres_real):
            score += self.total_fibres_real * 2

        if is_valid(self.broken_real):
            score += self.broken_real * 1.5

        if is_valid(self.landfowl_real):
            score += self.landfowl_real * 2

        # Penalità per dati stimati
        if self.is_estimated:
            score -= 50

        return score
    
    def to_dict(self) -> Dict:
        """Converte in dizionario per output"""
        return {
            'Codice Art': self.article_code,
            'Codice Lotto': self.lot_code,
            'Descrizione lotto': self.description,
            'Note Laboratorio': self.lab_notes,
            'DC reale': self.dc_real,
            'Other Elements reale': self.other_elements_real,
            'Feather reale': self.feather_real,
            'FP reale': self.fp_real,
            'Duck reale': self.duck_real,
            'Stimato si/no': 'SI' if self.is_estimated else 'NO',
            'Ossigeno reale O2': self.oxygen_real,
            'Turbidità reale': self.turbidity_real,
            'Quantità disponibile a magazzino': self.qty_available,
            'Costo euro/kg': self.cost_per_kg,
            'Total Fibres': self.total_fibres_real,
            'Broken': self.broken_real,
            'Landfowl': self.landfowl_real,
            'Variante DC Nominale': self.dc_nominal,
            'Variante Quality nominale': self.quality_nominal,
            'Variante Std nominale': self.standard_nominal,
            'Variante FP nominale': self.fp_nominal
        }


class InventoryManager:
    """Gestisce l'inventario dei lotti"""
    
    def __init__(self):
        self.lots: List[LotData] = []
        self.df: Optional[pd.DataFrame] = None
    
    def load_from_csv(self, filepath: str) -> Dict:
        """
        Carica inventario da file CSV WMS

        Returns:
            Dict con statistiche caricamento
        """
        import logging
        logger = logging.getLogger(__name__)

        try:
            # Leggi CSV
            logger.info(f"Loading CSV from {filepath}")
            df = pd.read_csv(filepath, sep=',', encoding='utf-8')
            logger.info(f"CSV loaded: {len(df)} rows, columns: {list(df.columns)}")

            # Preprocessing: gestisci formato numeri italiani
            df = self._preprocess_dataframe(df)

            # Filtra materie prime (escludiamo) - solo se colonna esiste
            if 'SCO_Gruppo' in df.columns:
                df = df[df['SCO_Gruppo'] != '5']

            # Converti in LotData objects
            self.lots = []
            skipped = 0
            error_details = []

            for row_idx, row in df.iterrows():
                try:
                    lot = self._row_to_lot(row)
                    if lot and lot.has_sufficient_data():
                        self.lots.append(lot)
                    else:
                        skipped += 1
                        if lot:
                            logger.debug(f"Row {row_idx}: Insufficient data for lot {lot.lot_code}")
                except Exception as e:
                    skipped += 1
                    error_msg = f"Row {row_idx}: {str(e)}"
                    error_details.append(error_msg)
                    logger.warning(f"Failed to process row {row_idx}: {str(e)}")
                    continue

            self.df = df

            # Log summary
            logger.info(f"Loaded {len(self.lots)} lots, skipped {skipped} rows")
            if error_details:
                logger.warning(f"Errors during processing: {error_details[:5]}")  # Log first 5 errors

            return {
                'success': True,
                'total_rows': len(df),
                'lots_loaded': len(self.lots),
                'lots_skipped': skipped,
                'unique_articles': len(set(lot.article_code for lot in self.lots)),
                'total_kg_available': sum(lot.qty_available for lot in self.lots),
                'error_details': error_details[:10]  # Return first 10 errors if any
            }

        except Exception as e:
            logger.error(f"Failed to load CSV: {str(e)}", exc_info=True)
            return {
                'success': False,
                'error': str(e)
            }
    
    def _preprocess_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        """Preprocessa DataFrame: gestione numeri italiani, null, etc."""

        # Mapping colonne CSV WMS reale -> nomi attesi dal codice
        column_mapping = {
            'SCO_Duck': 'SCO_Duck_Real',
            'SCO_OtherElements': 'SCO_OtherElements_Real',
            'SCO_Feather': 'SCO_Feather_Real',
            'SCO_OxygenIndex': 'SCO_Ossigeno_Real',
            'SCO_Turbidity': 'SCO_Torbidita_Real',
            'SCO_TotalFibres': 'SCO_TotalFibres_Real',
            'SCO_Broken': 'SCO_Broken_Real',
            'SCO_Landfowl': 'SCO_Landfowl_Real',
            'DISPONIBILE': 'SCO_Qty',
            'LOT_PrezzoUnit': 'SCO_CostoKg'
        }

        # Rinomina colonne se esistono
        df = df.rename(columns=column_mapping)

        # Colonne numeriche da convertire
        numeric_cols = [
            'SCO_DownCluster_Real', 'SCO_FillPower_Real', 'SCO_Duck_Real',
            'SCO_OtherElements_Real', 'SCO_Feather_Real', 'SCO_Ossigeno_Real',
            'SCO_Torbidita_Real', 'SCO_TotalFibres_Real', 'SCO_Broken_Real',
            'SCO_Landfowl_Real', 'SCO_Qty', 'SCO_CostoKg'
        ]
        
        for col in numeric_cols:
            if col in df.columns:
                # Converti formato italiano (virgola -> punto)
                if df[col].dtype == 'object':
                    df[col] = df[col].astype(str).str.replace(',', '.')
                
                # Converti a numerico, gestendo errori
                df[col] = pd.to_numeric(df[col], errors='coerce')
        
        # Gestisci null
        df = df.fillna({
            'SCO_DownCluster_Real': np.nan,
            'SCO_FillPower_Real': np.nan,
            'SCO_Duck_Real': 0,  # Default 0 per duck se mancante
            'SCO_OtherElements_Real': np.nan,
            'SCO_Feather_Real': np.nan
        })
        
        return df
    
    def _row_to_lot(self, row) -> Optional[LotData]:
        """Converte riga DataFrame in LotData"""
        try:
            # Helper function to safely get value from pandas Series (use closure over row)
            def get_first_value(*column_names):
                """
                Try multiple column names and return first non-null value from row.
                Uses closure to access 'row' from outer scope - prevents pandas Series ambiguity error.
                """
                for col_name in column_names:
                    if col_name in row.index:
                        val = row[col_name]
                        if pd.notna(val):
                            val_str = str(val).strip()
                            if val_str and val_str.lower() != 'nan':
                                return val_str
                return None

            def get_value_safe(col_name, default=None):
                """Safely get single column value from pandas Series"""
                if col_name in row.index:
                    val = row[col_name]
                    if pd.notna(val):
                        return val
                return default

            # Determina descrizione e note lab dalle colonne disponibili
            # FIXED: Use helper function instead of row.get() to avoid pandas Series ambiguity
            description = get_first_value('LOT_DESC', 'SCO_Descrizione') or ''
            lab_notes = get_first_value('SCO_LabNote', 'LOT_LabNote', 'SCO_NoteLab') or ''

            # Ottieni duck_real dal CSV
            duck_real_raw = get_value_safe('SCO_Duck_Real', 0)

            lot = LotData(
                lot_code=str(row['SCO_LOTT']),
                article_code=str(row['SCO_ART']),
                dc_real=get_value_safe('SCO_DownCluster_Real'),
                fp_real=get_value_safe('SCO_FillPower_Real'),
                duck_real=duck_real_raw,  # Verrà corretto dopo se necessario
                other_elements_real=get_value_safe('SCO_OtherElements_Real'),
                feather_real=get_value_safe('SCO_Feather_Real'),
                oxygen_real=get_value_safe('SCO_Ossigeno_Real'),
                turbidity_real=get_value_safe('SCO_Torbidita_Real'),
                total_fibres_real=get_value_safe('SCO_TotalFibres_Real'),
                broken_real=get_value_safe('SCO_Broken_Real'),
                landfowl_real=get_value_safe('SCO_Landfowl_Real'),
                qty_available=get_value_safe('SCO_Qty', 0),
                cost_per_kg=get_value_safe('SCO_CostoKg'),
                description=description,
                lab_notes=lab_notes,
                dc_nominal=get_value_safe('SCO_DownCluster_Nom'),
                quality_nominal=get_value_safe('SCO_Quality_Nom'),
                standard_nominal=get_value_safe('SCO_Standard_Nom'),
                fp_nominal=get_value_safe('SCO_FillPower_Nom')
            )

            # CORREZIONE 1: DC non testato → stima da note laboratorio > nominale
            # Priorità: 1) Note laboratorio, 2) DC nominale
            if (lot.dc_real is None or lot.dc_real == 0):
                # Prova prima a estrarre da note laboratorio
                lab_estimates = None
                if lot.lab_notes and len(str(lot.lab_notes).strip()) > 5:
                    lab_estimates = parse_lab_notes(str(lot.lab_notes))

                if lab_estimates and lab_estimates.dc_estimate:
                    # Usa stima da note laboratorio (più precisa!)
                    lot.dc_real = lab_estimates.dc_estimate
                    lot.dc_was_imputed = True
                    # Salva anche OE se disponibile
                    if lab_estimates.oe_estimate and (lot.other_elements_real is None or lot.other_elements_real == 0):
                        lot.other_elements_real = lab_estimates.oe_estimate
                elif lot.dc_nominal and lot.dc_nominal > 0:
                    # Fallback: usa DC nominale
                    lot.dc_real = lot.dc_nominal
                    lot.dc_was_imputed = True

            # CORREZIONE 2: FP non testato → stima da note laboratorio > nominale
            # Priorità: 1) Note laboratorio, 2) FP nominale
            if (lot.fp_real is None or lot.fp_real == 0):
                # Prova prima a estrarre da note laboratorio
                lab_estimates = None
                if lot.lab_notes and len(str(lot.lab_notes).strip()) > 5:
                    lab_estimates = parse_lab_notes(str(lot.lab_notes))

                if lab_estimates and lab_estimates.fp_estimate:
                    # Usa stima da note laboratorio (più precisa!)
                    lot.fp_real = lab_estimates.fp_estimate
                    lot.fp_was_imputed = True
                elif lot.fp_nominal and lot.fp_nominal > 0:
                    # Fallback: usa FP nominale
                    lot.fp_real = lot.fp_nominal
                    lot.fp_was_imputed = True

            # CORREZIONE 3: DUCK per articoli ANATRA
            # Se il codice articolo indica ANATRA (species='A') e duck_real è 0 o None,
            # significa che è 100% anatra (non serve misurarlo)
            if lot.product.species == 'A':
                if lot.duck_real is None or lot.duck_real == 0:
                    lot.duck_real = 100.0

            # CORREZIONE 4: DUCK per articoli OCA
            # Se il codice articolo indica OCA (species='O') e duck_real è None,
            # imposta a 0 (oca pura)
            if lot.product.species == 'O':
                if lot.duck_real is None:
                    lot.duck_real = 0.0

            # CORREZIONE 5: DUCK per articoli MISTI (POAG, POAB, etc.)
            # Se il codice articolo indica MISTO OCA/ANATRA (species='OA') e duck_real è 0 o None,
            # stima al 50% (i misti hanno sempre del duck, 0% è impossibile)
            if lot.product.species == 'OA':
                if lot.duck_real is None or lot.duck_real == 0:
                    lot.duck_real = 50.0

            # IMPORTANTE: Verifica se dati sono stimati DOPO tutte le correzioni
            lot._check_estimated_data()

            return lot
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            # Log with more context for debugging
            try:
                article = str(row['SCO_ART']) if 'SCO_ART' in row.index and pd.notna(row['SCO_ART']) else 'UNKNOWN'
                lot_code = str(row['SCO_LOTT']) if 'SCO_LOTT' in row.index and pd.notna(row['SCO_LOTT']) else 'UNKNOWN'
                logger.error(f"Error processing row for article {article}, lot {lot_code}: {str(e)}", exc_info=True)
            except:
                logger.error(f"Error processing row: {str(e)}", exc_info=True)
            return None
    
    def filter_lots(
        self,
        species: Optional[str] = None,
        color: Optional[str] = None,
        min_dc: Optional[float] = None,
        max_dc: Optional[float] = None,
        min_qty: Optional[float] = None,
        exclude_water_repellent: bool = True,
        exclude_raw_materials: bool = True,
        allow_estimated: bool = False
    ) -> List[LotData]:
        """
        Filtra lotti secondo criteri

        Args:
            exclude_raw_materials: Se True, esclude materiali grezzi (group='G')

        Returns:
            Lista di LotData filtrati
        """
        filtered = self.lots.copy()

        # Filtra materiali grezzi (group='G')
        if exclude_raw_materials:
            filtered = [l for l in filtered if l.product.group != 'G']

        # Filtra per specie
        if species:
            filtered = [l for l in filtered if l.product.species == species]

        # Filtra per colore
        if color:
            filtered = [l for l in filtered if l.product.color == color]

        # Filtra per DC
        if min_dc is not None:
            filtered = [l for l in filtered
                       if l.dc_real is not None and l.dc_real >= min_dc]
        if max_dc is not None:
            filtered = [l for l in filtered
                       if l.dc_real is not None and l.dc_real <= max_dc]

        # Filtra per quantità minima
        if min_qty is not None:
            filtered = [l for l in filtered if l.qty_available >= min_qty]

        # Filtra water repellent
        # IMPORTANTE: usa l.is_water_repellent() (metodo del lotto) invece di
        # l.product.is_water_repellent() perché GWR/NWR può essere anche in quality_nominal
        if exclude_water_repellent:
            filtered = [l for l in filtered if not l.is_water_repellent()]

        # Filtra dati stimati
        if not allow_estimated:
            filtered = [l for l in filtered if not l.is_estimated]

        return filtered
    
    def get_statistics(self) -> Dict:
        """Ritorna statistiche inventario"""
        if not self.lots:
            return {'error': 'Nessun lotto caricato'}
        
        # Raggruppa per articolo
        by_article = {}
        for lot in self.lots:
            art = lot.article_code
            if art not in by_article:
                by_article[art] = []
            by_article[art].append(lot)
        
        # Calcola statistiche
        stats = {
            'total_lots': len(self.lots),
            'total_articles': len(by_article),
            'total_kg': sum(l.qty_available for l in self.lots),
            'lots_with_estimated_data': sum(1 for l in self.lots if l.is_estimated),
            'by_species': self._group_by_attribute('species'),
            'by_color': self._group_by_attribute('color'),
            'by_state': self._group_by_attribute('state'),
            'dc_range': {
                'min': min((l.dc_real for l in self.lots if l.dc_real is not None), default=0),
                'max': max((l.dc_real for l in self.lots if l.dc_real is not None), default=0),
                'avg': np.mean([l.dc_real for l in self.lots if l.dc_real is not None]) if any(l.dc_real is not None for l in self.lots) else 0
            }
        }
        
        return stats
    
    def _group_by_attribute(self, attr: str) -> Dict:
        """Raggruppa lotti per attributo ProductCode"""
        groups = {}
        for lot in self.lots:
            value = getattr(lot.product, attr, None)
            if value:
                if value not in groups:
                    groups[value] = {
                        'count': 0,
                        'total_kg': 0
                    }
                groups[value]['count'] += 1
                groups[value]['total_kg'] += lot.qty_available
        return groups
    
    def find_lot_by_code(self, lot_code: str) -> Optional[LotData]:
        """Trova lotto per codice"""
        for lot in self.lots:
            if lot.lot_code == lot_code:
                return lot
        return None
    
    def get_lots_by_article(self, article_code: str) -> List[LotData]:
        """Ritorna tutti i lotti di un articolo"""
        return [l for l in self.lots if l.article_code == article_code]
