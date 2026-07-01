import { Routes, Route, Navigate } from 'react-router-dom'
import { useAuthStore } from '@/stores/authStore'
import { useEffect } from 'react'

import Layout from '@/components/Layout'
import ProtectedRoute from '@/components/ProtectedRoute'

import LoginPage from '@/pages/LoginPage'
import RegisterPage from '@/pages/RegisterPage'
import ForgotPasswordPage from '@/pages/ForgotPasswordPage'
import ResetPasswordPage from '@/pages/ResetPasswordPage'
import DashboardPage from '@/pages/DashboardPage'
import DocumentsPage from '@/pages/DocumentsPage'
import DocumentDetailPage from '@/pages/DocumentDetailPage'
import ReviewPage from '@/pages/ReviewPage'
import SettingsPage from '@/pages/SettingsPage'
import QuizzesPage from '@/pages/QuizzesPage'
import QuizPlayPage from '@/pages/QuizPlayPage'
import QuizResultsPage from '@/pages/QuizResultsPage'
import AnalyticsPage from '@/pages/AnalyticsPage'
import KnowledgeBasePage from '@/pages/KnowledgeBasePage'
import TranslationsPage from '@/pages/TranslationsPage'
import IntelligenceTestPage from '@/pages/IntelligenceTestPage'
import ProviderHealthPage from '@/pages/ProviderHealthPage'
import AchievementsPage from '@/pages/AchievementsPage'
import NotFoundPage from '@/pages/NotFoundPage'

function App() {
  const { isAuthenticated, isLoading, fetchUser, token } = useAuthStore()

  useEffect(() => {
    if (token && !isAuthenticated) {
      fetchUser()
    } else {
      useAuthStore.getState().setLoading(false)
    }
  }, [token, isAuthenticated, fetchUser])

  if (isLoading) {
    return (
      <div className="min-h-screen gradient-bg flex items-center justify-center">
        <div className="flex flex-col items-center gap-4">
          <div className="w-16 h-16 border-4 border-primary-500 border-t-transparent rounded-full animate-spin" />
          <p className="text-gray-600 font-medium">Učitavanje...</p>
        </div>
      </div>
    )
  }

  return (
    <Routes>
      <Route path="/login" element={
        isAuthenticated ? <Navigate to="/" replace /> : <LoginPage />
      } />
      <Route path="/register" element={
        isAuthenticated ? <Navigate to="/" replace /> : <RegisterPage />
      } />
      <Route path="/forgot-password" element={
        isAuthenticated ? <Navigate to="/" replace /> : <ForgotPasswordPage />
      } />
      <Route path="/reset-password" element={
        isAuthenticated ? <Navigate to="/" replace /> : <ResetPasswordPage />
      } />
      
      <Route path="/" element={
        <ProtectedRoute>
          <Layout />
        </ProtectedRoute>
      }>
        <Route index element={<DashboardPage />} />
        <Route path="documents" element={<DocumentsPage />} />
        <Route path="documents/:id" element={<DocumentDetailPage />} />
        <Route path="review/:id" element={<ReviewPage />} />
        <Route path="settings" element={<SettingsPage />} />
        <Route path="quizzes" element={<QuizzesPage />} />
        <Route path="quizzes/:quizId/play" element={<QuizPlayPage />} />
        <Route path="quizzes/:quizId/results" element={<QuizResultsPage />} />
        <Route path="quizzes/:quizId/results/:attemptId" element={<QuizResultsPage />} />
        <Route path="analytics" element={<AnalyticsPage />} />
        <Route path="knowledge" element={<KnowledgeBasePage />} />
        <Route path="review" element={<TranslationsPage />} />
        <Route path="intelligence-test" element={<IntelligenceTestPage />} />
        <Route path="providers" element={<ProviderHealthPage />} />
        <Route path="achievements" element={<AchievementsPage />} />
      </Route>
      
      <Route path="*" element={<NotFoundPage />} />
    </Routes>
  )
}

export default App
