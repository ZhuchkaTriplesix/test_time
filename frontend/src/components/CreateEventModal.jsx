import React, { useState } from 'react'

export function CreateEventModal({ isOpen, onClose, onSubmit, initialTicket }) {
  const [eventType, setEventType] = useState(initialTicket ? 'agent' : 'client')
  const [clientId, setClientId] = useState(initialTicket ? initialTicket.external_client_id : 'tg_user_123')
  const [topic, setTopic] = useState(initialTicket ? initialTicket.topic : 'Техническая поддержка')
  const [content, setContent] = useState(
    initialTicket ? 'Здравствуйте! Ваш вопрос решен.' : 'Здравствуйте, у меня не работает оплата в приложении.'
  )
  const [isSubmitting, setIsSubmitting] = useState(false)

  if (!isOpen) return null

  const handleSubmit = async (e) => {
    e.preventDefault()
    setIsSubmitting(true)

    const eventPayload = {
      external_event_id: `evt_${eventType}_${Date.now()}_${Math.random().toString(36).substring(2, 6)}`,
      event_type: eventType,
      external_client_id: clientId,
      topic: topic,
      content: content,
      ticket_id: initialTicket?.id || null,
    }

    try {
      await onSubmit(eventPayload)
      onClose()
    } catch (err) {
      alert(`Ошибка при отправке события: ${err.message}`)
    } finally {
      setIsSubmitting(false)
    }
  }

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-content" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <h3>{initialTicket ? 'Ответ сотрудника на тикет' : 'Симуляция входящего события'}</h3>
          <button
            onClick={onClose}
            style={{ background: 'none', border: 'none', color: '#94a3b8', fontSize: '1.25rem', cursor: 'pointer' }}
          >
            ✕
          </button>
        </div>

        <form onSubmit={handleSubmit}>
          <div className="form-group">
            <label>Тип события:</label>
            <select
              className="form-control"
              value={eventType}
              onChange={(e) => setEventType(e.target.value)}
              disabled={!!initialTicket}
            >
              <option value="client">Клиентское сообщение (Новый тикет)</option>
              <option value="agent">Ответ сотрудника (Закрытие тикета)</option>
            </select>
          </div>

          <div className="form-group">
            <label>ID клиента / канала:</label>
            <input
              type="text"
              className="form-control"
              value={clientId}
              onChange={(e) => setClientId(e.target.value)}
              required
            />
          </div>

          {eventType === 'client' && (
            <div className="form-group">
              <label>Направление (Topic):</label>
              <input
                type="text"
                className="form-control"
                value={topic}
                onChange={(e) => setTopic(e.target.value)}
                required
              />
            </div>
          )}

          <div className="form-group">
            <label>Текст сообщения:</label>
            <textarea
              className="form-control"
              rows={3}
              value={content}
              onChange={(e) => setContent(e.target.value)}
              required
            ></textarea>
          </div>

          <div className="modal-footer">
            <button type="button" className="btn btn-secondary" onClick={onClose}>
              Отмена
            </button>
            <button type="submit" className="btn btn-primary" disabled={isSubmitting}>
              {isSubmitting ? 'Отправка...' : 'Отправить событие'}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}
