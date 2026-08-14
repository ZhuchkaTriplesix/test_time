/**
 * Корневой компонент операционной панели мониторинга SLA (App.jsx).
 *
 * Назначение:
 * - Управление состоянием данных: метрики, открытые тикеты, доступные топики.
 * - Периодический опрос API (поллинг каждые 10 секунд) с возможностью паузы.
 * - Координация взаимодействия с модальными окнами ответа оператора и создания событий.
 * - Отображение Toast-уведомлений об успешных ответах и закрытии тикетов.
 */
import React, { useState, useEffect, useCallback } from 'react'
import { MetricsPanel } from './components/MetricsPanel'
import { FilterBar } from './components/FilterBar'
import { TicketTable } from './components/TicketTable'
import { OperatorReplyModal } from './components/OperatorReplyModal'
import { CreateEventModal } from './components/CreateEventModal'
import { Toast } from './components/Toast'

export function App() {
  const [metrics, setMetrics] = useState(null)
  const [tickets, setTickets] = useState([])
  const [topics, setTopics] = useState([])
  const [selectedTopic, setSelectedTopic] = useState('')
  const [isAutoRefresh, setIsAutoRefresh] = useState(true)
  const [isLoading, setIsLoading] = useState(false)
  const [lastUpdated, setLastUpdated] = useState(null)

  // Modals state
  const [isNewEventModalOpen, setIsNewEventModalOpen] = useState(false)
  const [isReplyModalOpen, setIsReplyModalOpen] = useState(false)
  const [activeReplyTicket, setActiveReplyTicket] = useState(null)

  // Toast state
  const [toast, setToast] = useState(null)

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

  // Handle client new event creation
  const handleCreateClientEvent = async (eventPayload) => {
    try {
      const res = await fetch('/api/events', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(eventPayload),
      })
      if (!res.ok) {
        const err = await res.json()
        throw new Error(err.detail || 'Не удалось создать обращение')
      }
      setToast({
        type: 'success',
        title: 'Обращение создано',
        message: `Новый тикет от ${eventPayload.external_client_id} добавлен в очередь`,
      })
      await fetchData()
    } catch (err) {
      setToast({
        type: 'error',
        title: 'Ошибка создания',
        message: err.message,
      })
      throw err
    }
  }

  // Handle agent reply & ticket closing
  const handleAnswerTicket = async (eventPayload, ticket) => {
    try {
      const res = await fetch('/api/events', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(eventPayload),
      })
      if (!res.ok) {
        const err = await res.json()
        throw new Error(err.detail || 'Не удалось отправить ответ')
      }

      const waitTimeText =
        ticket.wait_time_seconds < 60
          ? `${Math.floor(ticket.wait_time_seconds)} сек`
          : `${Math.floor(ticket.wait_time_seconds / 60)}м ${Math.floor(ticket.wait_time_seconds % 60)}с`

      setToast({
        type: 'success',
        title: 'Ответ отправлен клиенту!',
        message: `Обращение #${ticket.id.slice(0, 8)} закрыто за ${waitTimeText}. Метрики обновлены.`,
      })
      await fetchData()
    } catch (err) {
      setToast({
        type: 'error',
        title: 'Ошибка отправки ответа',
        message: err.message,
      })
      throw err
    }
  }

  const handleOpenReplyModal = (ticket) => {
    setActiveReplyTicket(ticket)
    setIsReplyModalOpen(true)
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
          <button className="btn btn-primary" onClick={() => setIsNewEventModalOpen(true)}>
            <span>+</span>
            <span>Новое обращение</span>
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
        onAnswerTicket={handleOpenReplyModal}
      />

      {/* Operator reply modal */}
      <OperatorReplyModal
        isOpen={isReplyModalOpen}
        onClose={() => {
          setIsReplyModalOpen(false)
          setActiveReplyTicket(null)
        }}
        ticket={activeReplyTicket}
        onSubmit={handleAnswerTicket}
      />

      {/* Simulation new event modal */}
      <CreateEventModal
        isOpen={isNewEventModalOpen}
        onClose={() => setIsNewEventModalOpen(false)}
        onSubmit={handleCreateClientEvent}
      />

      {/* Toast notifications */}
      <Toast toast={toast} onClose={() => setToast(null)} />
    </div>
  )
}
