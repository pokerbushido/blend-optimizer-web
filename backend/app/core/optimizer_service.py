"""
Optimizer Service
Adapts optimizer_core for web API use with database
"""
import sys
import time
from typing import List, Dict, Optional
from decimal import Decimal
from dataclasses import dataclass, asdict
from sqlalchemy.orm import Session
from uuid import UUID, uuid4

# Add optimizer core to path
sys.path.insert(0, '/app/optimizer_core')
from optimizer import BlendOptimizer
from inventory import LotData, InventoryManager
from compatibility import parse_product_code

# Use app config values instead of optimizer core config
from app.config import settings
dc_tolerance = settings.DC_TOLERANCE
fp_tolerance = settings.FP_TOLERANCE
duck_tolerance = settings.DUCK_TOLERANCE
max_lots_per_blend = settings.MAX_LOTS_PER_BLEND
max_combinations = settings.MAX_COMBINATIONS

from app.models.models import InventoryLot
from app.schemas.schemas import (
    BlendRequirements,
    OptimizationResult,
    BlendSolution,
    BlendLot
)


class OptimizerService:
    """Service for blend optimization using optimizer_core"""

    @staticmethod
    def db_lot_to_lotdata(db_lot: InventoryLot) -> LotData:
        """
        Convert database InventoryLot to optimizer LotData

        Args:
            db_lot: InventoryLot from database

        Returns:
            LotData for optimizer
        """
        return LotData(
            article_code=db_lot.article_code,
            lot_code=db_lot.lot_code,
            description=db_lot.description or "",
            # Real values (use correct parameter names from LotData)
            dc_real=float(db_lot.dc_real) if db_lot.dc_real is not None else None,
            fp_real=float(db_lot.fp_real) if db_lot.fp_real is not None else None,
            duck_real=float(db_lot.duck_real) if db_lot.duck_real is not None else None,
            other_elements_real=float(db_lot.oe_real) if db_lot.oe_real is not None else None,
            feather_real=float(db_lot.feather_real) if db_lot.feather_real is not None else None,
            oxygen_real=float(db_lot.oxygen_real) if db_lot.oxygen_real is not None else None,
            turbidity_real=float(db_lot.turbidity_real) if db_lot.turbidity_real is not None else None,
            # Nominal values
            dc_nominal=float(db_lot.dc_nominal) if db_lot.dc_nominal is not None else None,
            fp_nominal=float(db_lot.fp_nominal) if db_lot.fp_nominal is not None else None,
            quality_nominal=db_lot.quality_nominal or "",
            # Additional quality
            total_fibres_real=float(db_lot.total_fibres) if db_lot.total_fibres is not None else None,
            broken_real=float(db_lot.broken) if db_lot.broken is not None else None,
            landfowl_real=float(db_lot.landfowl) if db_lot.landfowl is not None else None,
            # Business
            qty_available=float(db_lot.available_kg),
            cost_per_kg=float(db_lot.cost_per_kg) if db_lot.cost_per_kg is not None else None,
            # Metadata
            lab_notes=db_lot.lab_notes or "",
            # Flags
            is_estimated=db_lot.is_estimated,
            dc_was_imputed=db_lot.dc_was_imputed,
            fp_was_imputed=db_lot.fp_was_imputed
        )

    @staticmethod
    def load_lots_from_db(
        db: Session,
        requirements: Optional[BlendRequirements] = None
    ) -> List[LotData]:
        """
        Load active lots from database and convert to LotData

        Args:
            db: Database session
            requirements: Optional requirements to pre-filter

        Returns:
            List of LotData objects
        """
        query = db.query(InventoryLot).filter(
            InventoryLot.is_active == True,
            InventoryLot.available_kg > 0
        )

        # NOTE: NON filtriamo per species/color a livello database
        # L'optimizer core ha logica flessibile che usa duck_real e altri valori reali
        # per determinare la compatibilità. Il pre-filtro rigido eliminerebbe
        # candidati validi prima che l'algoritmo possa applicare la logica flessibile.
        #
        # Riferimento: optimizer_v33/optimizer.py:287-397 (_filter_candidates)

        # Exclude raw materials (group='G') if requested
        if requirements and requirements.exclude_raw_materials:
            query = query.filter(
                (InventoryLot.group_code != 'G') | (InventoryLot.group_code == None)
            )

        db_lots = query.all()

        # Convert to LotData
        lot_data_list = [OptimizerService.db_lot_to_lotdata(lot) for lot in db_lots]

        return lot_data_list

    @staticmethod
    def optimize_blend(
        requirements: BlendRequirements,
        db: Session
    ) -> OptimizationResult:
        """
        Run blend optimization

        Args:
            requirements: Blend requirements
            db: Database session

        Returns:
            Optimization result with solutions
        """
        start_time = time.time()
        request_id = uuid4()

        # Load lots from database
        inventory = OptimizerService.load_lots_from_db(db, requirements)

        if not inventory:
            raise ValueError("No suitable lots found in inventory for these requirements")

        # Create optimizer requirements dict
        optimizer_requirements = {}

        # Target parameters with correct naming for optimizer_core
        if requirements.target_dc is not None:
            optimizer_requirements['dc_target'] = float(requirements.target_dc)

        if requirements.target_fp is not None:
            optimizer_requirements['fp_target'] = float(requirements.target_fp)

        if requirements.target_duck is not None:
            optimizer_requirements['duck_target'] = float(requirements.target_duck)

        if requirements.max_oe is not None:
            optimizer_requirements['max_oe'] = float(requirements.max_oe)

        # Required quantity parameter
        optimizer_requirements['quantity_kg'] = float(requirements.total_kg)

        # Tolerance parameters from config
        optimizer_requirements['dc_tolerance'] = dc_tolerance
        optimizer_requirements['fp_tolerance'] = fp_tolerance
        optimizer_requirements['duck_tolerance'] = duck_tolerance

        # Max lots constraint
        if requirements.max_lots is not None:
            optimizer_requirements['max_lots'] = requirements.max_lots
        else:
            optimizer_requirements['max_lots'] = max_lots_per_blend

        # Product code parsing (preferred method - identical to MCP)
        if requirements.product_code:
            # Parse product code (e.g., "PAB" -> species='A', color='B', state='P')
            try:
                product = parse_product_code(requirements.product_code)
                optimizer_requirements['species'] = product.species
                optimizer_requirements['color'] = product.color
                optimizer_requirements['state'] = product.state
                print(f"✅ Parsed product code '{requirements.product_code}': species={product.species}, color={product.color}, state={product.state}")
            except Exception as e:
                print(f"⚠️  Failed to parse product code '{requirements.product_code}': {e}")
                # Fallback: use original logic below
        else:
            # Legacy logic: Species/Color from UI checkboxes
            # Species - passa SOLO se c'è esattamente un valore
            # Se ci sono più valori, non specificare (lascia che optimizer usi logica flessibile)
            if requirements.species and len(requirements.species) == 1:
                optimizer_requirements['species'] = requirements.species[0]
            elif requirements.species and len(requirements.species) > 1:
                # Più valori: non specificare, lascia che optimizer applichi logica flessibile
                pass

            # Color - passa SOLO se c'è esattamente un valore
            if requirements.color and len(requirements.color) == 1:
                optimizer_requirements['color'] = requirements.color[0]
            elif requirements.color and len(requirements.color) > 1:
                # Più valori: non specificare, lascia che optimizer applichi logica flessibile
                pass

            # State (material state: L/W/G)
            if requirements.state:
                optimizer_requirements['state'] = requirements.state

        # Water repellent (optional)
        if requirements.water_repellent is not None:
            optimizer_requirements['water_repellent'] = requirements.water_repellent

        # Create InventoryManager and populate with lots
        inventory_manager = InventoryManager()
        inventory_manager.lots = inventory

        # Create optimizer
        optimizer = BlendOptimizer(inventory_manager)

        # Debug logging
        print(f"\n🔍 DEBUG - Optimizer requirements: {optimizer_requirements}")
        print(f"🔍 DEBUG - Allow estimated: {requirements.allow_estimated}")
        print(f"🔍 DEBUG - Inventory lots: {len(inventory)}")

        # Run optimization with allow_estimated parameter and fallback strategy
        solutions = optimizer.optimize(
            requirements=optimizer_requirements,
            num_solutions=requirements.num_solutions,
            allow_estimated=requirements.allow_estimated
        )

        # If no solutions found, provide helpful error message
        if not solutions:
            # Check how many candidates were filtered with/without estimated data
            candidates_real = optimizer._filter_candidates(optimizer_requirements, allow_estimated=False)
            candidates_with_est = optimizer._filter_candidates(optimizer_requirements, allow_estimated=True)

            estimated_available = len(candidates_with_est) - len(candidates_real)

            print(f"❌ DEBUG - No solutions found")
            print(f"📊 DEBUG - Candidates (real only): {len(candidates_real)}")
            print(f"📊 DEBUG - Candidates (with estimated): {len(candidates_with_est)}")

            if estimated_available > 0 and not requirements.allow_estimated:
                raise ValueError(
                    f"No solution found with lab-tested data only. "
                    f"{estimated_available} additional lots with estimated values are available. "
                    f"Try enabling 'allow_estimated' option to include them."
                )
            elif len(candidates_real) == 0 and len(candidates_with_est) == 0:
                raise ValueError(
                    f"No compatible lots found in inventory. "
                    f"Please check that your inventory has lots matching the requirements "
                    f"(species, color, state, DC range)."
                )
            else:
                raise ValueError(
                    f"No valid blend combinations found with {len(candidates_real)} candidates. "
                    f"Try adjusting: (1) DC target or tolerance, (2) max_lots constraint, "
                    f"(3) quantity_kg, or (4) enable estimated data."
                )

        print(f"✅ DEBUG - Found {len(solutions)} solutions")

        # Convert solutions to API format
        api_solutions = []
        for idx, solution in enumerate(solutions, start=1):
            total_kg = float(requirements.total_kg)

            # Use pre-calculated values from BlendSolution
            avg_dc = solution.dc_average
            avg_fp = solution.fp_average
            avg_duck = solution.duck_average
            total_cost = solution.total_cost
            score = solution.score

            blend_lots = []
            for lot, kg_used in solution.lots:  # solution.lots is List[Tuple[LotData, float]]
                # Get original DB lot for ID
                db_lot = db.query(InventoryLot).filter(
                    InventoryLot.article_code == lot.article_code,
                    InventoryLot.lot_code == lot.lot_code,
                    InventoryLot.is_active == True
                ).first()

                if not db_lot:
                    continue

                percentage = (kg_used / total_kg) * 100

                # Calculate total cost for this lot
                lot_total_cost = None
                if lot.cost_per_kg:
                    lot_total_cost = Decimal(str(round(lot.cost_per_kg * kg_used, 2)))

                blend_lots.append(BlendLot(
                    lot_id=db_lot.id,
                    article_code=lot.article_code,
                    lot_code=lot.lot_code,
                    description=lot.description,
                    kg_used=Decimal(str(round(kg_used, 2))),
                    percentage=Decimal(str(round(percentage, 2))),
                    # Real quality values
                    dc_real=Decimal(str(lot.dc_real)) if lot.dc_real else None,
                    fp_real=Decimal(str(lot.fp_real)) if lot.fp_real else None,
                    duck_real=Decimal(str(lot.duck_real)) if lot.duck_real else None,
                    # Nominal values
                    dc_nominal=Decimal(str(lot.dc_nominal)) if lot.dc_nominal else None,
                    fp_nominal=Decimal(str(lot.fp_nominal)) if lot.fp_nominal else None,
                    duck_nominal=None,  # Not available in LotData
                    standard_nominal=db_lot.standard_nominal,
                    quality_nominal=db_lot.quality_nominal,
                    # Metadata
                    species=db_lot.species,
                    color=db_lot.color,
                    # Cost
                    cost_per_kg=Decimal(str(lot.cost_per_kg)) if lot.cost_per_kg else None,
                    total_cost=lot_total_cost
                ))

            # Calculate delta from targets (absolute difference)
            dc_delta = None
            fp_delta = None
            duck_delta = None
            oe_delta = None

            # Compliance checks
            compliance_dc = True
            compliance_fp = True
            compliance_duck = True
            compliance_oe = True

            if requirements.target_dc is not None:
                dc_diff = abs(avg_dc - float(requirements.target_dc))
                dc_delta = Decimal(str(round(dc_diff, 2)))
                compliance_dc = dc_diff <= dc_tolerance

            if requirements.target_fp is not None:
                fp_diff = abs(avg_fp - float(requirements.target_fp))
                fp_delta = Decimal(str(round(fp_diff, 1)))
                compliance_fp = fp_diff <= fp_tolerance

            if requirements.target_duck is not None:
                duck_diff = abs(avg_duck - float(requirements.target_duck))
                duck_delta = Decimal(str(round(duck_diff, 2)))
                compliance_duck = duck_diff <= duck_tolerance

            # Get aggregated_oe if available (may not be in all optimizer versions)
            avg_oe = getattr(solution, 'oe_average', None)

            # Check OE compliance (max_oe is a maximum constraint)
            if requirements.max_oe is not None and avg_oe is not None:
                oe_delta = Decimal(str(round(avg_oe, 2)))
                compliance_oe = avg_oe <= float(requirements.max_oe)

            api_solutions.append(BlendSolution(
                solution_number=idx,
                lots=blend_lots,
                num_lots=len(blend_lots),
                total_kg=Decimal(str(total_kg)),
                total_cost=Decimal(str(round(total_cost, 2))) if total_cost > 0 else None,
                avg_cost_per_kg=Decimal(str(round(total_cost / total_kg, 2))) if total_cost > 0 else None,
                # Aggregated quality (renamed from avg_*)
                aggregated_dc=Decimal(str(round(avg_dc, 2))) if avg_dc > 0 else None,
                aggregated_fp=Decimal(str(round(avg_fp, 1))) if avg_fp > 0 else None,
                aggregated_duck=Decimal(str(round(avg_duck, 2))) if avg_duck > 0 else None,
                aggregated_oe=Decimal(str(round(avg_oe, 2))) if avg_oe and avg_oe > 0 else None,
                # Delta from target
                dc_delta=dc_delta,
                fp_delta=fp_delta,
                duck_delta=duck_delta,
                oe_delta=oe_delta,
                # Compliance (match frontend naming: compliance_*)
                compliance_dc=compliance_dc,
                compliance_fp=compliance_fp,
                compliance_duck=compliance_duck,
                compliance_oe=compliance_oe,
                # Score
                score=score
            ))

        computation_time = time.time() - start_time

        return OptimizationResult(
            request_id=request_id,
            requirements=requirements,
            solutions=api_solutions,
            generated_at=time.time(),
            computation_time_seconds=round(computation_time, 2)
        )
