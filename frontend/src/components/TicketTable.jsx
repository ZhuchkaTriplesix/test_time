/**
 * Компонент таблицы открытых обращений.
 *
 * Назначение:
 * - Отображение обращений с секундомером ожидания и понятным бейджем SLA (текст + цвет: NORMAL, WARNING, OVERDUE).
 * - Быстрое действие "Ответить" для закрытия тикета.
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
        <h2>Открытые обращения, требующие ответа</h2>
        <span className="badge-count">{total} открыто</span>
      </div>

      {tickets.length === 0 ? (
        <div className="empty-state">
          <div className="empty-state-icon">🎉</div>
          <h3>Все обращения закрыты</h3>
          <p>В данный момент нет открытых тикетов, ожидающих ответа.</p>
        </div>
      ) : (
        <table className="tickets-table">
          <thead>
            <tr>
              <th>Клиент / Источник</th>
              <th>Направление</th>
              <th>Содержание обращения</th>
              <th>Время ожидания</th>
              <th>SLA-статус</th>
              <th>Действие</th>
            </tr>
          </thead>
          <tbody>
            {tickets.map((ticket) => (
              <tr key={ticket.id}>
                <td>
                  <strong>{ticket.external_client_id}</strong>
                </td>
                <td>
                  <span className="topic-tag">{ticket.topic}</span>
                </td>
                <td style={{ maxWidth: '380px' }}>
                  <div style={{ wordBreak: 'break-word' }}>{ticket.content}</div>
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
                <td>
                  <button
                    className="btn btn-primary"
                    style={{ padding: '0.35rem 0.75rem', fontSize: '0.75rem' }}
                    onClick={() => onAnswerTicket(ticket)}
                  >
                    Ответить
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
