'use client'

import { useState, useEffect } from 'react'
import { X, Play, RefreshCw } from 'lucide-react'
import { Workflow } from '@/lib/api'
import { cn } from '@/lib/utils'

interface TriggerWorkflowModalProps {
  workflow: Workflow
  open: boolean
  onClose: () => void
  onTrigger: (inputs: Record<string, string | boolean>) => void
  isLoading: boolean
}

export function TriggerWorkflowModal({
  workflow,
  open,
  onClose,
  onTrigger,
  isLoading,
}: TriggerWorkflowModalProps) {
  const [inputs, setInputs] = useState<Record<string, string | boolean>>({})

  // Initialize inputs with defaults when workflow changes
  useEffect(() => {
    const defaults: Record<string, string | boolean> = {}
    workflow.inputs.forEach((input) => {
      if (input.type === 'boolean') {
        // Handle various truthy string values
        const defaultVal = (input.default || '').toLowerCase()
        defaults[input.name] = defaultVal === 'true' || defaultVal === 'yes' || defaultVal === '1'
      } else {
        // Always use empty string for undefined/null to keep input controlled
        defaults[input.name] = input.default ?? ''
      }
    })
    setInputs(defaults)
  }, [workflow])

  if (!open) return null

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    // Convert all values to strings for GitHub API, skip empty optional fields
    const stringInputs: Record<string, string> = {}
    workflow.inputs.forEach((input) => {
      const value = inputs[input.name]
      const strValue = String(value)
      // Only include non-empty values, or required fields, or boolean fields
      if (strValue !== '' || input.required || input.type === 'boolean') {
        stringInputs[input.name] = strValue
      }
    })
    onTrigger(stringInputs)
  }

  return (
    <div className="fixed inset-0 z-[100] flex items-center justify-center">
      {/* Backdrop */}
      <div className="absolute inset-0 bg-black/70 backdrop-blur-sm" onClick={onClose} />

      {/* Modal */}
      <div className="relative bg-white rounded-2xl shadow-2xl w-full max-w-lg mx-4 max-h-[90vh] overflow-hidden ring-1 ring-black/10">
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-stone-200">
          <h2 className="text-lg font-semibold text-stone-900">Run {workflow.name}</h2>
          <button
            onClick={onClose}
            className="p-1 rounded-lg text-stone-400 hover:text-stone-600 hover:bg-stone-100 transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Content */}
        <form onSubmit={handleSubmit}>
          <div className="px-6 py-4 space-y-4 max-h-[60vh] overflow-y-auto">
            {workflow.inputs.length === 0 ? (
              <div className="text-center py-4 text-stone-500">
                This workflow has no input parameters. Click &quot;Run Workflow&quot; to start.
              </div>
            ) : (
              workflow.inputs.map((input) => (
                <div key={input.name}>
                  <label className="block text-sm font-medium text-stone-700 mb-1">
                    {input.name}
                    {input.required && <span className="text-red-500 ml-1">*</span>}
                  </label>

                  {input.description && (
                    <p className="text-xs text-stone-500 mb-2">{input.description}</p>
                  )}

                  {input.type === 'boolean' ? (
                    <label className="flex items-center gap-2 cursor-pointer">
                      <input
                        type="checkbox"
                        checked={Boolean(inputs[input.name])}
                        onChange={(e) =>
                          setInputs({
                            ...inputs,
                            [input.name]: e.target.checked,
                          })
                        }
                        className="w-4 h-4 rounded border-stone-300 text-youdle-600 focus:ring-youdle-500"
                      />
                      <span className="text-sm text-stone-600">Enable</span>
                    </label>
                  ) : input.type === 'choice' && input.options ? (
                    <select
                      value={String(inputs[input.name] ?? '')}
                      onChange={(e) =>
                        setInputs({
                          ...inputs,
                          [input.name]: e.target.value,
                        })
                      }
                      required={input.required}
                      className="w-full px-3 py-2 rounded-lg border border-stone-300 text-stone-900 focus:outline-none focus:ring-2 focus:ring-youdle-500 focus:border-transparent"
                    >
                      {input.options.map((option) => (
                        <option key={option} value={option}>
                          {option}
                        </option>
                      ))}
                    </select>
                  ) : (
                    <input
                      type="text"
                      value={String(inputs[input.name] ?? '')}
                      onChange={(e) =>
                        setInputs({
                          ...inputs,
                          [input.name]: e.target.value,
                        })
                      }
                      required={input.required}
                      placeholder={input.default || ''}
                      className="w-full px-3 py-2 rounded-lg border border-stone-300 text-stone-900 placeholder:text-stone-400 focus:outline-none focus:ring-2 focus:ring-youdle-500 focus:border-transparent"
                    />
                  )}
                </div>
              ))
            )}
          </div>

          {/* Footer */}
          <div className="flex items-center justify-end gap-3 px-6 py-4 border-t border-stone-200 bg-stone-50">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 text-sm font-medium text-stone-600 hover:text-stone-900 hover:bg-stone-100 rounded-lg transition-colors"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={isLoading}
              className={cn(
                'flex items-center gap-2 px-4 py-2 text-sm font-medium text-white rounded-lg transition-colors',
                isLoading ? 'bg-youdle-400 cursor-not-allowed' : 'bg-youdle-600 hover:bg-youdle-700'
              )}
            >
              {isLoading ? (
                <>
                  <RefreshCw className="w-4 h-4 animate-spin" />
                  Triggering...
                </>
              ) : (
                <>
                  <Play className="w-4 h-4" />
                  Run Workflow
                </>
              )}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}
