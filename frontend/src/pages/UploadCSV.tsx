import { useState } from 'react'
import { useInventory } from '@/hooks/useInventory'
import Card from '@/components/ui/Card'
import Button from '@/components/ui/Button'
import Badge from '@/components/ui/Badge'
import { formatDateTime } from '@/utils/formatters'

export default function UploadCSV() {
  const { uploadCSV, isUploading, uploadHistory, isLoadingHistory } = useInventory()
  const [selectedFile, setSelectedFile] = useState<File | null>(null)
  const [notes, setNotes] = useState('')

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      setSelectedFile(e.target.files[0])
    }
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!selectedFile) return

    uploadCSV(
      { file: selectedFile, notes },
      {
        onSuccess: () => {
          setSelectedFile(null)
          setNotes('')
          // Reset file input
          const fileInput = document.getElementById('csv-file') as HTMLInputElement
          if (fileInput) fileInput.value = ''
        },
      }
    )
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-gray-900">Carica Inventario CSV</h1>
        <p className="text-gray-600 mt-1">
          Carica un file CSV con i dati dell'inventario lotti
        </p>
      </div>

      {/* Upload Form */}
      <Card title="Carica Nuovo File">
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              File CSV <span className="text-red-500">*</span>
            </label>
            <input
              id="csv-file"
              type="file"
              accept=".csv"
              onChange={handleFileChange}
              className="block w-full text-sm text-gray-900 border border-gray-300 rounded-lg cursor-pointer bg-gray-50 focus:outline-none focus:border-primary-500"
              required
            />
            <p className="mt-1 text-sm text-gray-500">
              Formato CSV con colonne: article_code, description, species, dc_real, fp_real, available_kg, cost_per_kg, ecc.
            </p>
          </div>

          {selectedFile && (
            <div className="p-3 bg-blue-50 border border-blue-200 rounded-lg">
              <p className="text-sm text-blue-900">
                File selezionato: <strong>{selectedFile.name}</strong> ({(selectedFile.size / 1024).toFixed(2)} KB)
              </p>
            </div>
          )}

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Note (opzionale)
            </label>
            <textarea
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
              rows={3}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent"
              placeholder="Aggiungi note sull'upload..."
            />
          </div>

          <div className="flex justify-end">
            <Button
              type="submit"
              variant="primary"
              isLoading={isUploading}
              disabled={isUploading || !selectedFile}
            >
              {isUploading ? 'Upload in corso...' : 'Carica CSV'}
            </Button>
          </div>
        </form>
      </Card>

      {/* Upload History */}
      <Card title="Cronologia Upload">
        {isLoadingHistory ? (
          <div className="text-center py-8">
            <p className="text-gray-600">Caricamento...</p>
          </div>
        ) : uploadHistory && uploadHistory.length > 0 ? (
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                    Data
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                    Filename
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                    Utente
                  </th>
                  <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase">
                    Lotti
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                    Stato
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                    Note
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {uploadHistory.map((upload) => (
                  <tr key={upload.id} className="hover:bg-gray-50">
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      {formatDateTime(upload.upload_timestamp)}
                    </td>
                    <td className="px-6 py-4 text-sm font-medium text-gray-900">
                      {upload.filename}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-600">
                      {upload.uploaded_by_username}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-right text-gray-900">
                      {upload.total_lots}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <Badge variant={
                        upload.status === 'success' ? 'success' :
                        upload.status === 'partial' ? 'warning' : 'danger'
                      }>
                        {upload.status}
                      </Badge>
                    </td>
                    <td className="px-6 py-4 text-sm text-gray-600">
                      {upload.notes || '-'}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <div className="text-center py-8">
            <p className="text-gray-600">Nessun upload effettuato</p>
          </div>
        )}
      </Card>
    </div>
  )
}
