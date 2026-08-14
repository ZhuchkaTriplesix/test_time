/**
 * Модальное окно ответа оператора на обращение клиента (UX Response Interface).
 *
 * Назначение:
 * - Отображение полного контекста обращения клиента (имя, канал, текст, время ожидания, статус SLA).
 * - Предоставление быстрых готовых шаблонов ответов (Canned Responses) в один клик.
 * - Удобный ввод текста с поддержкой горячих клавиш Ctrl+Enter / Cmd+Enter для мгновенной отправки.
 */
import React, { useState, useEffect, useRef } from 'react'

const CANNED_RESPONSES = [
  {
    label: '✨ Вопрос решен',
    text: 'Здравствуйте! Ваш вопрос успешно решен, пожалуйста, проверьте доступ.',
  },
  {
    label: '💳 Оплата зачислена',
    text: 'Здравствуйте! Платеж успешно найден и зачислен на ваш баланс. Приносим извинения за ожидание.',
  },
  {
    label: '🛠 Передано разработчикам',
    text: 'Здравствуйте! Передали информацию в технический отдел, исправление будет выпущено в ближайшее время.',
  },
  {
    label: '❓ Запрос деталей',
    text: 'Здравствуйте! Подскажите, пожалуйста, модель вашего устройства и версию приложения?',
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
        agent_name: 'Оператор поддержки',
      },
    }

    try {
      await onSubmit(payload, ticket)
      onClose()
    } catch (err) {
      // Error handled by parent
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
    if (seconds < 60) return `${Math.floor(seconds)} сек`
    const m = Math.floor(seconds / 60)
    const s = Math.floor(seconds % 60)
    return `${m}м ${s}с`
  }

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-content operator-reply-modal" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <div className="operator-modal-title">
            <span className="operator-title-icon">💬</span>
            <div>
              <h3>Ответ на обращение #{ticket.id.slice(0, 8)}</h3>
              <p className="modal-subtitle">Отправка ответа клиенту и фиксация времени первой реакции</p>
            </div>
          </div>
          <button className="modal-close-btn" onClick={onClose}>
            ✕
          </button>
        </div>

        {/* Client context card */}
        <div className="client-context-card">
          <div className="client-context-header">
            <div className="client-info">
              <span className="client-avatar">👤</span>
              <div>
                <strong>{ticket.external_client_id}</strong>
                <span className="topic-tag-pill">{ticket.topic}</span>
              </div>
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
                {ticket.sla_status === 'overdue' ? '🚨 Overdue' : ticket.sla_status === 'warning' ? '⚠️ Warning' : '🟢 Normal'}
              </span>
              <span className="wait-time-badge">⏱ ждет {formatWaitTime(ticket.wait_time_seconds)}</span>
            </div>
          </div>

          <div className="client-message-bubble">
            <div className="bubble-label">Сообщение клиента:</div>
            <div className="bubble-text">{ticket.content}</div>
          </div>
        </div>

        {/* Quick Canned Responses */}
        <div className="canned-responses-section">
          <label className="canned-title">Быстрые шаблоны ответов (клик для вставки):</label>
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
          <label htmlFor="reply-textarea">Текст вашего ответа:</label>
          <textarea
            id="reply-textarea"
            ref={textareaRef}
            className="form-control reply-textarea"
            rows={4}
            value={replyText}
            onChange={(e) => setReplyText(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Введите текст ответа клиенту..."
            required
          />
          <div className="reply-hint">
            <span>💡 Подсказка: нажмите <strong>Ctrl + Enter</strong> (или <strong>Cmd + Enter</strong>) для быстрой отправки</span>
            <span className="char-count">{replyText.length} симв.</span>
          </div>
        </div>

        <div className="modal-footer">
          <button type="button" className="btn btn-secondary" onClick={onClose} disabled={isSubmitting}>
            Отмена
          </button>
          <button
            type="button"
            className="btn btn-primary btn-submit-reply"
            onClick={handleSend}
            disabled={isSubmitting || !replyText.trim()}
          >
            {isSubmitting ? 'Отправка...' : '✉️ Отправить ответ и закрыть тикет'}
          </button>
        </div>
      </div>
    </div>
  )
}
