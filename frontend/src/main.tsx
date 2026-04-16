import React from 'react'
import ReactDOM from 'react-dom/client'
import { BrowserRouter } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { Toaster } from 'react-hot-toast'
import posthog from 'posthog-js'
import App from './App'
import './index.css'

const isProduction = import.meta.env.PROD === true || import.meta.env.VITE_API_URL?.includes('localhost') === false

// eslint-disable-next-line @typescript-eslint/no-unused-vars
const POSTHOG_DISABLED = true  // Disable for now

if (isProduction && !POSTHOG_DISABLED) {
  posthog.init('phc_AHoXWRrVeZyw3oiik6dKrQ6oYF9xbn4bRpKWBJDZP3cp', {
    api_host: '/ingest',
    person_profiles: 'identified_only',
    capture_pageview: true 
  })
}
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 5 * 60 * 1000,
      retry: 1,
      refetchOnWindowFocus: false,
    },
  },
})

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <App />
        <Toaster
          position="top-right"
          toastOptions={{
            duration: 4000,
            style: {
              background: '#fff',
              color: '#1f2937',
              borderRadius: '12px',
              boxShadow: '0 10px 40px rgba(0,0,0,0.1)',
            },
            success: {
              iconTheme: {
                primary: '#10b981',
                secondary: '#fff',
              },
            },
            error: {
              iconTheme: {
                primary: '#ef4444',
                secondary: '#fff',
              },
            },
          }}
        />
      </BrowserRouter>
    </QueryClientProvider>
  </React.StrictMode>
)
