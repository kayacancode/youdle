'use client'

import { useState } from 'react'
import { Settings, Save, RefreshCw, Database, Server, Key } from 'lucide-react'
import { cn } from '@/lib/utils'

export default function SettingsPage() {
  const [config, setConfig] = useState({
    batchSize: 10,
    searchDaysBack: 30,
    model: 'gpt-4',
    usePlaceholderImages: false,
    useLegacyOrchestrator: false,
  })

  const [isSaving, setIsSaving] = useState(false)
  const [saved, setSaved] = useState(false)

  const handleSave = async () => {
    setIsSaving(true)
    // In a real app, this would save to localStorage or an API
    await new Promise(resolve => setTimeout(resolve, 500))
    localStorage.setItem('youdle_config', JSON.stringify(config))
    setIsSaving(false)
    setSaved(true)
    setTimeout(() => setSaved(false), 2000)
  }

  return (
    <div className="space-y-8 animate-fade-in max-w-3xl">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold text-stone-900">
          Settings
        </h1>
        <p className="mt-2 text-stone-500">
          Configure your blog generation pipeline and API connections.
        </p>
      </div>

      {/* Generation Settings */}
      <div className="rounded-2xl bg-white border border-stone-200 p-6">
        <div className="flex items-center gap-3 mb-6">
          <div className="w-10 h-10 rounded-xl bg-youdle-100 dark:bg-youdle-900/30 flex items-center justify-center">
            <Settings className="w-5 h-5 text-youdle-600 dark:text-youdle-400" />
          </div>
          <div>
            <h2 className="text-lg font-semibold text-stone-900">
              Generation Settings
            </h2>
            <p className="text-sm text-stone-500">
              Default parameters for blog post generation
            </p>
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div>
            <label className="block text-sm font-medium text-midnight-700 mb-2">
              Default Batch Size
            </label>
            <input
              type="number"
              min={1}
              max={50}
              value={config.batchSize}
              onChange={(e) => setConfig({ ...config, batchSize: parseInt(e.target.value) || 10 })}
              className="w-full px-3 py-2 rounded-lg border border-midnight-300 bg-white text-stone-900 focus:ring-2 focus:ring-youdle-500 focus:border-transparent"
            />
            <p className="mt-1 text-xs text-stone-500">
              Number of articles to process per run
            </p>
          </div>

          <div>
            <label className="block text-sm font-medium text-midnight-700 mb-2">
              Search Days Back
            </label>
            <input
              type="number"
              min={1}
              max={90}
              value={config.searchDaysBack}
              onChange={(e) => setConfig({ ...config, searchDaysBack: parseInt(e.target.value) || 30 })}
              className="w-full px-3 py-2 rounded-lg border border-midnight-300 bg-white text-stone-900 focus:ring-2 focus:ring-youdle-500 focus:border-transparent"
            />
            <p className="mt-1 text-xs text-stone-500">
              How far back to search for articles
            </p>
          </div>

          <div>
            <label className="block text-sm font-medium text-midnight-700 mb-2">
              LLM Model
            </label>
            <select
              value={config.model}
              onChange={(e) => setConfig({ ...config, model: e.target.value })}
              className="w-full px-3 py-2 rounded-lg border border-midnight-300 bg-white text-stone-900 focus:ring-2 focus:ring-youdle-500 focus:border-transparent"
            >
              <option value="gpt-4">GPT-4</option>
              <option value="gpt-4-turbo">GPT-4 Turbo</option>
              <option value="gpt-3.5-turbo">GPT-3.5 Turbo</option>
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-midnight-700 mb-2">
              Options
            </label>
            <div className="space-y-3">
              <label className="flex items-center gap-3">
                <input
                  type="checkbox"
                  checked={config.usePlaceholderImages}
                  onChange={(e) => setConfig({ ...config, usePlaceholderImages: e.target.checked })}
                  className="w-4 h-4 rounded border-midnight-300 text-youdle-500 focus:ring-youdle-500"
                />
                <span className="text-sm text-midnight-700">
                  Use placeholder images (skip Gemini)
                </span>
              </label>
              <label className="flex items-center gap-3">
                <input
                  type="checkbox"
                  checked={config.useLegacyOrchestrator}
                  onChange={(e) => setConfig({ ...config, useLegacyOrchestrator: e.target.checked })}
                  className="w-4 h-4 rounded border-midnight-300 text-youdle-500 focus:ring-youdle-500"
                />
                <span className="text-sm text-midnight-700">
                  Use legacy orchestrator (skip LangGraph)
                </span>
              </label>
            </div>
          </div>
        </div>
      </div>

      {/* API Status */}
      <div className="rounded-2xl bg-white border border-stone-200 p-6">
        <div className="flex items-center gap-3 mb-6">
          <div className="w-10 h-10 rounded-xl bg-blue-100 dark:bg-blue-900/30 flex items-center justify-center">
            <Server className="w-5 h-5 text-blue-600 dark:text-blue-400" />
          </div>
          <div>
            <h2 className="text-lg font-semibold text-stone-900">
              API Connections
            </h2>
            <p className="text-sm text-stone-500">
              Status of external services
            </p>
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {[
            { name: 'FastAPI Backend', endpoint: 'http://localhost:8000', status: 'connected' },
            { name: 'Supabase', endpoint: 'Connected', status: 'connected' },
            { name: 'OpenAI API', endpoint: 'Configured', status: 'configured' },
            { name: 'Exa Search API', endpoint: 'Configured', status: 'configured' },
            { name: 'Google Gemini', endpoint: 'Configured', status: 'configured' },
          ].map((service) => (
            <div
              key={service.name}
              className="flex items-center justify-between p-3 rounded-xl bg-midnight-50"
            >
              <div className="flex items-center gap-3">
                <div className={cn(
                  'w-2 h-2 rounded-full',
                  service.status === 'connected' ? 'bg-green-500' : 'bg-yellow-500'
                )} />
                <div>
                  <p className="text-sm font-medium text-stone-900">
                    {service.name}
                  </p>
                  <p className="text-xs text-stone-500">
                    {service.endpoint}
                  </p>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Environment Variables Info */}
      <div className="rounded-2xl bg-white border border-stone-200 p-6">
        <div className="flex items-center gap-3 mb-6">
          <div className="w-10 h-10 rounded-xl bg-purple-100 dark:bg-purple-900/30 flex items-center justify-center">
            <Key className="w-5 h-5 text-purple-600 dark:text-purple-400" />
          </div>
          <div>
            <h2 className="text-lg font-semibold text-stone-900">
              Environment Variables
            </h2>
            <p className="text-sm text-stone-500">
              Required environment variables for the system
            </p>
          </div>
        </div>

        <div className="bg-midnight-50 rounded-lg p-4 font-mono text-sm">
          <pre className="text-midnight-600 whitespace-pre-wrap">
{`# Frontend (.env.local)
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_SUPABASE_URL=your-supabase-url
NEXT_PUBLIC_SUPABASE_ANON_KEY=your-supabase-key

# Backend (.env)
OPENAI_API_KEY=your-openai-key
EXA_API_KEY=your-exa-key
GOOGLE_API_KEY=your-gemini-key
SUPABASE_URL=your-supabase-url
SUPABASE_KEY=your-supabase-key`}
          </pre>
        </div>
      </div>

      {/* Save Button */}
      <div className="flex justify-end">
        <button
          onClick={handleSave}
          disabled={isSaving}
          className={cn(
            'flex items-center gap-2 px-6 py-3 rounded-xl font-medium transition-all',
            'bg-gradient-to-r from-youdle-500 to-youdle-600 text-white',
            'hover:from-youdle-600 hover:to-youdle-700 hover:shadow-lg hover:shadow-youdle-500/25',
            'disabled:opacity-50 disabled:cursor-not-allowed'
          )}
        >
          {isSaving ? (
            <RefreshCw className="w-4 h-4 animate-spin" />
          ) : saved ? (
            <>
              <Save className="w-4 h-4" />
              Saved!
            </>
          ) : (
            <>
              <Save className="w-4 h-4" />
              Save Settings
            </>
          )}
        </button>
      </div>
    </div>
  )
}



