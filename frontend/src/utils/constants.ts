import { Species, Color, UserRole } from '@/types/api'

// Use nginx proxy in production, direct connection in development
export const API_BASE_URL = import.meta.env.VITE_API_URL || '/api'

export const TOKEN_KEY = 'blend_optimizer_token'
export const USER_KEY = 'blend_optimizer_user'

// Species options
export const SPECIES_OPTIONS: { value: Species; label: string }[] = [
  { value: 'O', label: 'Oca' },
  { value: 'A', label: 'Anatra' },
  { value: 'OA', label: 'Oca/Anatra' },
  { value: 'C', label: 'Pollo' },
]

// Color options
export const COLOR_OPTIONS: { value: Color; label: string }[] = [
  { value: 'B', label: 'Bianco' },
  { value: 'G', label: 'Grigio' },
  { value: 'PW', label: 'Prevalentemente Bianco' },
  { value: 'NPW', label: 'Non Prevalentemente Bianco' },
]

// User role options
export const ROLE_OPTIONS: { value: UserRole; label: string }[] = [
  { value: UserRole.ADMIN, label: 'Amministratore' },
  { value: UserRole.OPERATORE, label: 'Operatore' },
  { value: UserRole.VISUALIZZATORE, label: 'Visualizzatore' },
]

// Certification options
export const CERTIFICATION_OPTIONS = [
  { value: 'RDS', label: 'RDS' },
  { value: 'GRS', label: 'GRS' },
  { value: 'OEKO', label: 'OEKO' },
  { value: 'None', label: 'Nessuna' },
]

// Default optimization values
export const DEFAULT_OPTIMIZATION = {
  DC_TOLERANCE: 3.0,
  FP_TOLERANCE: 5.0,
  DUCK_TOLERANCE: 5.0,
  NUM_SOLUTIONS: 3,
  MAX_LOTS: 8,
}

// Pagination
export const DEFAULT_PAGE_SIZE = 20
export const PAGE_SIZE_OPTIONS = [10, 20, 50, 100]
