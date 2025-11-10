"""
Blend optimization endpoints
"""
from typing import Dict
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
import json
import logging
from datetime import datetime
from io import BytesIO

from app.database import get_db
from app.models.models import User
from app.schemas.schemas import (
    BlendRequirements,
    OptimizationResult,
    OptimizationStatus
)
from app.core.security import require_operatore
from app.core.optimizer_service import OptimizerService
from app.core.excel_export_service import ExcelExportService

router = APIRouter(prefix="/optimize", tags=["optimization"])
logger = logging.getLogger(__name__)

# In-memory cache for optimization results (for simplicity)
# In production, use Redis or database
optimization_cache: Dict[UUID, OptimizationResult] = {}


@router.post("/blend", response_model=OptimizationResult, status_code=status.HTTP_200_OK)
async def optimize_blend(
    requirements: BlendRequirements,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_operatore)
):
    """
    Run blend optimization

    Finds optimal combinations of lots to meet requirements

    Args:
        requirements: Blend requirements (DC, FP, duck%, species, etc.)
        db: Database session
        current_user: Current authenticated user

    Returns:
        Optimization result with multiple solutions
    """
    try:
        result = OptimizerService.optimize_blend(requirements, db)

        # Cache result
        optimization_cache[result.request_id] = result

        return result

    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Optimization error: {str(e)}"
        )


@router.get("/{request_id}/status", response_model=OptimizationStatus)
async def get_optimization_status(
    request_id: UUID,
    _: User = Depends(require_operatore)
):
    """
    Get status of optimization request

    For future async implementation with Celery

    Args:
        request_id: Optimization request ID

    Returns:
        Status information
    """
    if request_id in optimization_cache:
        return OptimizationStatus(
            request_id=request_id,
            status="completed",
            progress=100,
            result=optimization_cache[request_id]
        )
    else:
        return OptimizationStatus(
            request_id=request_id,
            status="not_found",
            message="Optimization request not found or expired"
        )


@router.get("/{request_id}/results", response_model=OptimizationResult)
async def get_optimization_results(
    request_id: UUID,
    _: User = Depends(require_operatore)
):
    """
    Get optimization results by request ID

    Args:
        request_id: Optimization request ID

    Returns:
        Full optimization result
    """
    if request_id not in optimization_cache:
        raise HTTPException(
            status_code=404,
            detail="Optimization results not found or expired"
        )

    return optimization_cache[request_id]


@router.get("/{request_id}/excel")
async def download_excel(
    request_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_operatore)
):
    """
    Download optimization results as Excel file

    Args:
        request_id: Optimization request ID
        db: Database session
        current_user: Current authenticated user

    Returns:
        Excel file as download
    """
    logger.info(f"Excel download requested for optimization {request_id} by user {current_user.username}")

    if request_id not in optimization_cache:
        logger.warning(f"Optimization {request_id} not found in cache")
        raise HTTPException(
            status_code=404,
            detail="Optimization results not found or expired"
        )

    result = optimization_cache[request_id]

    try:
        # Generate Excel
        excel_bytes = ExcelExportService.generate_excel(result, db)

        # Generate filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"blend_optimization_{timestamp}.xlsx"

        logger.info(f"Excel file '{filename}' generated successfully for {request_id}, returning to client")

        # Return as streaming response
        return StreamingResponse(
            BytesIO(excel_bytes),
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={
                "Content-Disposition": f'attachment; filename="{filename}"'
            }
        )

    except Exception as e:
        logger.error(f"Excel generation failed for {request_id}: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error generating Excel: {str(e)}"
        )
