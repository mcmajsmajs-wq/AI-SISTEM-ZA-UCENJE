import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { documentsApi, filesApi } from '@/services/api'
import type { Document, Chunk, CostEstimate, TranslationProgress } from '@/types'

export const documentKeys = {
  all: ['documents'] as const,
  list: (page: number, status?: string) => ['documents', page, status] as const,
  detail: (id: string) => ['document', id] as const,
  chunks: (id: string) => ['document-chunks', id] as const,
  progress: (id: string) => ['document-progress', id] as const,
}

export function useDocumentsList(page = 1, statusFilter = '') {
  return useQuery({
    queryKey: documentKeys.list(page, statusFilter),
    queryFn: async () => {
      const res = await documentsApi.list((page - 1) * 10, 10, statusFilter || undefined)
      return res.data as { items: Document[]; total: number; skip: number; limit: number }
    },
    refetchInterval: (query) => {
      const docs: Document[] = query.state.data?.items ?? []
      const hasActive = docs.some(d => ['pending', 'processing', 'translating'].includes(d.status))
      return hasActive ? 10000 : false
    },
  })
}

export function useDocumentDetail(id: string) {
  const activeStatuses = ['pending', 'processing', 'translating', 'partial']
  return useQuery({
    queryKey: documentKeys.detail(id),
    queryFn: async () => {
      const res = await documentsApi.get(id)
      return res.data as Document
    },
    enabled: !!id,
    refetchInterval: (query) => {
      const status = (query.state.data as any)?.status
      return activeStatuses.includes(status) ? 5000 : false
    },
  })
}

export function useDocumentChunks(documentId: string, skip = 0, limit = 50) {
  return useQuery({
    queryKey: [...documentKeys.chunks(documentId), skip, limit],
    queryFn: async () => {
      const res = await documentsApi.getChunks(documentId, skip, limit)
      return res.data as { items: Chunk[]; total: number }
    },
    enabled: !!documentId,
  })
}

export function useDocumentProgress(id: string) {
  return useQuery({
    queryKey: documentKeys.progress(id),
    queryFn: async () => {
      const res = await documentsApi.getProgress(id)
      return res.data as TranslationProgress
    },
    enabled: !!id,
    refetchInterval: (query) => {
      const data = query.state.data
      return data && data.status === 'translating' ? 3000 : false
    },
  })
}

export function useUploadDocument() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: async ({ file, title, onProgress }: { file: File; title?: string; onProgress?: (pct: number) => void }) => {
      const uploadRes = await filesApi.upload(file, onProgress)
      const fileId: string = uploadRes.data.id
      const docRes = await documentsApi.create(fileId, title)
      return docRes.data as Document
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: documentKeys.all })
    },
  })
}

export function useProcessDocument() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (id: string) => documentsApi.process(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: documentKeys.all })
    },
  })
}

export function useTranslateDocument() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: async (id: string) => {
      await documentsApi.validateTranslationProvider()
      return documentsApi.translate(id, undefined)
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: documentKeys.all })
    },
  })
}

export function useDeleteDocument() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (id: string) => documentsApi.delete(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: documentKeys.all })
    },
  })
}

export function useDocumentCostEstimate(id: string, provider: string) {
  return useQuery({
    queryKey: ['document-cost', id, provider],
    queryFn: async () => {
      const res = await documentsApi.estimateCost(id, provider)
      return res.data as CostEstimate
    },
    enabled: !!id && !!provider,
  })
}

export function useStopTranslation() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (id: string) => documentsApi.stopTranslation(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: documentKeys.all })
    },
  })
}

export function useDocumentQuizAvailability(id: string) {
  return useQuery({
    queryKey: ['document-quiz-availability', id],
    queryFn: async () => {
      const res = await documentsApi.getQuizAvailability(id)
      return res.data as { total: number; available: number; used: number }
    },
    enabled: !!id,
    refetchInterval: 30000,
  })
}
