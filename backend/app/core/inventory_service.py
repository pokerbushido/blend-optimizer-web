"""
Inventory Service
Handles CSV parsing and database operations for inventory
Adapts optimizer_core/inventory.py functionality
"""
import sys
import pandas as pd
from typing import List, Optional, Dict
from io import StringIO
from sqlalchemy.orm import Session
from uuid import UUID
import re

# Add optimizer core to path
import os
optimizer_core_path = os.path.join(os.path.dirname(__file__), '..', '..', 'optimizer_core')
optimizer_core_path = os.path.abspath(optimizer_core_path)
if optimizer_core_path not in sys.path:
    sys.path.insert(0, optimizer_core_path)
from inventory import InventoryManager as CoreInventoryManager

from app.models.models import InventoryLot, InventoryUpload, User


class InventoryService:
    """Service for managing inventory data"""

    # Column mapping for Italian WMS CSV format → standardized column names
    # Based on optimizer_core/inventory.py for compatibility
    COLUMN_MAPPING = {
        # Quantity variations (most important!)
        'DISPONIBILE': 'SCO_QTA',
        'quantità disponibile': 'SCO_QTA',
        'disponibile': 'SCO_QTA',
        'qta': 'SCO_QTA',
        'quantita disponibile': 'SCO_QTA',  # without accent

        # Price/Cost variations
        'LOT_PrezzoUnit': 'SCO_COSTO_KG',
        'prezzo': 'SCO_COSTO_KG',
        'costo per kg': 'SCO_COSTO_KG',

        # Quality parameters with _Real suffix (from optimizer_core)
        'SCO_Duck_Real': 'SCO_Duck',
        'SCO_OtherElements_Real': 'SCO_OE',
        'SCO_Feather_Real': 'SCO_Feather',
        'SCO_TotalFibres_Real': 'SCO_TotalFibres',
        'SCO_Broken_Real': 'SCO_Broken',
        'SCO_Landfowl_Real': 'SCO_Landfowl',

        # Quality parameters (Italian variations)
        'SCO_OtherElements': 'SCO_OE',
        'SCO_OxygenIndex': 'SCO_Oxygen',
        'SCO_Ossigeno_Real': 'SCO_Oxygen',
        'SCO_Torbidita_Real': 'SCO_Turbidity',

        # Nominal values with _Nom suffix
        'SCO_DownCluster_Nom': 'SCO_DownCluster_Nominal',
        'SCO_FillPower_Nom': 'SCO_FillPower_Nominal',
        'SCO_Standard_Nom': 'SCO_Standard_Nominal',
        'SCO_Quality_Nom': 'SCO_QUALITA',

        # Description variations
        'descrizione': 'SCO_DESC',
        'LOT_DESC': 'SCO_DESC',

        # Quality variations
        'qualità': 'SCO_QUALITA',
        'qualita': 'SCO_QUALITA',

        # Lab notes variations (all possible column names)
        'note laboratorio': 'SCO_NOTE_LAB',
        'note': 'SCO_NOTE_LAB',
        'SCO_LabNote': 'SCO_NOTE_LAB',
        'LOT_LabNote': 'SCO_NOTE_LAB',
        'SCO_NoteLab': 'SCO_NOTE_LAB',
        'SCO_NOTE_LABORATORIO': 'SCO_NOTE_LAB',
    }

    @staticmethod
    def parse_article_code(code: str) -> Dict[str, Optional[str]]:
        """
        Parse article code into components
        Based on optimizer_core/compatibility.py logic

        Format: [GROUP]|{STATE}{SPECIES}{COLOR}|[CERTIFICATION]

        Returns dict with: group_code, species, color, state, certification
        """
        # Handle special codes (PGR, PBR)
        if 'PGR' in code.upper():
            return {
                'group_code': None,
                'species': 'OA',
                'color': 'G',
                'state': 'P',
                'certification': None
            }
        if 'PBR' in code.upper():
            return {
                'group_code': None,
                'species': 'OA',
                'color': 'B',
                'state': 'P',
                'certification': None
            }

        # Split by pipe
        parts = code.split('|')

        result = {
            'group_code': None,
            'species': None,
            'color': None,
            'state': None,
            'certification': None
        }

        # Parse parts
        for part in parts:
            part = part.strip()

            # Group code (single digit or 'G')
            if part in ['3', 'G']:
                result['group_code'] = part
            # Certification
            elif part in ['GWR', 'NWR']:
                result['certification'] = part
            # Main code (STATE + SPECIES + COLOR)
            elif len(part) >= 3:
                # State: P, M, S, O
                if part[0] in ['P', 'M', 'S', 'O']:
                    result['state'] = part[0]
                    # Species: O, A, C, OA
                    if len(part) >= 3:
                        if part[1:3] == 'OA':
                            result['species'] = 'OA'
                            # Color after OA
                            if len(part) > 3:
                                result['color'] = part[3:]
                        else:
                            result['species'] = part[1]
                            # Color after single species
                            if len(part) > 2:
                                result['color'] = part[2:]

        return result

    @staticmethod
    def normalize_column_names(df: pd.DataFrame) -> pd.DataFrame:
        """
        Normalize column names to handle Italian WMS format variations

        Maps Italian column names to standardized names used by the web app.
        Handles case-insensitive matching and extra whitespace.
        Prevents duplicate column names by keeping only the first occurrence.

        Args:
            df: DataFrame with original column names

        Returns:
            DataFrame with normalized column names
        """
        import logging
        logger = logging.getLogger(__name__)

        # Create a mapping from normalized original names to new names
        rename_mapping = {}
        columns_seen = set()  # Track target column names we've already mapped

        for original_col in df.columns:
            # Normalize: strip whitespace, lowercase for matching
            normalized = original_col.strip().lower()

            # Check if this normalized name is in our mapping
            if normalized in {k.lower(): v for k, v in InventoryService.COLUMN_MAPPING.items()}:
                # Find the target column name
                for italian_name, standard_name in InventoryService.COLUMN_MAPPING.items():
                    if italian_name.lower() == normalized:
                        # Only map if we haven't already mapped to this target column
                        if standard_name not in columns_seen:
                            rename_mapping[original_col] = standard_name
                            columns_seen.add(standard_name)
                        else:
                            # Skip this column to avoid duplicates
                            logger.warning(
                                f"Skipping duplicate column mapping: '{original_col}' → '{standard_name}' "
                                f"(already mapped from another column)"
                            )
                        break

        # Apply renaming
        if rename_mapping:
            df = df.rename(columns=rename_mapping)

        return df

    @staticmethod
    def csv_to_dataframe(csv_content: str) -> pd.DataFrame:
        """
        Parse CSV content to DataFrame
        Handles Italian format (comma as decimal separator)
        Normalizes column names for compatibility with Italian WMS exports
        """
        import logging
        logger = logging.getLogger(__name__)

        # Replace comma with dot for decimals (Italian format)
        csv_content_processed = csv_content

        # Read CSV
        df = pd.read_csv(
            StringIO(csv_content_processed),
            sep=',',
            encoding='utf-8-sig'  # Handle BOM
        )

        logger.info(f"CSV loaded with {len(df)} rows and {len(df.columns)} columns")
        logger.info(f"Original columns: {list(df.columns)}")

        # Normalize column names (Italian → Standard)
        df = InventoryService.normalize_column_names(df)

        logger.info(f"After normalization columns: {list(df.columns)}")

        # Check for lab_notes column
        lab_note_columns = [col for col in df.columns if 'note' in col.lower() or 'lab' in col.lower()]
        if lab_note_columns:
            logger.info(f"Found potential lab notes columns: {lab_note_columns}")
        else:
            logger.warning("No lab notes column found in CSV (searched for columns containing 'note' or 'lab')")

        return df

    @staticmethod
    def validate_percentage_field(value: Optional[float], field_name: str, article_code: str, lot_code: str, row_num: int) -> None:
        """
        Validate that percentage fields are in valid range (0-100)

        Args:
            value: Field value to validate
            field_name: Name of the field
            article_code: Article code for error message
            lot_code: Lot code for error message
            row_num: Row number in CSV for error message

        Raises:
            ValueError: If value is outside valid range
        """
        if value is not None:
            if value < 0 or value > 100:
                raise ValueError(
                    f"CSV Row {row_num} ({article_code}/{lot_code}): "
                    f"Field '{field_name}' has invalid value {value}. "
                    f"Percentage fields must be between 0 and 100. "
                    f"Check your CSV column mapping - this may indicate the wrong column is being read."
                )

    @staticmethod
    def dataframe_to_lots(
        df: pd.DataFrame,
        upload_id: UUID,
        db: Session
    ) -> List[InventoryLot]:
        """
        Convert DataFrame rows to InventoryLot objects

        Maps CSV columns from WMS to database fields
        """
        lots = []

        for row_num, row in enumerate(df.iterrows(), start=2):  # Start at 2 to account for header
            _, row = row  # Unpack tuple from iterrows

            # Extract article and lot code
            # Use direct indexing with pandas Series, not .get()
            article_code = str(row['SCO_ART']).strip() if 'SCO_ART' in row.index and pd.notna(row['SCO_ART']) else ''
            lot_code = str(row['SCO_LOTT']).strip() if 'SCO_LOTT' in row.index and pd.notna(row['SCO_LOTT']) else ''

            if not article_code or not lot_code:
                continue

            # Parse article code
            parsed = InventoryService.parse_article_code(article_code)

            # Helper to safely get value from row (handles pandas Series properly)
            def get_value(col_name, default=None):
                """Safely get value from pandas Series row"""
                if col_name in row.index:
                    val = row[col_name]

                    # Handle case where val is a Series (due to duplicate columns)
                    if isinstance(val, pd.Series):
                        # Get first non-null value from the Series
                        val = val.dropna().iloc[0] if not val.dropna().empty else None

                    if pd.notna(val):
                        return val
                return default

            # Helper to convert to float safely
            def to_float(col_name_or_val):
                """Convert column value or direct value to float"""
                # If it's a string (column name), get the value first
                if isinstance(col_name_or_val, str) and col_name_or_val in row.index:
                    val = get_value(col_name_or_val)
                else:
                    val = col_name_or_val

                if val is None or pd.isna(val):
                    return None
                # Convert to string first to handle all types safely
                val_str = str(val).strip()
                if not val_str or val_str.lower() == 'nan':
                    return None
                try:
                    # Handle Italian format (comma as decimal)
                    val_str = val_str.replace(',', '.')
                    return float(val_str)
                except:
                    return None

            # Helper to get first non-null value from multiple column names
            def get_first_value(*column_names):
                """Try multiple column names and return first non-null value from row"""
                for col_name in column_names:
                    if col_name in row.index:
                        val = row[col_name]

                        # Handle case where val is a Series (due to duplicate columns)
                        if isinstance(val, pd.Series):
                            # Get first non-null value from the Series
                            val = val.dropna().iloc[0] if not val.dropna().empty else None

                        # Check if value is valid (not NaN, not None, not empty string)
                        if pd.notna(val):
                            val_str = str(val).strip()
                            if val_str and val_str.lower() != 'nan':
                                return val_str
                return None

            # Extract and validate percentage fields
            dc_real = to_float('SCO_DownCluster_Real')
            duck_real = to_float('SCO_Duck')
            oe_real = to_float('SCO_OE')
            feather_real = to_float('SCO_Feather')
            dc_nominal = to_float('SCO_DownCluster_Nominal')

            # Validate percentage fields (0-100 range)
            InventoryService.validate_percentage_field(dc_real, 'dc_real (SCO_DownCluster_Real)', article_code, lot_code, row_num)
            InventoryService.validate_percentage_field(duck_real, 'duck_real (SCO_Duck)', article_code, lot_code, row_num)
            InventoryService.validate_percentage_field(oe_real, 'oe_real (SCO_OE)', article_code, lot_code, row_num)
            InventoryService.validate_percentage_field(feather_real, 'feather_real (SCO_Feather)', article_code, lot_code, row_num)
            InventoryService.validate_percentage_field(dc_nominal, 'dc_nominal (SCO_DownCluster_Nominal)', article_code, lot_code, row_num)

            # Create lot object
            lot = InventoryLot(
                upload_id=upload_id,
                article_code=article_code,
                lot_code=lot_code,
                description=get_first_value('SCO_DESC'),

                # Real values (use validated variables)
                dc_real=dc_real,
                fp_real=to_float('SCO_FillPower_Real'),
                duck_real=duck_real,
                oe_real=oe_real,
                feather_real=feather_real,
                oxygen_real=to_float('SCO_Oxygen'),
                turbidity_real=to_float('SCO_Turbidity'),

                # Nominal values (use validated variables + new fields)
                dc_nominal=dc_nominal,
                fp_nominal=to_float('SCO_FillPower_Nominal'),
                standard_nominal=get_first_value('SCO_Standard_Nominal'),

                # Additional quality
                total_fibres=to_float('SCO_TotalFibres'),
                broken=to_float('SCO_Broken'),
                landfowl=to_float('SCO_Landfowl'),

                # Business data
                available_kg=to_float('SCO_QTA') or 0,
                cost_per_kg=to_float('SCO_COSTO_KG'),

                # Metadata from parsed code
                group_code=parsed['group_code'],
                species=parsed['species'],
                color=parsed['color'],
                state=parsed['state'],
                certification=parsed['certification'],
                quality_nominal=get_first_value('SCO_QUALITA'),
                # Try multiple column name variants for lab notes (different CSV formats)
                lab_notes=get_first_value('SCO_NOTE_LAB', 'SCO_LabNote', 'LOT_LabNote', 'SCO_NoteLab', 'SCO_NOTE_LABORATORIO'),

                # Flags (will be set by imputation logic if needed)
                is_estimated=False,
                dc_was_imputed=False,
                fp_was_imputed=False,
                is_active=True
            )

            lots.append(lot)

        # Log statistics about lab_notes
        import logging
        logger = logging.getLogger(__name__)
        lots_with_notes = sum(1 for lot in lots if lot.lab_notes and lot.lab_notes.strip())
        logger.info(f"Processed {len(lots)} lots, {lots_with_notes} have lab_notes")
        if lots_with_notes > 0:
            logger.info(f"Sample lab_notes: {[lot.lab_notes[:50] for lot in lots if lot.lab_notes][:3]}")

        return lots

    @staticmethod
    def upload_csv(
        csv_content: str,
        filename: str,
        user: User,
        db: Session,
        notes: Optional[str] = None
    ) -> InventoryUpload:
        """
        Process CSV upload and store in database

        Args:
            csv_content: CSV file content as string
            filename: Original filename
            user: User who uploaded
            db: Database session
            notes: Optional notes

        Returns:
            InventoryUpload record
        """
        # Parse CSV
        df = InventoryService.csv_to_dataframe(csv_content)

        # Track original row count
        original_count = len(df)

        # Remove duplicates based on article_code + lot_code
        # Keep only the first occurrence of each combination
        df = df.drop_duplicates(subset=['SCO_ART', 'SCO_LOTT'], keep='first')

        # Calculate duplicates removed
        duplicates_removed = original_count - len(df)

        # Prepare notes with duplicate info
        upload_notes = notes or ""
        if duplicates_removed > 0:
            duplicate_info = f"\n[Auto] Removed {duplicates_removed} duplicate rows from CSV"
            upload_notes = (upload_notes + duplicate_info).strip()

        # Create upload record
        upload = InventoryUpload(
            uploaded_by=user.id,
            filename=filename,
            total_lots=len(df),  # Count after deduplication
            status="processing",
            notes=upload_notes
        )
        db.add(upload)
        db.flush()  # Get upload ID

        # Delete existing lots (hard delete)
        # This removes all previous inventory data before loading new CSV
        db.query(InventoryLot).delete()
        db.flush()  # Ensure delete is completed before insert

        # Convert to lots
        lots = InventoryService.dataframe_to_lots(df, upload.id, db)

        # Apply imputation logic (similar to optimizer_core)
        lots = InventoryService.apply_imputation(lots)

        # Add lots to database
        db.bulk_save_objects(lots)

        # Update upload status
        upload.status = "completed"

        db.commit()
        db.refresh(upload)

        return upload

    @staticmethod
    def apply_imputation(lots: List[InventoryLot]) -> List[InventoryLot]:
        """
        Apply imputation logic for missing DC/FP values
        Based on optimizer_core/inventory.py logic
        """
        for lot in lots:
            # Impute DC from nominal if missing
            if lot.dc_real is None and lot.dc_nominal is not None:
                lot.dc_real = lot.dc_nominal
                lot.dc_was_imputed = True
                lot.is_estimated = True

            # Impute FP from nominal if missing
            if lot.fp_real is None and lot.fp_nominal is not None:
                lot.fp_real = lot.fp_nominal
                lot.fp_was_imputed = True
                lot.is_estimated = True

            # Automatic corrections for duck% based on species
            if lot.species:
                # Pure duck (A) → duck = 100%
                if lot.species == 'A' and lot.duck_real is None:
                    lot.duck_real = 100.0

                # Pure goose (O) → duck = 0%
                if lot.species == 'O' and lot.duck_real is None:
                    lot.duck_real = 0.0

                # Mixed (OA) → duck = 50% default
                if lot.species == 'OA' and lot.duck_real is None:
                    lot.duck_real = 50.0

        return lots

    @staticmethod
    def get_inventory_stats(db: Session) -> Dict:
        """Get inventory statistics"""
        from sqlalchemy import func

        active_lots = db.query(InventoryLot).filter(InventoryLot.is_active == True)

        total_lots = active_lots.count()
        total_kg = db.query(func.sum(InventoryLot.available_kg)).filter(
            InventoryLot.is_active == True
        ).scalar() or 0

        avg_dc = db.query(func.avg(InventoryLot.dc_real)).filter(
            InventoryLot.is_active == True,
            InventoryLot.dc_real.isnot(None)
        ).scalar()

        avg_fp = db.query(func.avg(InventoryLot.fp_real)).filter(
            InventoryLot.is_active == True,
            InventoryLot.fp_real.isnot(None)
        ).scalar()

        # Count by species
        by_species = {}
        species_counts = db.query(
            InventoryLot.species,
            func.count(InventoryLot.id),
            func.sum(InventoryLot.available_kg)
        ).filter(
            InventoryLot.is_active == True
        ).group_by(InventoryLot.species).all()

        for species, count, kg in species_counts:
            by_species[species or 'unknown'] = {
                'count': count,
                'total_kg': float(kg or 0)
            }

        return {
            'total_lots': total_lots,
            'total_kg': float(total_kg),
            'avg_dc': float(avg_dc) if avg_dc else None,
            'avg_fp': float(avg_fp) if avg_fp else None,
            'by_species': by_species
        }
