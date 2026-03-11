/**
 * Hook for SSE connection to job events stream.
 *
 * Connects to the backend SSE endpoint and dispatches
 * job_started / job_progress / job_completed / job_failed
 * events to a caller-provided callback.
 */
import { useState, useEffect, useRef, useCallback } from 'react'
import type { JobEvent } from '../types/schedule'

const SSE_URL = 'http://localhost:8000/api/jobs/events/stream'

interface UseJobEventsResult {
  lastEvent: JobEvent | null
  connected: boolean
}

export function useJobEvents(onEvent?: (event: JobEvent) => void): UseJobEventsResult {
  const [lastEvent, setLastEvent] = useState<JobEvent | null>(null)
  const [connected, setConnected] = useState(false)

  // Store onEvent in a ref so changes don't trigger reconnection
  const onEventRef = useRef(onEvent)
  onEventRef.current = onEvent

  const handleMessage = useCallback((eventType: string, data: any) => {
    const jobEvent: JobEvent = {
      event: eventType as JobEvent['event'],
      data,
    }
    setLastEvent(jobEvent)
    onEventRef.current?.(jobEvent)
  }, [])

  useEffect(() => {
    const eventSource = new EventSource(SSE_URL)

    eventSource.onopen = () => {
      setConnected(true)
    }

    eventSource.onerror = () => {
      setConnected(false)
    }

    // Listen for each event type
    const eventTypes = ['job_started', 'job_progress', 'job_completed', 'job_failed']
    eventTypes.forEach(type => {
      eventSource.addEventListener(type, (e: MessageEvent) => {
        try {
          const data = JSON.parse(e.data)
          handleMessage(type, data)
        } catch (err) {
          console.error(`Failed to parse SSE event ${type}:`, err)
        }
      })
    })

    // Also listen for generic messages (keepalive pings)
    eventSource.onmessage = () => {
      // keepalive — ignore
    }

    return () => {
      eventSource.close()
      setConnected(false)
    }
  }, [handleMessage])

  return { lastEvent, connected }
}
