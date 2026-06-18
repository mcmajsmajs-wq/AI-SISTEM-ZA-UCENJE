import { create } from 'zustand'

export interface ExportProgress {
  documentId: string
  format: string
  status: string
  current: number
  total: number
  message: string | null
}

interface ExportProgressState {
  exports: Record<string, ExportProgress>
}

export const useExportProgressStore = create<ExportProgressState>(() => ({
  exports: {},
}))
