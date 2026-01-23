import { useState, useEffect, useRef, useCallback } from 'react'
import { useDebounce } from './useDebounce'

export type AutosaveStatus = 'idle' | 'saving' | 'saved' | 'error'

interface UseAutosaveOptions<T> {
  /** Data to save */
  data: T
  /** Function to save the data */
  onSave: (data: T) => Promise<void>
  /** Validation function - returns error message or null if valid */
  validate?: (data: T) => string | null
  /** Debounce delay in milliseconds (default: 2000) */
  delay?: number
  /** Whether autosave is enabled (default: true) */
  enabled?: boolean
  /** How long to show "Saved" status before returning to idle (default: 2000) */
  savedDisplayDuration?: number
}

interface UseAutosaveReturn {
  /** Current autosave status */
  status: AutosaveStatus
  /** Error message if status is 'error' */
  error: string | null
  /** Manually trigger a save */
  save: () => Promise<void>
}

/**
 * Hook for autosaving data with debounce.
 * Automatically saves data after a period of inactivity.
 */
export function useAutosave<T>({
  data,
  onSave,
  validate,
  delay = 2000,
  enabled = true,
  savedDisplayDuration = 2000,
}: UseAutosaveOptions<T>): UseAutosaveReturn {
  const [status, setStatus] = useState<AutosaveStatus>('idle')
  const [error, setError] = useState<string | null>(null)

  // Use refs to avoid dependency issues
  const dataRef = useRef<T>(data)
  const onSaveRef = useRef(onSave)
  const validateRef = useRef(validate)
  const initialDataRef = useRef<string>(JSON.stringify(data))
  const isFirstRender = useRef(true)
  const savedTimeoutRef = useRef<NodeJS.Timeout | null>(null)
  const isSavingRef = useRef(false)

  // Keep refs updated
  dataRef.current = data
  onSaveRef.current = onSave
  validateRef.current = validate

  const debouncedData = useDebounce(data, delay)

  const save = useCallback(async () => {
    const currentData = dataRef.current

    // Validate if validation function provided
    if (validateRef.current) {
      const validationError = validateRef.current(currentData)
      if (validationError) {
        setStatus('error')
        setError(validationError)
        return
      }
    }

    // Prevent concurrent saves
    if (isSavingRef.current) return
    isSavingRef.current = true

    setStatus('saving')
    setError(null)

    try {
      await onSaveRef.current(currentData)
      setStatus('saved')

      // Clear any existing timeout
      if (savedTimeoutRef.current) {
        clearTimeout(savedTimeoutRef.current)
      }

      // Return to idle after savedDisplayDuration
      savedTimeoutRef.current = setTimeout(() => {
        setStatus('idle')
      }, savedDisplayDuration)

      // Update initial data ref since we've saved
      initialDataRef.current = JSON.stringify(currentData)
    } catch (err) {
      setStatus('error')
      setError(err instanceof Error ? err.message : 'Failed to save')
    } finally {
      isSavingRef.current = false
    }
  }, [savedDisplayDuration])

  // Autosave when debounced data changes
  useEffect(() => {
    // Skip on first render
    if (isFirstRender.current) {
      isFirstRender.current = false
      return
    }

    // Don't save if disabled
    if (!enabled) return

    // Don't save if data hasn't actually changed from initial
    const currentDataString = JSON.stringify(debouncedData)
    if (currentDataString === initialDataRef.current) return

    save()
  }, [debouncedData, enabled, save])

  // Reset when enabled changes (e.g., modal opens/closes)
  useEffect(() => {
    if (enabled) {
      // Reset state when autosave becomes enabled (modal opened)
      initialDataRef.current = JSON.stringify(data)
      isFirstRender.current = true
      setStatus('idle')
      setError(null)
    }
  }, [enabled]) // eslint-disable-line react-hooks/exhaustive-deps

  // Cleanup timeout on unmount
  useEffect(() => {
    return () => {
      if (savedTimeoutRef.current) {
        clearTimeout(savedTimeoutRef.current)
      }
    }
  }, [])

  return { status, error, save }
}
