/**
 * Компонент таблицы открытых обращений (Ticket Data Table).
 *
 * Назначение:
 * - Вывод активных тикетов в виде структурированной таблицы с моноширинными ID и таймерами.
 * - Строгая индикация SLA-уровней: NORMAL (зеленый), WARNING (желтый), OVERDUE (красный).
 * - Кнопка "Resolve" для быстрого ответа и закрытия тикета.
 */
import React from 'react'

export function TicketTable({ tickets, total, onAnswerTicket }) {
  const renderSlaBadge = (slaStatus) => {
    switch (slaStatus) {
      case 'overdue':
        return (
          <span className="sla-badge sla-overdue">
            <span className="sla-dot dot-overdue"></span>
            <span>OVERDUE (&gt;180s)</span>
          </span>
        )
      case 'warning':
        return (
          <span className="sla-badge sla-warning">
            <span className="sla-dot dot-warning"></span>
            <span>WARNING (&gt;60s)</span>
          </span>
        )
      default:
        return (
          <span className="sla-badge sla-normal">
            <span className="sla-dot dot-normal"></span>
            <span>NORMAL</span>
          </span>
        )
    }
  }

  const formatWaitTime = (seconds) => {
    if (seconds < 60) {
      return `${Math.floor(seconds)}s`
    }
    const mins = Math.floor(seconds / 60)
    const secs = Math.floor(seconds % 60)
    return `${mins}m ${secs}s`
  }

  return (
    <div className="table-card">
      <div className="table-header-title">
        <div className="title-with-badge">
          <h2>Очередь открытых обращений</h2>
          <span className="badge-count">{total} OPEN</span>
        </div>
        <div className="table-hint-text">
          Пороговые значения SLA: Warning = 60s, Overdue = 180s
        </div>
      </div>

      {tickets.length === 0 ? (
        <div className="empty-state">
          <div className="empty-state-icon">✓</div>
          <h3>Очередь чиста</h3>
          <p>Все обращения закрыты. Время первой реакции зафиксировано.</p>
        </div>
      ) : (
        <div className="table-responsive">
          <table className="tickets-table">
            <thead>
              <tr>
                <th style={{ width: '180px' }}>ID / Клиент</th>
                <th style={{ width: '180px' }}>Направление</th>
                <th>Содержание обращения</th>
                <th style={{ width: '130px' }}>Ожидание</th>
                <th style={{ width: '160px' }}>SLA Уровень</th>
                <th style={{ width: '110px', textAlign: 'right' }}>Действие</th>
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
                      <span className="ticket-id-badge">#{ticket.id.slice(0, 8)}</span>
                      <span className="client-id-text">{ticket.external_client_id}</span>
                    </div>
                  </td>
                  <td>
                    <span className="topic-tag">{ticket.topic}</span>
                  </td>
                  <td>
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
                            ? '#fbbf24'
                            : '#34d399',
                      }}
                    >
                      {formatWaitTime(ticket.wait_time_seconds)}
                    </span>
                  </td>
                  <td>{renderSlaBadge(ticket.sla_status)}</td>
                  <td style={{ textAlign: 'right' }}>
                    <button
                      className="btn btn-resolve-action"
                      onClick={() => onAnswerTicket(ticket)}
                      title="Открыть форму ответа и закрыть тикет"
                    >
                      Ответить
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}
