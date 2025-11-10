import { useInventory } from '@/hooks/useInventory'
import Card from '@/components/ui/Card'
import Spinner from '@/components/ui/Spinner'
import { formatNumber, formatKg } from '@/utils/formatters'

export default function Stats() {
  const { stats, isLoadingStats } = useInventory()

  if (isLoadingStats) {
    return (
      <div className="flex justify-center py-12">
        <Spinner size="lg" />
      </div>
    )
  }

  if (!stats) {
    return (
      <Card>
        <div className="text-center py-12">
          <p className="text-gray-600">Nessun dato disponibile</p>
        </div>
      </Card>
    )
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-gray-900">Statistiche Avanzate</h1>
        <p className="text-gray-600 mt-1">
          Analisi dettagliata dell'inventario
        </p>
      </div>

      {/* Overview */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <Card>
          <div className="text-sm font-medium text-gray-600 mb-2">Lotti Totali</div>
          <div className="text-4xl font-bold text-gray-900">{stats.total_lots}</div>
        </Card>

        <Card>
          <div className="text-sm font-medium text-gray-600 mb-2">Quantità Totale</div>
          <div className="text-4xl font-bold text-gray-900">{formatKg(stats.total_kg)}</div>
        </Card>

        <Card>
          <div className="text-sm font-medium text-gray-600 mb-2">DC Medio</div>
          <div className="text-4xl font-bold text-primary-600">{formatNumber(stats.avg_dc, 1)}%</div>
        </Card>

        <Card>
          <div className="text-sm font-medium text-gray-600 mb-2">FP Medio</div>
          <div className="text-4xl font-bold text-primary-600">{formatNumber(stats.avg_fp, 0)}</div>
        </Card>
      </div>

      {/* Species Analysis */}
      <Card title="Analisi per Specie">
        <div className="space-y-6">
          {Object.entries(stats.by_species).map(([species, data]) => {
            const speciesLabel = species === 'O' ? 'Oca' : species === 'A' ? 'Anatra' : species === 'OA' ? 'Oca/Anatra' : 'Pollo'
            const percentage = (data.total_kg / stats.total_kg) * 100

            return (
              <div key={species} className="border-b border-gray-200 pb-6 last:border-0">
                <div className="flex items-center justify-between mb-3">
                  <h3 className="text-lg font-semibold text-gray-900">{speciesLabel}</h3>
                  <span className="text-sm text-gray-600">{formatNumber(percentage, 1)}% del totale</span>
                </div>

                {/* Progress bar */}
                <div className="w-full bg-gray-200 rounded-full h-2 mb-4">
                  <div
                    className="bg-primary-600 h-2 rounded-full transition-all"
                    style={{ width: `${percentage}%` }}
                  />
                </div>

                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                  <div>
                    <div className="text-sm text-gray-600">Lotti</div>
                    <div className="text-xl font-semibold text-gray-900">{data.count}</div>
                  </div>
                  <div>
                    <div className="text-sm text-gray-600">Quantità</div>
                    <div className="text-xl font-semibold text-gray-900">{formatKg(data.total_kg)}</div>
                  </div>
                  <div>
                    <div className="text-sm text-gray-600">DC Medio</div>
                    <div className="text-xl font-semibold text-gray-900">{formatNumber(data.avg_dc, 1)}%</div>
                  </div>
                  <div>
                    <div className="text-sm text-gray-600">FP Medio</div>
                    <div className="text-xl font-semibold text-gray-900">{formatNumber(data.avg_fp, 0)}</div>
                  </div>
                </div>
              </div>
            )
          })}
        </div>
      </Card>

      {/* Color Distribution */}
      <Card title="Distribuzione per Colore">
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          {Object.entries(stats.by_color).map(([color, data]) => {
            const colorLabel = color === 'B' ? 'Bianco' : color === 'G' ? 'Grigio' : color === 'PW' ? 'Prev. Bianco' : 'Non Prev. Bianco'
            const percentage = (data.total_kg / stats.total_kg) * 100

            return (
              <div key={color} className="border border-gray-200 rounded-lg p-4">
                <div className="text-lg font-semibold text-gray-900 mb-2">{colorLabel}</div>
                <div className="space-y-2">
                  <div>
                    <div className="text-xs text-gray-600">Lotti</div>
                    <div className="text-lg font-medium text-gray-900">{data.count}</div>
                  </div>
                  <div>
                    <div className="text-xs text-gray-600">Quantità</div>
                    <div className="text-lg font-medium text-gray-900">{formatKg(data.total_kg)}</div>
                  </div>
                  <div>
                    <div className="text-xs text-gray-600">% Totale</div>
                    <div className="text-lg font-medium text-primary-600">{formatNumber(percentage, 1)}%</div>
                  </div>
                </div>
              </div>
            )
          })}
        </div>
      </Card>

      {/* Quality Distribution */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <Card title="Distribuzione Down Cluster (DC)">
          <div className="space-y-4">
            {[
              { range: '< 80%', min: 0, max: 80, color: 'bg-red-500' },
              { range: '80-85%', min: 80, max: 85, color: 'bg-orange-500' },
              { range: '85-90%', min: 85, max: 90, color: 'bg-yellow-500' },
              { range: '90-95%', min: 90, max: 95, color: 'bg-green-500' },
              { range: '> 95%', min: 95, max: 100, color: 'bg-emerald-500' },
            ].map((range) => {
              // Mock data for visualization
              const lotsInRange = Math.floor(Math.random() * 20) + 5
              const percentage = (lotsInRange / stats.total_lots) * 100

              return (
                <div key={range.range}>
                  <div className="flex justify-between items-center mb-1">
                    <span className="text-sm font-medium text-gray-700">{range.range}</span>
                    <span className="text-sm text-gray-600">{lotsInRange} lotti</span>
                  </div>
                  <div className="w-full bg-gray-200 rounded-full h-2">
                    <div
                      className={`${range.color} h-2 rounded-full transition-all`}
                      style={{ width: `${percentage}%` }}
                    />
                  </div>
                </div>
              )
            })}
          </div>
        </Card>

        <Card title="Distribuzione Fill Power (FP)">
          <div className="space-y-4">
            {[
              { range: '< 600', min: 0, max: 600, color: 'bg-red-500' },
              { range: '600-700', min: 600, max: 700, color: 'bg-orange-500' },
              { range: '700-800', min: 700, max: 800, color: 'bg-yellow-500' },
              { range: '800-900', min: 800, max: 900, color: 'bg-green-500' },
              { range: '> 900', min: 900, max: 1000, color: 'bg-emerald-500' },
            ].map((range) => {
              // Mock data for visualization
              const lotsInRange = Math.floor(Math.random() * 20) + 5
              const percentage = (lotsInRange / stats.total_lots) * 100

              return (
                <div key={range.range}>
                  <div className="flex justify-between items-center mb-1">
                    <span className="text-sm font-medium text-gray-700">{range.range}</span>
                    <span className="text-sm text-gray-600">{lotsInRange} lotti</span>
                  </div>
                  <div className="w-full bg-gray-200 rounded-full h-2">
                    <div
                      className={`${range.color} h-2 rounded-full transition-all`}
                      style={{ width: `${percentage}%` }}
                    />
                  </div>
                </div>
              )
            })}
          </div>
        </Card>
      </div>
    </div>
  )
}
