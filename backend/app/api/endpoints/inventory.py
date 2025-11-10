"""
Inventory endpoints
"""
from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_

from app.database import get_db
from app.models.models import User, InventoryLot as InventoryLotModel, InventoryUpload as InventoryUploadModel
from app.schemas.schemas import (
    InventoryLot,
    InventoryLotListItem,
    InventoryUpload,
    InventoryStats
)
from app.core.security import require_admin, require_visualizzatore
from app.core.inventory_service import InventoryService
from app.config import settings

router = APIRouter(prefix="/inventory", tags=["inventory"])


@router.post("/upload", response_model=InventoryUpload, status_code=status.HTTP_201_CREATED)
async def upload_csv(
    file: UploadFile = File(...),
    notes: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """
    Upload CSV inventory file (Admin only)

    Replaces existing inventory (soft delete old lots, insert new ones)

    Args:
        file: CSV file
        notes: Optional notes about this upload
        db: Database session
        current_user: Current authenticated admin user

    Returns:
        Upload record with statistics
    """
    # Validate file extension
    if not file.filename.endswith('.csv'):
        raise HTTPException(
            status_code=400,
            detail="Only CSV files are allowed"
        )

    # Read file content
    content = await file.read()
    try:
        csv_content = content.decode('utf-8-sig')  # Handle BOM
    except UnicodeDecodeError:
        try:
            csv_content = content.decode('latin-1')  # Fallback encoding
        except:
            raise HTTPException(
                status_code=400,
                detail="Unable to decode CSV file. Please ensure it's UTF-8 or Latin-1 encoded."
            )

    # Process upload
    import logging
    import traceback
    logger = logging.getLogger(__name__)

    try:
        logger.info(f"Starting CSV upload: {file.filename}")
        upload = InventoryService.upload_csv(
            csv_content=csv_content,
            filename=file.filename,
            user=current_user,
            db=db,
            notes=notes
        )
        logger.info(f"CSV upload successful: {upload.total_lots} lots")
        return upload
    except Exception as e:
        logger.error(f"CSV upload failed: {str(e)}")
        logger.error(traceback.format_exc())
        db.rollback()
        raise HTTPException(
            status_code=400,
            detail=f"Error processing CSV: {str(e)}"
        )


@router.get("/lots", response_model=List[InventoryLotListItem])
async def list_lots(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    article_code: Optional[str] = None,
    species: Optional[str] = None,
    min_dc: Optional[float] = None,
    max_dc: Optional[float] = None,
    min_available_kg: Optional[float] = None,
    only_active: bool = True,
    db: Session = Depends(get_db),
    _: User = Depends(require_visualizzatore)
):
    """
    List inventory lots with filters

    Args:
        skip: Number of records to skip (pagination)
        limit: Maximum number of records to return
        article_code: Filter by article code (partial match)
        species: Filter by species (O, A, OA, C)
        min_dc: Minimum DC %
        max_dc: Maximum DC %
        min_available_kg: Minimum available kg
        only_active: Only show active lots (default True)
        db: Database session

    Returns:
        List of inventory lots
    """
    query = db.query(InventoryLotModel)

    # Filters
    if only_active:
        query = query.filter(InventoryLotModel.is_active == True)

    if article_code:
        query = query.filter(InventoryLotModel.article_code.ilike(f"%{article_code}%"))

    if species:
        query = query.filter(InventoryLotModel.species == species)

    if min_dc is not None:
        query = query.filter(
            or_(
                InventoryLotModel.dc_real >= min_dc,
                InventoryLotModel.dc_nominal >= min_dc
            )
        )

    if max_dc is not None:
        query = query.filter(
            or_(
                InventoryLotModel.dc_real <= max_dc,
                InventoryLotModel.dc_nominal <= max_dc
            )
        )

    if min_available_kg is not None:
        query = query.filter(InventoryLotModel.available_kg >= min_available_kg)

    # Order by DC desc, then available kg desc
    query = query.order_by(
        InventoryLotModel.dc_real.desc().nullslast(),
        InventoryLotModel.available_kg.desc()
    )

    # Pagination
    lots = query.offset(skip).limit(limit).all()

    return lots


@router.get("/lots/{lot_id}", response_model=InventoryLot)
async def get_lot(
    lot_id: UUID,
    db: Session = Depends(get_db),
    _: User = Depends(require_visualizzatore)
):
    """
    Get detailed lot information by ID

    Args:
        lot_id: Lot UUID
        db: Database session

    Returns:
        Detailed lot data
    """
    lot = db.query(InventoryLotModel).filter(InventoryLotModel.id == lot_id).first()
    if not lot:
        raise HTTPException(status_code=404, detail="Lot not found")
    return lot


@router.get("/stats", response_model=InventoryStats)
async def get_stats(
    db: Session = Depends(get_db),
    _: User = Depends(require_visualizzatore)
):
    """
    Get inventory statistics

    Returns:
        Aggregate statistics about current inventory
    """
    stats = InventoryService.get_inventory_stats(db)
    return stats


@router.get("/uploads", response_model=List[InventoryUpload])
async def list_uploads(
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin)
):
    """
    List CSV upload history (Admin only)

    Args:
        skip: Number of records to skip
        limit: Maximum number of records to return
        db: Database session

    Returns:
        List of uploads
    """
    uploads = db.query(InventoryUploadModel)\
        .order_by(InventoryUploadModel.upload_timestamp.desc())\
        .offset(skip)\
        .limit(limit)\
        .all()
    return uploads
