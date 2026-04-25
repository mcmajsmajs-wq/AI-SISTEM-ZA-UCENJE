import { useState } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import { useQuery, useMutation } from '@tanstack/react-query'
import toast from 'react-hot-toast'
import { documentsApi, quizApi } from '@/services/api'
import {
  Sparkles,
  FileText,
  Loader2,
  ChevronLeft,
  AlertCircle,
  CheckCircle,
  Target,
  Clock,
  Award
} from 'lucide-react'
import clsx from 'clsx'

export default function QuizGeneratePage() {
  const navigate = useNavigate()
  const [step, setStep] = useState(1)
  const [formData, setFormData] = useState({
    document_id: '',
    title: '',
    num_questions: 10,
    question_types: ['multiple_choice'],
    difficulty: 'medium' as 'easy' | 'medium' | 'hard' | 'mixed',
    time_limit: 15,
    passing_score: 60,
  })

  const { data: documents, isLoading: documentsLoading } = useQuery({
    queryKey: ['documents'],
    queryFn: () => documentsApi.list(1, 100, 'completed'),
  })

  const generateMutation = useMutation({
    mutationFn: () => quizApi.generate({
      document_id: formData.document_id,
      title: formData.title || undefined,
      num_questions: formData.num_questions,
      question_types: formData.question_types.length > 0 ? formData.question_types : undefined,
      difficulty: formData.difficulty,
      time_limit: formData.time_limit,
      passing_score: formData.passing_score,
    }),
    onSuccess: (data) => {
      toast.success('Kviz se generiše...')
      navigate('/quizzes')
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.detail || 'Greška pri generisanju kviza')
    },
  })

  const handleQuestionTypeToggle = (type: string) => {
    setFormData(prev => ({
      ...prev,
      question_types: prev.question_types.includes(type)
        ? prev.question_types.filter(t => t !== type)
        : [...prev.question_types, type],
    }))
  }

  const handleSubmit = () => {
    if (!formData.document_id) {
      toast.error('Molimo vas da izaberete dokument')
      return
    }
    generateMutation.mutate()
  }

  const documentsList = documents?.data?.documents || []
  const selectedDocument = documentsList.find((d: any) => d.id === formData.document_id)

  return (
    <div className="max-w-3xl mx-auto space-y-6 animate-fade-in">
      <div className="flex items-center gap-4">
        <Link to="/quizzes" className="text-gray-500 hover:text-gray-700">
          <ChevronLeft className="w-5 h-5" />
        </Link>
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Generiši kviz</h1>
          <p className="text-gray-500 mt-1">Kreirajte kviz na osnovu prevedenog dokumenta</p>
        </div>
      </div>

      <div className="flex items-center gap-4 mb-6">
        {[1, 2, 3].map((s) => (
          <div key={s} className="flex items-center">
            <div className={clsx(
              "w-10 h-10 rounded-full flex items-center justify-center font-medium",
              s < step ? "bg-green-500 text-white" :
              s === step ? "bg-primary-500 text-white" :
              "bg-gray-100 text-gray-400"
            )}>
              {s < step ? <CheckCircle className="w-5 h-5" /> : s}
            </div>
            {s < 3 && (
              <div className={clsx(
                "w-16 h-1 mx-2",
                s < step ? "bg-green-500" : "bg-gray-100"
              )} />
            )}
          </div>
        ))}
      </div>

      {step === 1 && (
        <div className="card p-6">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">Izaberite dokument</h2>
          
          {documentsLoading ? (
            <div className="flex justify-center py-8">
              <Loader2 className="w-8 h-8 text-primary-500 animate-spin" />
            </div>
          ) : documentsList.length === 0 ? (
            <div className="text-center py-8">
              <FileText className="w-12 h-12 text-gray-400 mx-auto mb-3" />
              <p className="text-gray-500 mb-4">Nema dostupnih dokumenata</p>
              <Link to="/documents" className="btn-primary">
                Dodaj dokument
              </Link>
            </div>
          ) : (
            <div className="space-y-3 max-h-[400px] overflow-y-auto">
              {documentsList.map((doc: any) => (
                <button
                  key={doc.id}
                  onClick={() => setFormData(prev => ({ ...prev, document_id: doc.id }))}
                  className={clsx(
                    "w-full text-left p-4 rounded-xl border-2 transition-all",
                    formData.document_id === doc.id
                      ? "border-primary-500 bg-primary-50"
                      : "border-gray-200 hover:border-gray-300"
                  )}
                >
                  <div className="flex items-start gap-3">
                    <div className="w-10 h-10 rounded-lg bg-gray-100 flex items-center justify-center flex-shrink-0">
                      <FileText className="w-5 h-5 text-gray-600" />
                    </div>
                    <div className="flex-1 min-w-0">
                      <p className="font-medium text-gray-900 truncate">{doc.title}</p>
                      <p className="text-sm text-gray-500">
                        {doc.chunks_count || 0} segmenata • {doc.total_pages || 0} stranica
                      </p>
                    </div>
                    {formData.document_id === doc.id && (
                      <CheckCircle className="w-5 h-5 text-primary-500" />
                    )}
                  </div>
                </button>
              ))}
            </div>
          )}

          <div className="flex justify-end mt-6">
            <button
              onClick={() => setStep(2)}
              disabled={!formData.document_id}
              className="btn-primary"
            >
              Sledeće
            </button>
          </div>
        </div>
      )}

      {step === 2 && (
        <div className="card p-6">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">Podesite opcije</h2>
          
          <div className="space-y-6">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Naslov kviza (opciono)
              </label>
              <input
                type="text"
                value={formData.title}
                onChange={(e) => setFormData(prev => ({ ...prev, title: e.target.value }))}
                placeholder={selectedDocument ? `Kviz: ${selectedDocument.title}` : 'Unesite naslov'}
                className="input"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Broj pitanja: {formData.num_questions}
              </label>
              <input
                type="range"
                min="5"
                max="30"
                value={formData.num_questions}
                onChange={(e) => setFormData(prev => ({ ...prev, num_questions: parseInt(e.target.value) }))}
                className="w-full"
              />
              <div className="flex justify-between text-xs text-gray-500 mt-1">
                <span>5</span>
                <span>30</span>
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Tipovi pitanja
              </label>
              <div className="flex flex-wrap gap-2">
                {[
                  { value: 'multiple_choice', label: 'Višestruki izbor' },
                  { value: 'checkbox', label: 'Više tačnih' },
                  { value: 'true_false', label: 'Tačno/Netačno' },
                ].map((type) => (
                  <button
                    key={type.value}
                    onClick={() => handleQuestionTypeToggle(type.value)}
                    className={clsx(
                      "px-4 py-2 rounded-lg border-2 transition-all",
                      formData.question_types.includes(type.value)
                        ? "border-primary-500 bg-primary-50 text-primary-700"
                        : "border-gray-200 text-gray-600 hover:border-gray-300"
                    )}
                  >
                    {type.label}
                  </button>
                ))}
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Težina
              </label>
              <div className="grid grid-cols-4 gap-2">
                {[
                  { value: 'easy', label: 'Lako', color: 'green' },
                  { value: 'medium', label: 'Srednje', color: 'yellow' },
                  { value: 'hard', label: 'Teško', color: 'red' },
                  { value: 'mixed', label: 'Mešano', color: 'primary' },
                ].map((diff) => (
                  <button
                    key={diff.value}
                    onClick={() => setFormData(prev => ({ ...prev, difficulty: diff.value as any }))}
                    className={clsx(
                      "px-4 py-2 rounded-lg border-2 transition-all",
                      formData.difficulty === diff.value
                        ? `border-${diff.color}-500 bg-${diff.color}-50 text-${diff.color}-700`
                        : "border-gray-200 text-gray-600 hover:border-gray-300"
                    )}
                  >
                    {diff.label}
                  </button>
                ))}
              </div>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  <Clock className="w-4 h-4 inline mr-1" />
                  Vremensko ograničenje (min)
                </label>
                <input
                  type="number"
                  min="0"
                  max="120"
                  value={formData.time_limit}
                  onChange={(e) => setFormData(prev => ({ ...prev, time_limit: parseInt(e.target.value) || 0 }))}
                  className="input"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  <Target className="w-4 h-4 inline mr-1" />
                  Prolazni rezultat (%)
                </label>
                <input
                  type="number"
                  min="0"
                  max="100"
                  value={formData.passing_score}
                  onChange={(e) => setFormData(prev => ({ ...prev, passing_score: parseInt(e.target.value) || 0 }))}
                  className="input"
                />
              </div>
            </div>
          </div>

          <div className="flex justify-between mt-6">
            <button onClick={() => setStep(1)} className="btn-secondary">
              Nazad
            </button>
            <button onClick={() => setStep(3)} className="btn-primary">
              Sledeće
            </button>
          </div>
        </div>
      )}

      {step === 3 && (
        <div className="card p-6">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">Pregled i generisanje</h2>
          
          <div className="space-y-4 mb-6">
            <div className="flex items-center gap-3 p-3 bg-gray-50 rounded-lg">
              <FileText className="w-5 h-5 text-gray-500" />
              <div>
                <p className="text-sm text-gray-500">Dokument</p>
                <p className="font-medium">{selectedDocument?.title || 'Nije izabrano'}</p>
              </div>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div className="flex items-center gap-3 p-3 bg-gray-50 rounded-lg">
                <Target className="w-5 h-5 text-gray-500" />
                <div>
                  <p className="text-sm text-gray-500">Broj pitanja</p>
                  <p className="font-medium">{formData.num_questions}</p>
                </div>
              </div>
              <div className="flex items-center gap-3 p-3 bg-gray-50 rounded-lg">
                <Award className="w-5 h-5 text-gray-500" />
                <div>
                  <p className="text-sm text-gray-500">Težina</p>
                  <p className="font-medium capitalize">{formData.difficulty}</p>
                </div>
              </div>
              <div className="flex items-center gap-3 p-3 bg-gray-50 rounded-lg">
                <Clock className="w-5 h-5 text-gray-500" />
                <div>
                  <p className="text-sm text-gray-500">Vreme</p>
                  <p className="font-medium">{formData.time_limit} min</p>
                </div>
              </div>
              <div className="flex items-center gap-3 p-3 bg-gray-50 rounded-lg">
                <CheckCircle className="w-5 h-5 text-gray-500" />
                <div>
                  <p className="text-sm text-gray-500">Prolaznost</p>
                  <p className="font-medium">{formData.passing_score}%</p>
                </div>
              </div>
            </div>
          </div>

          <div className="bg-amber-50 border border-amber-200 rounded-xl p-4 mb-6">
            <div className="flex items-start gap-3">
              <AlertCircle className="w-5 h-5 text-amber-600 flex-shrink-0 mt-0.5" />
              <div>
                <p className="text-sm text-amber-800">
                  Generisanje kviza može trajati nekoliko minuta. Kviz će biti dostupan nakon što se završi.
                </p>
              </div>
            </div>
          </div>

          <div className="flex justify-between">
            <button onClick={() => setStep(2)} className="btn-secondary">
              Nazad
            </button>
            <button
              onClick={handleSubmit}
              disabled={generateMutation.isPending}
              className="btn-primary"
            >
              {generateMutation.isPending ? (
                <>
                  <Loader2 className="w-5 h-5 animate-spin" />
                  Generišem...
                </>
              ) : (
                <>
                  <Sparkles className="w-5 h-5" />
                  Generiši kviz
                </>
              )}
            </button>
          </div>
        </div>
      )}
    </div>
  )
}
