/**
 * ================================================================================
 * Petar II Petrović-Njegoš
 * "Blago tome ko dovijek živi, imao se rašta i roditi"
 * ================================================================================
 * 
 * AI Learning System
 * QuizResultsPage.tsx
 * Verzija: 1.0.0
 * Autor: Branko Suznjevic
 * Datum: 2026
 * ================================================================================
 */

import { useParams, useLocation, useNavigate } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { quizzesApi } from '@/services/api'
import { AttemptResult, AnswerResult } from '@/types'
import { CheckCircle, XCircle, Trophy, RotateCcw, List, ChevronDown, ChevronUp, Loader2, Star, Zap } from 'lucide-react'
import { useState } from 'react'
import clsx from 'clsx'

export default function QuizResultsPage() {
  const { quizId, attemptId } = useParams<{ quizId: string; attemptId: string }>()
  const location = useLocation()
  const navigate = useNavigate()
  const [expandedQ, setExpandedQ] = useState<string | null>(null)

  // Ako result dolazi state-om (iz play stranice) — koristimo ga direktno
  const resultFromState: AttemptResult | undefined = location.state?.result

  // Fetch specific attempt if attemptId provided, otherwise fetch latest
  const { data: fetchedData, isLoading } = useQuery({
    queryKey: ['attempt-result', quizId, attemptId ?? 'latest'],
    queryFn: () =>
      attemptId
        ? quizzesApi.getAttemptResult(quizId!, attemptId)
        : quizzesApi.getLatestAttemptResult(quizId!),
    enabled: !!quizId && !resultFromState,
  })

  const result: AttemptResult | null = resultFromState ?? (fetchedData as any)?.data ?? null

  if (isLoading) {
    return (
      <div className="flex justify-center items-center py-32">
        <Loader2 className="w-8 h-8 animate-spin text-indigo-400" />
      </div>
    )
  }

  if (!result) {
    return (
      <div className="max-w-2xl mx-auto text-center py-24">
        <Trophy className="w-14 h-14 text-gray-200 mx-auto mb-4" />
        <p className="text-gray-600 font-semibold text-lg mb-2">Nema rezultata</p>
        <p className="text-gray-400 text-sm mb-6">Ovaj kviz još nije igran. Pokreni kviz da bi video rezultate.</p>
        <button
          onClick={() => navigate(`/quizzes/${quizId}/play`)}
          className="btn-primary"
        >
          Pokreni kviz
        </button>
      </div>
    )
  }

  const correct = result.answers.filter((a) => a.is_correct).length
  const total = result.answers.length
  const passed = result.passed

  const scoreColor = passed ? 'text-green-600' : 'text-red-500'
  const scoreBg = passed
    ? 'from-green-50 to-emerald-50 border-green-200'
    : 'from-red-50 to-pink-50 border-red-200'

  return (
    <div className="max-w-2xl mx-auto space-y-5">
      {/* Score card */}
      <div className={clsx('rounded-2xl border p-8 text-center bg-gradient-to-br', scoreBg)}>
        <div className="flex justify-center mb-4">
          {passed
            ? <Trophy className="w-14 h-14 text-yellow-500" />
            : <XCircle className="w-14 h-14 text-red-400" />
          }
        </div>
        <p className="text-lg font-semibold text-gray-700 mb-1">
          {passed ? '🎉 Odlično! Položio si kviz!' : 'Nije uspelo ovog puta. Pokušaj ponovo!'}
        </p>
        <p className={clsx('text-6xl font-extrabold mt-2', scoreColor)}>
          {result.percentage.toFixed(0)}%
        </p>
        <p className="text-gray-500 text-sm mt-2">
          {result.score} / {result.total_points} poena · {correct}/{total} tačnih
        </p>
      </div>

      {/* XP Award */}
      {(result as any).xp_awarded != null && (result as any).xp_awarded > 0 && (
        <div className="rounded-2xl border border-indigo-200 bg-gradient-to-br from-indigo-50 to-violet-50 p-5 text-center">
          <div className="flex items-center justify-center gap-4">
            <div className="flex items-center gap-2">
              <Zap className="w-5 h-5 text-yellow-500" />
              <span className="text-lg font-bold text-indigo-700">
                +{(result as any).xp_awarded} XP
              </span>
            </div>
            {(result as any).leveled_up && (
              <div className="flex items-center gap-2 px-3 py-1 rounded-full bg-gradient-to-r from-indigo-500 to-violet-500 text-white text-sm font-semibold shadow-md">
                <Star className="w-4 h-4" />
                Nivo {(result as any).new_level}
              </div>
            )}
          </div>
          {(result as any).new_badges?.length > 0 && (
            <div className="mt-3 flex flex-wrap justify-center gap-2">
              {(result as any).new_badges.map((badge: any) => (
                <span
                  key={badge.slug}
                  className="inline-flex items-center gap-1 px-3 py-1 rounded-full bg-white border border-amber-200 text-amber-700 text-xs font-semibold shadow-sm"
                >
                  <Trophy className="w-3.5 h-3.5" />
                  {badge.name} {badge.xp_reward > 0 && `+${badge.xp_reward} XP`}
                </span>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Actions */}
      <div className="flex gap-3">
        <button
          onClick={() => navigate(`/quizzes/${quizId}/play`)}
          className="flex-1 flex items-center justify-center gap-2 py-2.5 rounded-xl border border-gray-200 text-sm font-medium text-gray-700 hover:bg-gray-50"
        >
          <RotateCcw className="w-4 h-4" />
          Ponovi kviz
        </button>
        <button
          onClick={() => navigate('/quizzes')}
          className="flex-1 flex items-center justify-center gap-2 py-2.5 rounded-xl text-white text-sm font-semibold"
          style={{ background: 'linear-gradient(135deg, #6366f1, #8b5cf6)' }}
        >
          <List className="w-4 h-4" />
          Svi kvizovi
        </button>
      </div>

      {/* Answers breakdown */}
      <div>
        <h2 className="text-base font-semibold text-gray-800 mb-3">Pregled odgovora</h2>
        <div className="space-y-2">
          {result.answers.map((ans: AnswerResult, idx: number) => (
            <div
              key={ans.question_id}
              className={clsx(
                'rounded-xl border bg-white overflow-hidden',
                ans.is_correct ? 'border-green-200' : 'border-red-200'
              )}
            >
              <button
                className="w-full flex items-center gap-3 px-4 py-3 text-left"
                onClick={() => setExpandedQ(expandedQ === ans.question_id ? null : ans.question_id)}
              >
                {ans.is_correct
                  ? <CheckCircle className="w-5 h-5 text-green-500 flex-shrink-0" />
                  : <XCircle className="w-5 h-5 text-red-400 flex-shrink-0" />
                }
                <span className="flex-1 text-sm font-medium text-gray-800 truncate">
                  Pitanje {idx + 1}
                </span>
                <span className={clsx(
                  'text-xs font-semibold px-2 py-0.5 rounded-full',
                  ans.is_correct ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-600'
                )}>
                  {ans.points_earned} pt
                </span>
                {expandedQ === ans.question_id
                  ? <ChevronUp className="w-4 h-4 text-gray-400" />
                  : <ChevronDown className="w-4 h-4 text-gray-400" />
                }
              </button>

              {expandedQ === ans.question_id && (
                <div className="px-4 pb-4 space-y-2 border-t border-gray-100 pt-3">
                  <div>
                    <p className="text-xs font-medium text-gray-500 mb-0.5">Tvoj odgovor:</p>
                    <p className={clsx(
                      'text-sm font-semibold',
                      ans.is_correct ? 'text-green-700' : 'text-red-600'
                    )}>
                      {ans.user_answer || '(bez odgovora)'}
                    </p>
                  </div>
                  {!ans.is_correct && (
                    <div>
                      <p className="text-xs font-medium text-gray-500 mb-0.5">Tačan odgovor:</p>
                      <p className="text-sm font-semibold text-green-700">{ans.correct_answer}</p>
                    </div>
                  )}
                  {ans.explanation && (
                    <div className="bg-indigo-50 rounded-lg px-3 py-2">
                      <p className="text-xs font-medium text-indigo-700 mb-0.5">Objašnjenje:</p>
                      <p className="text-xs text-indigo-800">{ans.explanation}</p>
                    </div>
                  )}
                </div>
              )}
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}
