import { useState } from 'react'
import { Link } from 'react-router-dom'
import { useAuth } from '@/hooks/useAuth'
import { useInventory } from '@/hooks/useInventory'
import Card from '@/components/ui/Card'
import Button from '@/components/ui/Button'
import Input from '@/components/ui/Input'
import Select from '@/components/ui/Select'
import Badge from '@/components/ui/Badge'
import Spinner from '@/components/ui/Spinner'
import { formatNumber, formatKg, formatCurrency } from '@/utils/formatters'
import { SPECIES_OPTIONS, COLOR_OPTIONS } from '@/utils/constants'
import type { Species, Color } from '@/types/api'

export default function Inventory() {
  const { isAdmin } = useAuth()
  const [filters, setFilters] = useState<{
    article_code?: string
    species?: Species
    color?: Color
    min_dc?: number
    max_dc?: number
    min_available_kg?: number
  }>({})

  const { lots, totalLots, isLoadingLots } = useInventory(filters)

  const handleFilterChange = (key: string, value: any) => {
    setFilters(prev => ({
      ...prev,
      [key]: value || undefined
    }))
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Inventario Lotti</h1>
          <p className="text-gray-600 mt-1">
            {totalLots} lotti disponibili
          </p>
        </div>
        {isAdmin() && (
          <Link to="/upload">
            <Button variant="primary">
              <svg className="w-5 h-5 mr-2 inline" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                      d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
              </svg>
              Carica CSV
            </Button>
          </Link>
        )}
      </div>

      {/* Filters */}
      <Card title="Filtri">
        <div className="grid grid-cols-1 md:grid-cols-3 lg:grid-cols-6 gap-4">
          <Input
            label="Codice Articolo"
            placeholder="Cerca..."
            value={filters.article_code || ''}
            onChange={(e) => handleFilterChange('article_code', e.target.value)}
          />

          <Select
            label="Specie"
            options={[{ value: '', label: 'Tutte' }, ...SPECIES_OPTIONS]}
            value={filters.species || ''}
            onChange={(e) => handleFilterChange('species', e.target.value)}
          />

          <Select
            label="Colore"
            options={[{ value: '', label: 'Tutti' }, ...COLOR_OPTIONS]}
            value={filters.color || ''}
            onChange={(e) => handleFilterChange('color', e.target.value)}
          />

          <Input
            label="DC Min %"
            type="number"
            placeholder="0"
            value={filters.min_dc || ''}
            onChange={(e) => handleFilterChange('min_dc', e.target.value ? parseFloat(e.target.value) : undefined)}
          />

          <Input
            label="DC Max %"
            type="number"
            placeholder="100"
            value={filters.max_dc || ''}
            onChange={(e) => handleFilterChange('max_dc', e.target.value ? parseFloat(e.target.value) : undefined)}
          />

          <Input
            label="Kg Min Disponibili"
            type="number"
            placeholder="0"
            value={filters.min_available_kg || ''}
            onChange={(e) => handleFilterChange('min_available_kg', e.target.value ? parseFloat(e.target.value) : undefined)}
          />
        </div>
      </Card>

      {/* Lots Table */}
      <Card>
        {isLoadingLots ? (
          <div className="flex justify-center py-12">
            <Spinner size="lg" />
          </div>
        ) : lots.length === 0 ? (
          <div className="text-center py-12">
            <p className="text-gray-600">Nessun lotto trovato con i filtri selezionati</p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Codice
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Descrizione
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Specie
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Colore
                  </th>
                  <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                    DC %
                  </th>
                  <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                    FP
                  </th>
                  <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Disponibile
                  </th>
                  <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Costo/kg
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Stato
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {lots.map((lot) => (
                  <tr key={lot.id} className="hover:bg-gray-50 transition-colors">
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                      {lot.article_code}
                    </td>
                    <td className="px-6 py-4 text-sm text-gray-900">
                      {lot.description}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-600">
                      {SPECIES_OPTIONS.find(s => s.value === lot.species)?.label}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-600">
                      {COLOR_OPTIONS.find(c => c.value === lot.color)?.label}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-right font-medium text-gray-900">
                      {formatNumber(lot.dc_real, 1)}%
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-right font-medium text-gray-900">
                      {formatNumber(lot.fp_real, 0)}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-right text-gray-900">
                      {formatKg(lot.available_kg)}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-right text-gray-900">
                      {formatCurrency(lot.cost_per_kg)}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <Badge variant={
                        lot.state === 'Disponibile' ? 'success' :
                        lot.state === 'Riservato' ? 'warning' : 'default'
                      }>
                        {lot.state}
                      </Badge>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </Card>
    </div>
  )
}
