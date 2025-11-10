import { useParams, useNavigate } from 'react-router-dom'
import { useOptimization } from '@/hooks/useOptimization'
import Card from '@/components/ui/Card'
import Button from '@/components/ui/Button'
import Badge from '@/components/ui/Badge'
import Spinner from '@/components/ui/Spinner'
import { formatNumber, formatKg, formatCurrency, formatDateTime } from '@/utils/formatters'

export default function Results() {
  const { requestId } = useParams<{ requestId: string }>()
  const navigate = useNavigate()
  const {
    status,
    results,
    isLoadingStatus,
    isLoadingResults,
    downloadExcel,
    isDownloading,
  } = useOptimization(requestId)

  const handleDownload = () => {
    if (requestId) {
      downloadExcel(requestId)
    }
  }

  if (isLoadingStatus || isLoadingResults) {
    return (
      <div className="flex flex-col items-center justify-center py-12">
        <Spinner size="lg" className="mb-4" />
        <p className="text-gray-600">Caricamento risultati...</p>
      </div>
    )
  }

  if (status?.status === 'pending' || status?.status === 'processing') {
    return (
      <div className="flex flex-col items-center justify-center py-12">
        <Spinner size="lg" className="mb-4" />
        <p className="text-lg font-semibold text-gray-900 mb-2">Ottimizzazione in corso...</p>
        <p className="text-gray-600">Attendere il completamento</p>
      </div>
    )
  }

  if (status?.status === 'failed') {
    return (
      <Card>
        <div className="text-center py-12">
          <div className="text-red-500 mb-4">
            <svg className="w-16 h-16 mx-auto" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </div>
          <p className="text-lg font-semibold text-gray-900 mb-2">Ottimizzazione fallita</p>
          <p className="text-gray-600 mb-6">{status.error_message}</p>
          <Button onClick={() => navigate('/optimize')}>Riprova</Button>
        </div>
      </Card>
    )
  }

  if (!results || results.solutions.length === 0) {
    return (
      <Card>
        <div className="text-center py-12">
          <p className="text-lg font-semibold text-gray-900 mb-2">Nessuna soluzione trovata</p>
          <p className="text-gray-600 mb-6">Prova a modificare i parametri di ottimizzazione</p>
          <Button onClick={() => navigate('/optimize')}>Crea Nuova Ottimizzazione</Button>
        </div>
      </Card>
    )
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Risultati Ottimizzazione</h1>
          <p className="text-gray-600 mt-1">
            {results.solutions.length} soluzione/i trovate - {formatDateTime(results.generated_at)}
          </p>
        </div>
        <div className="flex space-x-3">
          <Button
            variant="secondary"
            onClick={() => navigate('/optimize')}
          >
            Nuova Ottimizzazione
          </Button>
          <Button
            variant="primary"
            onClick={handleDownload}
            isLoading={isDownloading}
          >
            Download Excel
          </Button>
        </div>
      </div>

      {/* Requirements Summary */}
      <Card title="Parametri Richiesti">
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div>
            <div className="text-sm text-gray-600">DC Target</div>
            <div className="text-lg font-semibold text-gray-900">{formatNumber(results.requirements.target_dc, 1)}%</div>
          </div>
          <div>
            <div className="text-sm text-gray-600">FP Target</div>
            <div className="text-lg font-semibold text-gray-900">{results.requirements.target_fp ? formatNumber(results.requirements.target_fp, 0) : '-'}</div>
          </div>
          {results.requirements.max_oe && (
            <div>
              <div className="text-sm text-gray-600">Max Other Elements</div>
              <div className="text-lg font-semibold text-gray-900">≤ {formatNumber(results.requirements.max_oe, 1)}%</div>
            </div>
          )}
          <div>
            <div className="text-sm text-gray-600">Quantità Totale</div>
            <div className="text-lg font-semibold text-gray-900">{formatKg(results.requirements.total_kg)}</div>
          </div>
          <div>
            <div className="text-sm text-gray-600">Tempo Calcolo</div>
            <div className="text-lg font-semibold text-gray-900">{formatNumber(results.computation_time_seconds, 1)}s</div>
          </div>
        </div>
      </Card>

      {/* Solutions */}
      {results.solutions.map((solution) => (
        <Card key={solution.solution_number} title={`Soluzione #${solution.solution_number}`}>
          {/* Solution Summary */}
          <div className="grid grid-cols-2 md:grid-cols-7 gap-4 mb-6 p-4 bg-gray-50 rounded-lg">
            <div>
              <div className="text-sm text-gray-600">DC Ottenuto</div>
              <div className="text-lg font-semibold flex items-center space-x-2">
                <span>{formatNumber(solution.aggregated_dc, 1)}%</span>
                {solution.compliance_dc ? (
                  <Badge variant="success">✓</Badge>
                ) : (
                  <Badge variant="danger">✗</Badge>
                )}
              </div>
              <div className="text-xs text-gray-500">Δ {formatNumber(solution.dc_delta, 1)}%</div>
            </div>

            <div>
              <div className="text-sm text-gray-600">Duck Ottenuto</div>
              <div className="text-lg font-semibold flex items-center space-x-2">
                <span>{solution.aggregated_duck ? formatNumber(solution.aggregated_duck, 1) : '-'}%</span>
                {solution.compliance_duck ? (
                  <Badge variant="success">✓</Badge>
                ) : (
                  <Badge variant="danger">✗</Badge>
                )}
              </div>
              <div className="text-xs text-gray-500">Δ {solution.duck_delta ? formatNumber(solution.duck_delta, 1) : '-'}%</div>
            </div>

            <div>
              <div className="text-sm text-gray-600">FP Ottenuto</div>
              <div className="text-lg font-semibold flex items-center space-x-2">
                <span>{formatNumber(solution.aggregated_fp, 0)}</span>
                {solution.compliance_fp ? (
                  <Badge variant="success">✓</Badge>
                ) : (
                  <Badge variant="danger">✗</Badge>
                )}
              </div>
              <div className="text-xs text-gray-500">Δ {formatNumber(solution.fp_delta, 0)}</div>
            </div>

            <div>
              <div className="text-sm text-gray-600">Other Elements</div>
              <div className="text-lg font-semibold flex items-center space-x-2">
                <span>{solution.aggregated_oe ? formatNumber(solution.aggregated_oe, 1) : '-'}%</span>
                {results.requirements.max_oe && solution.aggregated_oe && (
                  solution.compliance_oe ? (
                    <Badge variant="success">✓</Badge>
                  ) : (
                    <Badge variant="danger">✗</Badge>
                  )
                )}
              </div>
              {solution.oe_delta && (
                <div className="text-xs text-gray-500">{formatNumber(solution.oe_delta, 1)}%</div>
              )}
            </div>

            <div>
              <div className="text-sm text-gray-600">Numero Lotti</div>
              <div className="text-lg font-semibold">{solution.num_lots}</div>
            </div>

            <div>
              <div className="text-sm text-gray-600">Costo Totale</div>
              <div className="text-lg font-semibold">{formatCurrency(solution.total_cost)}</div>
              <div className="text-xs text-gray-500">{formatCurrency(solution.avg_cost_per_kg)}/kg</div>
            </div>

            <div>
              <div className="text-sm text-gray-600">Score</div>
              <div className="text-lg font-semibold text-primary-600">{formatNumber(solution.score, 2)}</div>
            </div>
          </div>

          {/* Lots Table */}
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-3 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                    Codice
                  </th>
                  <th className="px-3 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                    Codice Lotto
                  </th>
                  <th className="px-3 py-3 text-right text-xs font-medium text-gray-500 uppercase">
                    DC Nom
                  </th>
                  <th className="px-3 py-3 text-center text-xs font-medium text-gray-500 uppercase">
                    Standard
                  </th>
                  <th className="px-3 py-3 text-right text-xs font-medium text-gray-500 uppercase">
                    FP Nom
                  </th>
                  <th className="px-3 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                    Quality
                  </th>
                  <th className="px-3 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                    LOT_DESC
                  </th>
                  <th className="px-3 py-3 text-right text-xs font-medium text-gray-500 uppercase">
                    DC %
                  </th>
                  <th className="px-3 py-3 text-right text-xs font-medium text-gray-500 uppercase">
                    FP
                  </th>
                  <th className="px-3 py-3 text-right text-xs font-medium text-gray-500 uppercase">
                    Duck %
                  </th>
                  <th className="px-3 py-3 text-right text-xs font-medium text-gray-500 uppercase">
                    Kg Usati
                  </th>
                  <th className="px-3 py-3 text-right text-xs font-medium text-gray-500 uppercase">
                    % Miscela
                  </th>
                  <th className="px-3 py-3 text-right text-xs font-medium text-gray-500 uppercase">
                    €/kg
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {solution.lots.map((lot, idx) => (
                  <tr key={idx} className="hover:bg-gray-50">
                    <td className="px-3 py-3 text-sm font-medium text-gray-900">
                      {lot.article_code}
                    </td>
                    <td className="px-3 py-3 text-sm text-gray-600">
                      {lot.lot_code}
                    </td>
                    <td className="px-3 py-3 text-sm text-right text-gray-500">
                      {lot.dc_nominal ? formatNumber(lot.dc_nominal, 1) : '-'}
                    </td>
                    <td className="px-3 py-3 text-sm text-center text-gray-500">
                      {lot.standard_nominal || '-'}
                    </td>
                    <td className="px-3 py-3 text-sm text-right text-gray-500">
                      {lot.fp_nominal ? formatNumber(lot.fp_nominal, 0) : '-'}
                    </td>
                    <td className="px-3 py-3 text-sm text-gray-500 truncate max-w-xs">
                      {lot.quality_nominal || '-'}
                    </td>
                    <td className="px-3 py-3 text-sm text-gray-900">
                      {lot.description || '-'}
                    </td>
                    <td className="px-3 py-3 text-sm text-right font-medium text-gray-900">
                      {formatNumber(lot.dc_real, 1)}%
                    </td>
                    <td className="px-3 py-3 text-sm text-right font-medium text-gray-900">
                      {formatNumber(lot.fp_real, 0)}
                    </td>
                    <td className="px-3 py-3 text-sm text-right text-gray-900">
                      {lot.duck_real ? `${formatNumber(lot.duck_real, 1)}%` : '-'}
                    </td>
                    <td className="px-3 py-3 text-sm text-right text-gray-900">
                      {formatKg(lot.kg_used)}
                    </td>
                    <td className="px-3 py-3 text-sm text-right text-gray-600">
                      {formatNumber(lot.percentage, 1)}%
                    </td>
                    <td className="px-3 py-3 text-sm text-right text-gray-900">
                      {formatCurrency(lot.cost_per_kg)}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </Card>
      ))}
    </div>
  )
}
