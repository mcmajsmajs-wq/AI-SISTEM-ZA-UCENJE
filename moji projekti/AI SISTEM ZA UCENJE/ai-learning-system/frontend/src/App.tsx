import { Routes, Route, Navigate } from 'react-router-dom'
import { useAuthStore } from '@/stores/authStore'
import { useEffect } from 'react'

import Layout from '@/components/Layout'
import ProtectedRoute from '@/components/ProtectedRoute'

import LoginPage from '@/pages/LoginPage'
import RegisterPage from '@/pages/RegisterPage'
import DashboardPage from '@/pages/DashboardPage'
import DocumentsPage from '@/pages/DocumentsPage'
import DocumentDetailPage from '@/pages/DocumentDetailPage'
import ReviewPage from '@/pages/ReviewPage'
import SettingsPage from '@/pages/SettingsPage'
import NotFoundPage from '@/pages/NotFoundPage'
import QuizzesPage from '@/pages/QuizzesPage'
import QuizDetailPage from '@/pages/QuizDetailPage'
import QuizPlayPage from '@/pages/QuizPlayPage'
import QuizGeneratePage from '@/pages/QuizGeneratePage'
import QuizResultsPage from '@/pages/QuizResultsPage'

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
      
      <Route path="/" element={
        <ProtectedRoute>
          <Layout />
        </ProtectedRoute>
      }>
        <Route index element={<DashboardPage />} />
        <Route path="documents" element={<DocumentsPage />} />
        <Route path="documents/:id" element={<DocumentDetailPage />} />
        <Route path="review/:id" element={<ReviewPage />} />
        <Route path="quizzes" element={<QuizzesPage />} />
        <Route path="quizzes/generate" element={<QuizGeneratePage />} />
        <Route path="quizzes/:id" element={<QuizDetailPage />} />
        <Route path="quizzes/:id/play" element={<QuizPlayPage />} />
        <Route path="quizzes/:id/results/:attemptId" element={<QuizResultsPage />} />
        <Route path="settings" element={<SettingsPage />} />
      </Route>
      
      <Route path="*" element={<NotFoundPage />} />
    </Routes>
  )
}

export default App
