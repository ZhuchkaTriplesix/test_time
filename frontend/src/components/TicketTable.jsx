/**
 * Компонент таблицы открытых обращений (TicketTable.jsx).
 *
 * Назначение:
 * - Отображение обращений с секундомером ожидания и понятным бейджем SLA (текст + цвет: NORMAL, WARNING, OVERDUE).
 * - Быстрое действие "💬 Ответить" для открытия удобного окна ответа оператора.
 */
import React from 'react'

export function TicketTable({ tickets, total, onAnswerTicket }) {
  const renderSlaBadge = (slaStatus) => {
    switch (slaStatus) {
      case 'overdue':
        return (
          <span className="sla-badge sla-overdue">
            <span>🚨</span>
            <span>OVERDUE (&gt;180с)</span>
          </span>
        )
      case 'warning':
        return (
          <span className="sla-badge sla-warning">
            <span>⚠️</span>
            <span>WARNING (&gt;60с)</span>
          </span>
        )
      default:
        return (
          <span className="sla-badge sla-normal">
            <span>🟢</span>
            <span>NORMAL</span>
          </span>
        )
    }
  }

  const formatWaitTime = (seconds) => {
    if (seconds < 60) {
      return `${Math.floor(seconds)} сек`
    }
    const mins = Math.floor(seconds / 60)
    const secs = Math.floor(seconds % 60)
    return `${mins}м ${secs}с`
  }

  return (
    <div className="table-card">
      <div className="table-header-title">
        <div className="title-with-badge">
          <h2>Очередь открытых обращений</h2>
          <span className="badge-count">{total} ожидает ответа</span>
        </div>
        <div className="table-hint-text">
          Кликните <strong>«💬 Ответить»</strong> на любом обращении для быстрой отправки ответа
        </div>
      </div>

      {tickets.length === 0 ? (
        <div className="empty-state">
          <div className="empty-state-icon">🎉</div>
          <h3>Все обращения обработаны!</h3>
          <p>В данный момент нет открытых тикетов, ожидающих первой реакции.</p>
        </div>
      ) : (
        <table className="tickets-table">
          <thead>
            <tr>
              <th>Клиент / Канал</th>
              <th>Направление</th>
              <th>Содержание обращения</th>
              <th>Время ожидания</th>
              <th>SLA-статус</th>
              <th style={{ textAlign: 'right' }}>Действие</th>
            </tr>
          </thead>
          <tbody>
            {tickets.map((ticket) => (
              <tr
                key={ticket.id}
                className={
                  ticket.sla_status === 'overdue'
                    ? 'row-overdue'
                    : ticket.sla_status === 'warning'
                    ? 'row-warning'
                    : ''
                }
              >
                <td>
                  <div className="client-cell">
                    <span className="cell-avatar">👤</span>
                    <div>
                      <strong>{ticket.external_client_id}</strong>
                      <div className="ticket-id-hint">#{ticket.id.slice(0, 8)}</div>
                    </div>
                  </div>
                </td>
                <td>
                  <span className="topic-tag">{ticket.topic}</span>
                </td>
                <td style={{ maxWidth: '420px' }}>
                  <div className="ticket-content-preview">{ticket.content}</div>
                </td>
                <td>
                  <span
                    className="wait-timer"
                    style={{
                      color:
                        ticket.sla_status === 'overdue'
                          ? '#f87171'
                          : ticket.sla_status === 'warning'
                          ? '#fde047'
                          : '#6ee7b7',
                    }}
                  >
                    ⏱ {formatWaitTime(ticket.wait_time_seconds)}
                  </span>
                </td>
                <td>{renderSlaBadge(ticket.sla_status)}</td>
                <td style={{ textAlign: 'right' }}>
                  <button
                    className="btn btn-reply-action"
                    onClick={() => onAnswerTicket(ticket)}
                    title="Открыть форму ответа клиенту"
                  >
                    <span>💬</span>
                    <span>Ответить</span>
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  )
}
