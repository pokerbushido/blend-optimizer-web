import { Link } from 'react-router-dom'
import { useAuth } from '@/hooks/useAuth'
import { useInventory } from '@/hooks/useInventory'
import Card from '@/components/ui/Card'
import Spinner from '@/components/ui/Spinner'
import { formatNumber, formatKg } from '@/utils/formatters'

export default function Dashboard() {
  const { user, isAdmin } = useAuth()
  const { stats, isLoadingStats } = useInventory()

  return (
    <div className="space-y-6">
      {/* Welcome */}
      <div>
        <h1 className="text-3xl font-bold text-gray-900">
          Benvenuto, {user?.full_name}
        </h1>
        <p className="text-gray-600 mt-1">
          Dashboard Sistema Ottimizzazione Piuma
        </p>
      </div>

      {/* Stats Grid */}
      {isLoadingStats ? (
        <div className="flex justify-center py-12">
          <Spinner size="lg" />
        </div>
      ) : stats ? (
        <>
          {/* Overview Stats */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            <Card>
              <div className="text-sm font-medium text-gray-600">Lotti Totali</div>
              <div className="text-3xl font-bold text-gray-900 mt-2">
                {stats.total_lots}
              </div>
            </Card>

            <Card>
              <div className="text-sm font-medium text-gray-600">Quantità Totale</div>
              <div className="text-3xl font-bold text-gray-900 mt-2">
                {formatKg(stats.total_kg)}
              </div>
            </Card>

            <Card>
              <div className="text-sm font-medium text-gray-600">DC Medio</div>
              <div className="text-3xl font-bold text-gray-900 mt-2">
                {formatNumber(stats.avg_dc, 1)}%
              </div>
            </Card>

            <Card>
              <div className="text-sm font-medium text-gray-600">FP Medio</div>
              <div className="text-3xl font-bold text-gray-900 mt-2">
                {formatNumber(stats.avg_fp, 0)}
              </div>
            </Card>
          </div>

          {/* Species Breakdown */}
          <Card title="Distribuzione per Specie">
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
              {Object.entries(stats.by_species).map(([species, data]) => (
                <div key={species} className="border border-gray-200 rounded-lg p-4">
                  <div className="text-lg font-semibold text-gray-900 mb-2">
                    {species === 'O' ? 'Oca' : species === 'A' ? 'Anatra' : species === 'OA' ? 'Oca/Anatra' : 'Pollo'}
                  </div>
                  <div className="space-y-1 text-sm">
                    <div className="flex justify-between">
                      <span className="text-gray-600">Lotti:</span>
                      <span className="font-medium">{data.count}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-600">Quantità:</span>
                      <span className="font-medium">{formatKg(data.total_kg)}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-600">DC medio:</span>
                      <span className="font-medium">{formatNumber(data.avg_dc, 1)}%</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-600">FP medio:</span>
                      <span className="font-medium">{formatNumber(data.avg_fp, 0)}</span>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </Card>
        </>
      ) : (
        <Card>
          <div className="text-center py-12">
            <p className="text-gray-600 mb-4">Nessun dato inventario disponibile</p>
            <Link to="/upload" className="text-primary-600 hover:text-primary-700 font-medium">
              Carica il tuo primo CSV
            </Link>
          </div>
        </Card>
      )}

      {/* Quick Actions */}
      <Card title="Azioni Rapide">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <Link
            to="/inventory"
            className="flex items-center p-4 border-2 border-gray-200 rounded-lg hover:border-primary-500 hover:bg-primary-50 transition-all group"
          >
            <div className="flex-shrink-0 w-10 h-10 bg-primary-100 rounded-lg flex items-center justify-center group-hover:bg-primary-200">
              <svg className="w-6 h-6 text-primary-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
              </svg>
            </div>
            <div className="ml-4">
              <div className="font-semibold text-gray-900">Visualizza Inventario</div>
              <div className="text-sm text-gray-600">Esplora i lotti disponibili</div>
            </div>
          </Link>

          <Link
            to="/optimize"
            className="flex items-center p-4 border-2 border-gray-200 rounded-lg hover:border-primary-500 hover:bg-primary-50 transition-all group"
          >
            <div className="flex-shrink-0 w-10 h-10 bg-primary-100 rounded-lg flex items-center justify-center group-hover:bg-primary-200">
              <svg className="w-6 h-6 text-primary-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 7h6m0 10v-3m-3 3h.01M9 17h.01M9 14h.01M12 14h.01M15 11h.01M12 11h.01M9 11h.01M7 21h10a2 2 0 002-2V5a2 2 0 00-2-2H7a2 2 0 00-2 2v14a2 2 0 002 2z" />
              </svg>
            </div>
            <div className="ml-4">
              <div className="font-semibold text-gray-900">Crea Ottimizzazione</div>
              <div className="text-sm text-gray-600">Ottimizza un nuovo blend</div>
            </div>
          </Link>

          <Link
            to="/history"
            className="flex items-center p-4 border-2 border-gray-200 rounded-lg hover:border-primary-500 hover:bg-primary-50 transition-all group"
          >
            <div className="flex-shrink-0 w-10 h-10 bg-primary-100 rounded-lg flex items-center justify-center group-hover:bg-primary-200">
              <svg className="w-6 h-6 text-primary-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
            </div>
            <div className="ml-4">
              <div className="font-semibold text-gray-900">Cronologia</div>
              <div className="text-sm text-gray-600">Visualizza ottimizzazioni passate</div>
            </div>
          </Link>

          {isAdmin() && (
            <Link
              to="/upload"
              className="flex items-center p-4 border-2 border-gray-200 rounded-lg hover:border-primary-500 hover:bg-primary-50 transition-all group"
            >
              <div className="flex-shrink-0 w-10 h-10 bg-primary-100 rounded-lg flex items-center justify-center group-hover:bg-primary-200">
                <svg className="w-6 h-6 text-primary-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
                </svg>
              </div>
              <div className="ml-4">
                <div className="font-semibold text-gray-900">Carica Inventario</div>
                <div className="text-sm text-gray-600">Importa dati CSV</div>
              </div>
            </Link>
          )}
        </div>
      </Card>
    </div>
  )
}
