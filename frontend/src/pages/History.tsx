import { Link } from 'react-router-dom'
import Card from '@/components/ui/Card'
import Badge from '@/components/ui/Badge'
import { formatDateTime, formatNumber } from '@/utils/formatters'

// Mock data for now - in real app would fetch from API
const mockHistory = [
  {
    id: '123e4567-e89b-12d3-a456-426614174000',
    created_at: new Date(Date.now() - 2 * 60 * 60 * 1000).toISOString(),
    target_dc: 90,
    target_fp: 750,
    total_kg: 100,
    status: 'completed',
    num_solutions: 3,
    computation_time: 2.5,
  },
  {
    id: '123e4567-e89b-12d3-a456-426614174001',
    created_at: new Date(Date.now() - 24 * 60 * 60 * 1000).toISOString(),
    target_dc: 85,
    target_fp: 700,
    total_kg: 150,
    status: 'completed',
    num_solutions: 5,
    computation_time: 3.2,
  },
  {
    id: '123e4567-e89b-12d3-a456-426614174002',
    created_at: new Date(Date.now() - 3 * 24 * 60 * 60 * 1000).toISOString(),
    target_dc: 92,
    target_fp: 800,
    total_kg: 80,
    status: 'failed',
    num_solutions: 0,
    computation_time: 1.1,
  },
]

export default function History() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-gray-900">Cronologia Ottimizzazioni</h1>
        <p className="text-gray-600 mt-1">
          Storico delle ottimizzazioni effettuate
        </p>
      </div>

      <Card>
        {mockHistory.length === 0 ? (
          <div className="text-center py-12">
            <p className="text-gray-600 mb-4">Nessuna ottimizzazione effettuata</p>
            <Link to="/optimize" className="text-primary-600 hover:text-primary-700 font-medium">
              Crea la tua prima ottimizzazione
            </Link>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                    Data
                  </th>
                  <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase">
                    DC Target
                  </th>
                  <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase">
                    FP Target
                  </th>
                  <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase">
                    Kg Totali
                  </th>
                  <th className="px-6 py-3 text-center text-xs font-medium text-gray-500 uppercase">
                    Soluzioni
                  </th>
                  <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase">
                    Tempo (s)
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                    Stato
                  </th>
                  <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase">
                    Azioni
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {mockHistory.map((record) => (
                  <tr key={record.id} className="hover:bg-gray-50">
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      {formatDateTime(record.created_at)}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-right font-medium text-gray-900">
                      {formatNumber(record.target_dc, 1)}%
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-right font-medium text-gray-900">
                      {formatNumber(record.target_fp, 0)}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-right text-gray-900">
                      {formatNumber(record.total_kg, 1)} kg
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-center text-gray-900">
                      {record.num_solutions}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-right text-gray-600">
                      {formatNumber(record.computation_time, 1)}s
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <Badge variant={
                        record.status === 'completed' ? 'success' :
                        record.status === 'processing' ? 'info' :
                        record.status === 'failed' ? 'danger' : 'default'
                      }>
                        {record.status}
                      </Badge>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-right text-sm">
                      {record.status === 'completed' && (
                        <Link
                          to={`/results/${record.id}`}
                          className="text-primary-600 hover:text-primary-900 font-medium"
                        >
                          Visualizza
                        </Link>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </Card>

      <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
        <p className="text-sm text-blue-900">
          <strong>Nota:</strong> Questa pagina mostra dati di esempio. L'integrazione completa con il backend
          per la cronologia delle ottimizzazioni sarà implementata nella prossima versione.
        </p>
      </div>
    </div>
  )
}
