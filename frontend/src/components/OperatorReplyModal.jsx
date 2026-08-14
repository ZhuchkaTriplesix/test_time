/**
 * Модальное окно ответа оператора (Service Desk Resolution Window).
 *
 * Назначение:
 * - Контекст тикета: идентификатор, источник, текст вопроса, таймер ожидания.
 * - Быстрые деловые шаблоны ответов.
 * - Поддержка шортката Ctrl+Enter / Cmd+Enter для моментального закрытия обращения.
 */
import React, { useState, useEffect, useRef } from 'react'

const CANNED_RESPONSES = [
  {
    label: 'Запрос решен',
    text: 'Здравствуйте! Ваш запрос обработан, проблема успешно устранена.',
  },
  {
    label: 'Зачисление платежа',
    text: 'Здравствуйте! Платеж идентифицирован и успешно зачислен на ваш баланс.',
  },
  {
    label: 'Эскалация в L2',
    text: 'Здравствуйте! Обращение передано профильным инженерам. Ожидайте обновления статуса.',
  },
  {
    label: 'Уточнение деталей',
    text: 'Здравствуйте! Уточните, пожалуйста, точное время возникновения ошибки и номер операции.',
  },
]

export function OperatorReplyModal({ isOpen, onClose, ticket, onSubmit }) {
  const [replyText, setReplyText] = useState('')
  const [isSubmitting, setIsSubmitting] = useState(false)
  const textareaRef = useRef(null)

  useEffect(() => {
    if (isOpen) {
      setReplyText(CANNED_RESPONSES[0].text)
      setTimeout(() => {
        if (textareaRef.current) {
          textareaRef.current.focus()
          textareaRef.current.select()
        }
      }, 50)
    }
  }, [isOpen, ticket])

  if (!isOpen || !ticket) return null

  const handleSelectTemplate = (templateText) => {
    setReplyText(templateText)
    if (textareaRef.current) {
      textareaRef.current.focus()
    }
  }

  const handleSend = async () => {
    if (!replyText.trim()) return
    setIsSubmitting(true)

    const payload = {
      external_event_id: `evt_agent_${Date.now()}_${Math.random().toString(36).substring(2, 6)}`,
      event_type: 'agent',
      ticket_id: ticket.id,
      content: replyText.trim(),
      payload: {
        agent_id: 'ops_agent_primary',
      },
    }

    try {
      await onSubmit(payload, ticket)
      onClose()
    } catch (err) {
      // Handled by parent
    } finally {
      setIsSubmitting(false)
    }
  }

  const handleKeyDown = (e) => {
    if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
      e.preventDefault()
      handleSend()
    }
  }

  const formatWaitTime = (seconds) => {
    if (seconds < 60) return `${Math.floor(seconds)}s`
    const m = Math.floor(seconds / 60)
    const s = Math.floor(seconds % 60)
    return `${m}m ${s}s`
  }

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-content operator-reply-modal" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <div>
            <h3>Ответ на обращение #{ticket.id.slice(0, 8)}</h3>
            <p className="modal-subtitle">
              Фиксация первого ответа оператора и закрытие тикета в базе данных
            </p>
          </div>
          <button className="modal-close-btn" onClick={onClose}>
            ✕
          </button>
        </div>

        {/* Client context card */}
        <div className="client-context-card">
          <div className="client-context-header">
            <div className="client-info">
              <span className="client-id-strong">{ticket.external_client_id}</span>
              <span className="topic-tag-pill">{ticket.topic}</span>
            </div>
            <div className="client-sla-info">
              <span
                className={`sla-status-pill ${
                  ticket.sla_status === 'overdue'
                    ? 'pill-overdue'
                    : ticket.sla_status === 'warning'
                    ? 'pill-warning'
                    : 'pill-normal'
                }`}
              >
                {ticket.sla_status.toUpperCase()}
              </span>
              <span className="wait-time-badge">
                Время ожидания: <strong>{formatWaitTime(ticket.wait_time_seconds)}</strong>
              </span>
            </div>
          </div>

          <div className="client-message-bubble">
            <div className="bubble-label">Текст обращения клиента:</div>
            <div className="bubble-text">{ticket.content}</div>
          </div>
        </div>

        {/* Quick Canned Responses */}
        <div className="canned-responses-section">
          <span className="canned-title">Шаблоны быстрых ответов:</span>
          <div className="canned-chips-container">
            {CANNED_RESPONSES.map((item, idx) => (
              <button
                key={idx}
                type="button"
                className="canned-chip"
                onClick={() => handleSelectTemplate(item.text)}
              >
                {item.label}
              </button>
            ))}
          </div>
        </div>

        {/* Reply text input */}
        <div className="reply-input-section">
          <label htmlFor="reply-textarea">Текст ответа:</label>
          <textarea
            id="reply-textarea"
            ref={textareaRef}
            className="form-control reply-textarea"
            rows={4}
            value={replyText}
            onChange={(e) => setReplyText(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Введите ответ клиенту..."
            required
          />
          <div className="reply-hint">
            <span>Используйте <strong>Ctrl + Enter</strong> (или <strong>⌘ + Enter</strong>) для быстрой отправки</span>
            <span className="char-count">{replyText.length} симв.</span>
          </div>
        </div>

        <div className="modal-footer">
          <button type="button" className="btn btn-secondary" onClick={onClose} disabled={isSubmitting}>
            Отмена
          </button>
          <button
            type="button"
            className="btn btn-primary"
            onClick={handleSend}
            disabled={isSubmitting || !replyText.trim()}
          >
            {isSubmitting ? 'Отправка...' : 'Отправить и закрыть тикет'}
          </button>
        </div>
      </div>
    </div>
  )
}
