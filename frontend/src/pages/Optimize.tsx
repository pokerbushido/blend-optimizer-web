import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useOptimization } from '@/hooks/useOptimization'
import Card from '@/components/ui/Card'
import Input from '@/components/ui/Input'
import Button from '@/components/ui/Button'
import { DEFAULT_OPTIMIZATION } from '@/utils/constants'
import type { BlendRequirements } from '@/types/api'

export default function Optimize() {
  const navigate = useNavigate()
  const { createOptimization, isCreating } = useOptimization()

  const [requirements, setRequirements] = useState<BlendRequirements>({
    product_code: '',
    target_dc: 90,
    target_fp: undefined,
    target_duck: undefined,
    max_oe: undefined,
    species: [],
    color: [],
    water_repellent: false,
    total_kg: 100,
    num_solutions: DEFAULT_OPTIMIZATION.NUM_SOLUTIONS,
    max_lots: DEFAULT_OPTIMIZATION.MAX_LOTS,
  })

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()

    createOptimization(requirements, {
      onSuccess: (data) => {
        console.log('✅ Optimization successful, request_id:', data.request_id)
        console.log('Solutions found:', data.solutions?.length)
        navigate(`/results/${data.request_id}`)
      },
    })
  }


  return (
    <div className="max-w-4xl mx-auto space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-gray-900">Crea Ottimizzazione Blend</h1>
        <p className="text-gray-600 mt-1">
          Definisci i parametri target e i vincoli per l'ottimizzazione
        </p>
      </div>

      <form onSubmit={handleSubmit} className="space-y-6">
        {/* Target Parameters */}
        <Card title="Parametri Target">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <Input
              label="Down Cluster Target (%)"
              type="number"
              step="0.1"
              min="0"
              max="100"
              value={requirements.target_dc}
              onChange={(e) => setRequirements(prev => ({ ...prev, target_dc: parseFloat(e.target.value) }))}
              required
              helperText={`Tolleranza: ±${DEFAULT_OPTIMIZATION.DC_TOLERANCE}%`}
            />

            <Input
              label="Fill Power Target - Opzionale"
              type="number"
              step="1"
              min="0"
              value={requirements.target_fp || ''}
              onChange={(e) => setRequirements(prev => ({ ...prev, target_fp: e.target.value ? parseFloat(e.target.value) : undefined }))}
              helperText="Lascia vuoto se non richiesto"
            />

            <Input
              label="Duck Content Target (%) - Opzionale"
              type="number"
              step="0.1"
              min="0"
              max="100"
              value={requirements.target_duck || ''}
              onChange={(e) => setRequirements(prev => ({ ...prev, target_duck: e.target.value ? parseFloat(e.target.value) : undefined }))}
              helperText="Lascia vuoto se non richiesto"
            />

            <Input
              label="Max Other Elements (%) - Opzionale"
              type="number"
              step="0.1"
              min="0"
              max="100"
              value={requirements.max_oe || ''}
              onChange={(e) => setRequirements(prev => ({ ...prev, max_oe: e.target.value ? parseFloat(e.target.value) : undefined }))}
              helperText="Valore massimo accettabile"
            />
          </div>
        </Card>

        {/* Constraints */}
        <Card title="Specifiche Prodotto">
          <div className="space-y-6">
            {/* Product Code */}
            <div>
              <Input
                label="Codice Articolo"
                type="text"
                value={requirements.product_code}
                onChange={(e) => setRequirements(prev => ({ ...prev, product_code: e.target.value.toUpperCase() }))}
                placeholder="Es: PAB, POB, POAG"
                required
              />
              <div className="mt-2 p-3 bg-blue-50 border border-blue-200 rounded-lg">
                <p className="text-sm font-medium text-blue-900 mb-1">Esempi di codici articolo:</p>
                <ul className="text-xs text-blue-700 space-y-1">
                  <li><strong>PAB</strong> = Piumino Anatra Bianco</li>
                  <li><strong>POB</strong> = Piumino Oca Bianco</li>
                  <li><strong>POAG</strong> = Piumino Oca/Anatra Grigio</li>
                  <li><strong>LAB</strong> = Lavato Anatra Bianco</li>
                  <li><strong>WAB</strong> = Washed Anatra Bianco</li>
                </ul>
                <p className="text-xs text-blue-600 mt-2">
                  <strong>Formato:</strong> [Stato][Specie][Colore] dove Stato = P/L/W, Specie = O/A/OA/C, Colore = B/G/PW/NPW
                </p>
              </div>
            </div>

            {/* Water Repellent */}
            <div className="flex items-center">
              <input
                type="checkbox"
                id="water_repellent"
                checked={requirements.water_repellent}
                onChange={(e) => setRequirements(prev => ({ ...prev, water_repellent: e.target.checked }))}
                className="h-4 w-4 text-primary-600 focus:ring-primary-500 border-gray-300 rounded"
              />
              <label htmlFor="water_repellent" className="ml-2 block text-sm text-gray-900">
                Richiedi Water Repellent
              </label>
            </div>
          </div>
        </Card>

        {/* Quantity and Options */}
        <Card title="Quantità e Opzioni">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <Input
              label="Quantità Totale (kg)"
              type="number"
              step="0.1"
              min="1"
              value={requirements.total_kg}
              onChange={(e) => setRequirements(prev => ({ ...prev, total_kg: parseFloat(e.target.value) }))}
              required
            />

            <Input
              label="Numero Soluzioni"
              type="number"
              min="1"
              max="10"
              value={requirements.num_solutions}
              onChange={(e) => setRequirements(prev => ({ ...prev, num_solutions: parseInt(e.target.value) }))}
              helperText="1-10 soluzioni"
            />

            <Input
              label="Max Lotti per Soluzione"
              type="number"
              min="2"
              max="15"
              value={requirements.max_lots}
              onChange={(e) => setRequirements(prev => ({ ...prev, max_lots: parseInt(e.target.value) }))}
              helperText="2-15 lotti"
            />
          </div>
        </Card>

        {/* Actions */}
        <div className="flex justify-end space-x-4">
          <Button
            type="button"
            variant="secondary"
            onClick={() => navigate('/dashboard')}
          >
            Annulla
          </Button>
          <Button
            type="submit"
            variant="primary"
            isLoading={isCreating}
            disabled={isCreating || !requirements.product_code || requirements.product_code.trim() === ''}
          >
            {isCreating ? 'Ottimizzazione in corso...' : 'Avvia Ottimizzazione'}
          </Button>
        </div>
      </form>
    </div>
  )
}
