"""
Pydantic Schemas for Request/Response validation
"""
from pydantic import BaseModel, Field, validator
from typing import Optional, List
from datetime import datetime
from uuid import UUID
from decimal import Decimal
from app.models.models import UserRole
import re


# ============================================================================
# User Schemas
# ============================================================================

class UserBase(BaseModel):
    """Base user schema"""
    username: str = Field(..., min_length=3, max_length=50)
    email: str = Field(..., pattern=r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$')
    full_name: Optional[str] = Field(None, max_length=100)
    role: UserRole = UserRole.VISUALIZZATORE


class UserCreate(UserBase):
    """Schema for creating a new user"""
    password: str = Field(..., min_length=8, max_length=100)


class UserUpdate(BaseModel):
    """Schema for updating user"""
    email: Optional[str] = Field(None, pattern=r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$')
    full_name: Optional[str] = None
    role: Optional[UserRole] = None
    is_active: Optional[bool] = None


class UserPasswordUpdate(BaseModel):
    """Schema for password update"""
    old_password: str
    new_password: str = Field(..., min_length=8, max_length=100)


class User(UserBase):
    """User response schema"""
    id: UUID
    is_active: bool
    created_at: datetime
    last_login: Optional[datetime] = None

    class Config:
        from_attributes = True


# ============================================================================
# Authentication Schemas
# ============================================================================

class Token(BaseModel):
    """JWT token response"""
    access_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    """Token payload data"""
    username: Optional[str] = None
    role: Optional[UserRole] = None


class LoginRequest(BaseModel):
    """Login request"""
    username: str
    password: str


# ============================================================================
# Inventory Lot Schemas
# ============================================================================

class InventoryLotBase(BaseModel):
    """Base inventory lot schema"""
    article_code: str = Field(..., max_length=50)
    lot_code: str = Field(..., max_length=100)
    description: Optional[str] = None

    # Real values
    dc_real: Optional[Decimal] = Field(None, ge=0, le=100)
    fp_real: Optional[Decimal] = Field(None, ge=0)
    duck_real: Optional[Decimal] = Field(None, ge=0, le=100)
    oe_real: Optional[Decimal] = Field(None, ge=0, le=100)
    feather_real: Optional[Decimal] = Field(None, ge=0, le=100)
    oxygen_real: Optional[Decimal] = Field(None, ge=0)
    turbidity_real: Optional[Decimal] = Field(None, ge=0)

    # Nominal values
    dc_nominal: Optional[Decimal] = Field(None, ge=0, le=100)
    fp_nominal: Optional[Decimal] = Field(None, ge=0)
    standard_nominal: Optional[str] = None

    # Additional quality
    total_fibres: Optional[Decimal] = None
    broken: Optional[Decimal] = None
    landfowl: Optional[Decimal] = None

    # Business data
    available_kg: Decimal = Field(..., ge=0)
    cost_per_kg: Optional[Decimal] = Field(None, ge=0)

    # Metadata
    group_code: Optional[str] = Field(None, max_length=10)
    species: Optional[str] = Field(None, max_length=10)
    color: Optional[str] = Field(None, max_length=10)
    state: Optional[str] = Field(None, max_length=10)
    certification: Optional[str] = Field(None, max_length=20)
    quality_nominal: Optional[str] = None
    lab_notes: Optional[str] = None

    # Flags
    is_estimated: bool = False
    dc_was_imputed: bool = False
    fp_was_imputed: bool = False


class InventoryLot(InventoryLotBase):
    """Full inventory lot with timestamps"""
    id: UUID
    upload_id: Optional[UUID] = None
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class InventoryLotListItem(BaseModel):
    """Simplified lot for list views"""
    id: UUID
    article_code: str
    lot_code: str
    description: Optional[str]
    dc_real: Optional[Decimal]
    fp_real: Optional[Decimal]
    duck_real: Optional[Decimal]
    available_kg: Decimal
    species: Optional[str]
    is_active: bool

    class Config:
        from_attributes = True


class InventoryStats(BaseModel):
    """Inventory statistics"""
    total_lots: int
    total_kg: Decimal
    avg_dc: Optional[Decimal]
    avg_fp: Optional[Decimal]
    by_species: dict


# ============================================================================
# Inventory Upload Schemas
# ============================================================================

class InventoryUploadCreate(BaseModel):
    """Schema for creating upload record"""
    filename: str
    total_lots: int
    notes: Optional[str] = None


class InventoryUpload(BaseModel):
    """Upload response schema"""
    id: UUID
    uploaded_by: UUID
    filename: str
    upload_timestamp: datetime
    total_lots: int
    status: str
    notes: Optional[str]

    class Config:
        from_attributes = True


# ============================================================================
# Optimization Schemas
# ============================================================================

class BlendRequirements(BaseModel):
    """Requirements for blend optimization"""
    # Product code (alternative to species/color/state)
    product_code: Optional[str] = Field(None, description="Product code (e.g., PAB, POB, POAG) - alternative to species/color")

    # Target parameters
    target_dc: Optional[Decimal] = Field(None, ge=0, le=100, description="Target Down Cluster %")
    target_fp: Optional[Decimal] = Field(None, ge=0, description="Target Fill Power")
    target_duck: Optional[Decimal] = Field(None, ge=0, le=100, description="Target Duck %")
    max_oe: Optional[Decimal] = Field(None, ge=0, le=100, description="Maximum Other Elements %")

    # Constraints (optional when product_code is specified)
    species: Optional[List[str]] = Field(None, description="List of species: O, A, OA, C")
    color: Optional[List[str]] = Field(None, description="List of colors: B, G, PW, NPW")
    state: Optional[str] = Field(None, description="Material state: L (Lavato), W (Washed), G (Grezzo)")
    water_repellent: Optional[bool] = Field(None, description="GWR/NWR required")
    exclude_raw_materials: bool = Field(True, description="Exclude group='G'")

    # Quantity
    total_kg: Decimal = Field(..., gt=0, description="Total kg required")

    # Optimization options
    allow_estimated: bool = Field(False, description="Allow use of lots with estimated DC/FP values")

    # Options
    num_solutions: int = Field(3, ge=1, le=10, description="Number of solutions to generate")
    max_lots: int = Field(10, ge=2, le=15, description="Max lots per blend")

    @validator('species')
    def validate_species(cls, v):
        if v:
            valid_species = {'O', 'A', 'OA', 'C'}
            for species in v:
                if species not in valid_species:
                    raise ValueError(f"Species '{species}' is not valid. Must be one of: O, A, OA, C")
        return v

    @validator('color')
    def validate_color(cls, v):
        if v:
            valid_colors = {'B', 'G', 'PW', 'NPW'}
            for color in v:
                if color not in valid_colors:
                    raise ValueError(f"Color '{color}' is not valid. Must be one of: B, G, PW, NPW")
        return v


class BlendLot(BaseModel):
    """Single lot in a blend solution"""
    lot_id: UUID
    article_code: str
    lot_code: str
    description: Optional[str]
    kg_used: Decimal
    percentage: Decimal

    # Real quality values
    dc_real: Optional[Decimal]
    fp_real: Optional[Decimal]
    duck_real: Optional[Decimal]

    # Nominal values
    dc_nominal: Optional[Decimal]
    fp_nominal: Optional[Decimal]
    duck_nominal: Optional[Decimal]
    standard_nominal: Optional[str]
    quality_nominal: Optional[str]

    # Metadata
    species: Optional[str]
    color: Optional[str]

    # Cost
    cost_per_kg: Optional[Decimal]
    total_cost: Optional[Decimal]  # cost_per_kg * kg_used


class BlendSolution(BaseModel):
    """Single blend optimization solution"""
    solution_number: int
    lots: List[BlendLot]
    num_lots: int  # Number of lots in this solution
    total_kg: Decimal
    total_cost: Optional[Decimal]
    avg_cost_per_kg: Optional[Decimal]  # Renamed from cost_per_kg

    # Aggregated quality (weighted by kg_used)
    aggregated_dc: Optional[Decimal]  # Renamed from avg_dc
    aggregated_fp: Optional[Decimal]  # Renamed from avg_fp
    aggregated_duck: Optional[Decimal]  # Renamed from avg_duck
    aggregated_oe: Optional[Decimal]  # Added

    # Delta from target (absolute difference)
    dc_delta: Optional[Decimal]
    fp_delta: Optional[Decimal]
    duck_delta: Optional[Decimal]
    oe_delta: Optional[Decimal]

    # Compliance (match frontend naming: compliance_*)
    compliance_dc: bool
    compliance_fp: bool
    compliance_duck: bool
    compliance_oe: bool

    # Score
    score: float


class OptimizationResult(BaseModel):
    """Complete optimization result"""
    request_id: UUID
    requirements: BlendRequirements
    solutions: List[BlendSolution]
    generated_at: datetime
    computation_time_seconds: float


class OptimizationStatus(BaseModel):
    """Status of async optimization task"""
    request_id: UUID
    status: str  # pending, processing, completed, failed
    progress: Optional[int] = None  # 0-100
    message: Optional[str] = None
    result: Optional[OptimizationResult] = None
