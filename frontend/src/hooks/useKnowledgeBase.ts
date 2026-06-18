import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { knowledgeApi } from '@/services/api'

export const kbKeys = {
  stats: ['knowledge-stats'] as const,
  sources: ['knowledge-sources'] as const,
}

export interface KBSource {
  id: string
  source_type: string
  name: string
  url?: string
  total_chunks: number
  status: string
  last_indexed?: string
  created_at: string
}

export interface KBStats {
  total_sources: number
  indexed_sources: number
  total_chunks: number
  error_sources: number
}

export interface KBQueryResult {
  answer: string
  sources?: { name: string; type: string; url?: string }[]
  provider?: string
}

export function useKBStats() {
  return useQuery({
    queryKey: kbKeys.stats,
    queryFn: async () => {
      const res = await knowledgeApi.stats()
      return res.data as KBStats
    },
    refetchInterval: 30000,
  })
}

export function useKBSources() {
  return useQuery({
    queryKey: kbKeys.sources,
    queryFn: async () => {
      const res = await knowledgeApi.sources()
      return res.data as KBSource[]
    },
  })
}

export function useKBQuery() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: async ({ query, provider }: { query: string; provider?: string }) => {
      const res = await knowledgeApi.query(query, 5, provider)
      return res.data as KBQueryResult
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: kbKeys.stats })
    },
  })
}

export function useKBIngestUrl() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: async ({ url, options }: { url: string; options?: { recursive?: boolean; max_depth?: number; max_pages?: number } }) => {
      const res = await knowledgeApi.ingestUrl(url, options)
      return res.data
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: kbKeys.sources })
      queryClient.invalidateQueries({ queryKey: kbKeys.stats })
    },
  })
}

export function useKBDeleteSource() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (id: string) => knowledgeApi.deleteSource(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: kbKeys.sources })
      queryClient.invalidateQueries({ queryKey: kbKeys.stats })
    },
  })
}

export function useKBReindex() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: () => knowledgeApi.reindex(),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: kbKeys.sources })
      queryClient.invalidateQueries({ queryKey: kbKeys.stats })
    },
  })
}
