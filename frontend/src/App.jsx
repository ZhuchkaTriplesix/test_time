import React, { useState, useEffect, useCallback } from 'react'
import { MetricsPanel } from './components/MetricsPanel'
import { FilterBar } from './components/FilterBar'
import { TicketTable } from './components/TicketTable'
import { CreateEventModal } from './components/CreateEventModal'

export function App() {
  const [metrics, setMetrics] = useState(null)
  const [tickets, setTickets] = useState([])
  const [topics, setTopics] = useState([])
  const [selectedTopic, setSelectedTopic] = useState('')
  const [isAutoRefresh, setIsAutoRefresh] = useState(true)
  const [isLoading, setIsLoading] = useState(false)
  const [lastUpdated, setLastUpdated] = useState(null)
  const [isModalOpen, setIsModalOpen] = useState(false)
  const [modalTicket, setModalTicket] = useState(null)

  const fetchData = useCallback(async () => {
    setIsLoading(true)
    try {
      // 1. Fetch metrics
      const metricsRes = await fetch('/api/metrics')
      if (metricsRes.ok) {
        const metricsData = await metricsRes.json()
        setMetrics(metricsData)
      }

      // 2. Fetch tickets
      const url = selectedTopic
        ? `/api/tickets?topic=${encodeURIComponent(selectedTopic)}`
        : '/api/tickets'
      const ticketsRes = await fetch(url)
      if (ticketsRes.ok) {
        const ticketsData = await ticketsRes.json()
        setTickets(ticketsData.tickets || [])
        setTopics(ticketsData.available_topics || [])
      }

      setLastUpdated(new Date())
    } catch (err) {
      console.error('Error fetching data:', err)
    } finally {
      setIsLoading(false)
    }
  }, [selectedTopic])

  // Polling effect every 10 seconds
  useEffect(() => {
    fetchData()
    if (!isAutoRefresh) return

    const interval = setInterval(() => {
      fetchData()
    }, 10000)

    return () => clearInterval(interval)
  }, [fetchData, isAutoRefresh])

  const handleSendEvent = async (eventPayload) => {
    const res = await fetch('/api/events', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(eventPayload),
    })
    if (!res.ok) {
      const err = await res.json()
      throw new Error(err.detail || 'Не удалось отправить событие')
    }
    await fetchData()
  }

  const handleOpenAnswerModal = (ticket) => {
    setModalTicket(ticket)
    setIsModalOpen(true)
  }

  const handleOpenNewEventModal = () => {
    setModalTicket(null)
    setIsModalOpen(true)
  }

  return (
    <div className="container">
      <header className="app-header">
        <div className="header-title">
          <h1>
            <span>⏱️</span> SLA Response Time Control
          </h1>
          <p>
            Мониторинг времени первой реакции операционных команд и контроль нарушений SLA
          </p>
        </div>
        <div className="header-actions">
          <button className="btn btn-primary" onClick={handleOpenNewEventModal}>
            + Отправить событие
          </button>
        </div>
      </header>

      <MetricsPanel metrics={metrics} />

      <FilterBar
        selectedTopic={selectedTopic}
        onTopicChange={setSelectedTopic}
        topics={topics}
        isAutoRefresh={isAutoRefresh}
        onToggleAutoRefresh={() => setIsAutoRefresh((prev) => !prev)}
        onManualRefresh={fetchData}
        isLoading={isLoading}
        lastUpdated={lastUpdated}
      />

      <TicketTable
        tickets={tickets}
        total={tickets.length}
        onAnswerTicket={handleOpenAnswerModal}
      />

      <CreateEventModal
        isOpen={isModalOpen}
        onClose={() => {
          setIsModalOpen(false)
          setModalTicket(null)
        }}
        onSubmit={handleSendEvent}
        initialTicket={modalTicket}
      />
    </div>
  )
}
