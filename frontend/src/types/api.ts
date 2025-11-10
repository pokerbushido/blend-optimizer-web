// ============================================================================
// USER & AUTHENTICATION TYPES
// ============================================================================

export enum UserRole {
  ADMIN = 'admin',
  OPERATORE = 'operatore',
  VISUALIZZATORE = 'visualizzatore',
}

export interface User {
  id: number
  username: string
  email: string
  full_name: string
  role: UserRole
  is_active: boolean
  created_at: string
  last_login: string | null
}

export interface LoginRequest {
  username: string
  password: string
}

export interface Token {
  access_token: string
  token_type: string
}

export interface UserCreate {
  username: string
  email: string
  password: string
  full_name: string
  role: UserRole
}

export interface UserUpdate {
  email?: string
  full_name?: string
  role?: UserRole
  is_active?: boolean
}

export interface PasswordChange {
  old_password: string
  new_password: string
}

// ============================================================================
// INVENTORY TYPES
// ============================================================================

export type Species = 'O' | 'A' | 'OA' | 'C'
export type Color = 'B' | 'G' | 'PW' | 'NPW'
export type State = 'Disponibile' | 'Riservato' | 'Esaurito'
export type Certification = 'RDS' | 'GRS' | 'OEKO' | 'None'

export interface InventoryLot {
  id: number
  article_code: string
  description: string
  species: Species
  color: Color
  state: State
  certification: Certification | null
  water_repellent: boolean
  group_code: string | null

  // Real quality parameters
  dc_real: number
  fp_real: number
  duck_real: number | null
  oe_real: number | null
  feather_real: number | null
  oxygen_real: number | null
  turbidity_real: number | null
  residue_real: number | null
  fat_real: number | null
  fibers_long_real: number | null
  fibers_short_real: number | null

  // Nominal parameters
  dc_nominal: number | null
  fp_nominal: number | null

  // Business data
  available_kg: number
  reserved_kg: number
  cost_per_kg: number

  // Metadata
  is_estimated: boolean
  dc_was_imputed: boolean
  fp_was_imputed: boolean
  notes: string | null
  last_updated: string
  created_at: string
  upload_id: number | null
}

export interface InventoryUpload {
  id: number
  filename: string
  upload_timestamp: string
  uploaded_by_id: number
  uploaded_by_username: string
  total_lots: number
  status: 'success' | 'partial' | 'failed'
  notes: string | null
}

export interface InventoryStats {
  total_lots: number
  total_kg: number
  avg_dc: number
  avg_fp: number
  avg_cost_per_kg: number
  by_species: Record<Species, {
    count: number
    total_kg: number
    avg_dc: number
    avg_fp: number
  }>
  by_color: Record<Color, {
    count: number
    total_kg: number
  }>
}

export interface InventoryFilters {
  article_code?: string
  species?: Species
  color?: Color
  min_dc?: number
  max_dc?: number
  min_fp?: number
  max_fp?: number
  min_available_kg?: number
  water_repellent?: boolean
  certification?: Certification
  only_active?: boolean
  limit?: number
  offset?: number
}

// ============================================================================
// OPTIMIZATION TYPES
// ============================================================================

export interface BlendRequirements {
  // Product code (alternative to species/color)
  product_code?: string

  // Target specifications
  target_dc: number
  target_fp?: number | null
  target_duck?: number | null
  max_oe?: number | null  // Maximum Other Elements %

  // Constraints (optional when product_code is specified)
  species?: Species[]
  color?: Color[]
  water_repellent: boolean

  // Quantity
  total_kg: number

  // Options
  num_solutions?: number  // 1-10, default 3
  max_lots?: number       // 2-15, default 8
}

export interface BlendLot {
  lot_id: number
  article_code: string
  lot_code: string
  description: string
  species: Species
  color: Color

  // Quantities
  kg_used: number
  percentage: number

  // Real quality parameters
  dc_real: number
  fp_real: number
  duck_real: number | null
  oe_real: number | null

  // Nominal quality parameters
  dc_nominal: number | null
  fp_nominal: number | null
  duck_nominal: number | null
  standard_nominal: string | null
  quality_nominal: string | null

  // Cost
  cost_per_kg: number
  total_cost: number
}

export interface BlendSolution {
  solution_number: number
  lots: BlendLot[]

  // Aggregated quality
  aggregated_dc: number
  aggregated_fp: number
  aggregated_duck: number | null
  aggregated_oe: number | null

  // Compliance
  dc_delta: number
  fp_delta: number
  duck_delta: number | null
  oe_delta: number | null

  compliance_dc: boolean
  compliance_fp: boolean
  compliance_duck: boolean
  compliance_oe: boolean

  // Scoring
  score: number
  total_cost: number
  avg_cost_per_kg: number

  // Metadata
  num_lots: number
  computation_notes: string | null
}

export interface OptimizationRequest {
  id: string
  user_id: number
  requirements: BlendRequirements
  status: 'pending' | 'processing' | 'completed' | 'failed'
  created_at: string
  completed_at: string | null
  error_message: string | null
}

export interface OptimizationResult {
  request_id: string
  requirements: BlendRequirements
  solutions: BlendSolution[]
  generated_at: string
  computation_time_seconds: number
  total_combinations_evaluated: number
}

// ============================================================================
// API RESPONSE TYPES
// ============================================================================

export interface ApiError {
  detail: string
}

export interface PaginatedResponse<T> {
  items: T[]
  total: number
  limit: number
  offset: number
  has_more: boolean
}

export interface HealthStatus {
  status: 'healthy' | 'unhealthy'
  database: 'connected' | 'disconnected'
  redis: 'connected' | 'disconnected'
  timestamp: string
}

// ============================================================================
// FORM TYPES (for React Hook Form)
// ============================================================================

export interface LoginFormData {
  username: string
  password: string
}

export interface OptimizationFormData extends BlendRequirements {
  // Same as BlendRequirements but used for form state
}

export interface UserFormData {
  username: string
  email: string
  password?: string
  full_name: string
  role: UserRole
}

export interface UploadCSVFormData {
  file: File | null
  notes?: string
}
