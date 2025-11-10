"""
Excel Export Service
Adapts optimizer_core/excel_export.py for web API use
Generates Excel in-memory instead of file system
"""
import sys
import logging
from io import BytesIO
from sqlalchemy.orm import Session

# Add optimizer core to path
import os
optimizer_core_path = os.path.join(os.path.dirname(__file__), '..', '..', 'optimizer_core')
optimizer_core_path = os.path.abspath(optimizer_core_path)
if optimizer_core_path not in sys.path:
    sys.path.insert(0, optimizer_core_path)
from excel_export import export_solutions_to_excel
from inventory import LotData

from app.schemas.schemas import OptimizationResult, BlendSolution
from app.models.models import InventoryLot

logger = logging.getLogger(__name__)


class ExcelExportService:
    """Service for generating Excel exports"""

    @staticmethod
    def generate_excel(result: OptimizationResult, db: Session) -> bytes:
        """
        Generate Excel file from optimization result

        Args:
            result: Optimization result
            db: Database session

        Returns:
            Excel file as bytes
        """
        logger.info(f"Starting Excel generation for {len(result.solutions)} solution(s)")

        # Convert API format back to optimizer format
        solutions_optimizer_format = []

        for solution in result.solutions:
            # Get LotData objects for this solution
            combination = []
            allocations = []

            for blend_lot in solution.lots:
                # Fetch DB lot
                db_lot = db.query(InventoryLot).filter(
                    InventoryLot.id == blend_lot.lot_id
                ).first()

                if not db_lot:
                    logger.warning(f"Lot ID {blend_lot.lot_id} not found in database, skipping")
                    continue

                # Convert to LotData
                lot_data = LotData(
                    article_code=db_lot.article_code,
                    lot_code=db_lot.lot_code,
                    description=db_lot.description or "",
                    dc_real=float(db_lot.dc_real) if db_lot.dc_real else None,
                    fp_real=float(db_lot.fp_real) if db_lot.fp_real else None,
                    duck_real=float(db_lot.duck_real) if db_lot.duck_real else None,
                    other_elements_real=float(db_lot.oe_real) if db_lot.oe_real else None,
                    feather_real=float(db_lot.feather_real) if db_lot.feather_real else None,
                    oxygen_real=float(db_lot.oxygen_real) if db_lot.oxygen_real else None,
                    turbidity_real=float(db_lot.turbidity_real) if db_lot.turbidity_real else None,
                    dc_nominal=float(db_lot.dc_nominal) if db_lot.dc_nominal else None,
                    fp_nominal=float(db_lot.fp_nominal) if db_lot.fp_nominal else None,
                    quality_nominal=db_lot.quality_nominal or "",
                    standard_nominal=db_lot.standard_nominal or "",
                    total_fibres_real=float(db_lot.total_fibres) if db_lot.total_fibres else None,
                    broken_real=float(db_lot.broken) if db_lot.broken else None,
                    landfowl_real=float(db_lot.landfowl) if db_lot.landfowl else None,
                    qty_available=float(db_lot.available_kg),
                    cost_per_kg=float(db_lot.cost_per_kg) if db_lot.cost_per_kg else None,
                    lab_notes=db_lot.lab_notes or "",
                    is_estimated=db_lot.is_estimated,
                    dc_was_imputed=db_lot.dc_was_imputed,
                    fp_was_imputed=db_lot.fp_was_imputed
                )

                combination.append(lot_data)
                allocations.append(float(blend_lot.kg_used))

            solutions_optimizer_format.append((
                combination,
                allocations,
                solution.score
            ))

        # Extract requirements
        requirements_dict = {}
        if result.requirements.target_dc:
            requirements_dict['dc'] = float(result.requirements.target_dc)
        if result.requirements.target_fp:
            requirements_dict['fp'] = float(result.requirements.target_fp)
        if result.requirements.target_duck:
            requirements_dict['duck'] = float(result.requirements.target_duck)
        if result.requirements.species:
            # Join species list into comma-separated string for export
            requirements_dict['species'] = ', '.join(result.requirements.species)

        logger.debug(f"Converted {len(solutions_optimizer_format)} solutions to optimizer format")
        logger.debug(f"Requirements: {requirements_dict}")

        # Generate Excel to BytesIO instead of file
        output = BytesIO()

        # Use optimizer_core export function
        # We need to modify it slightly to return bytes instead of saving to file
        # For now, we'll create a temporary workaround

        import tempfile
        import os

        with tempfile.NamedTemporaryFile(delete=False, suffix='.xlsx') as tmp:
            tmp_path = tmp.name

        try:
            logger.info(f"Generating Excel file to temporary path: {tmp_path}")
            # Export to temporary file
            export_solutions_to_excel(
                solutions=solutions_optimizer_format,
                requirements=requirements_dict,
                output_path=tmp_path
            )

            # Read file to bytes
            with open(tmp_path, 'rb') as f:
                excel_bytes = f.read()

            logger.info(f"Excel file generated successfully, size: {len(excel_bytes)} bytes")

        except Exception as e:
            logger.error(f"Failed to generate Excel file: {str(e)}", exc_info=True)
            raise

        finally:
            # Clean up temp file
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)
                logger.debug(f"Cleaned up temporary file: {tmp_path}")

        return excel_bytes
