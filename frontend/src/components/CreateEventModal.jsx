/**
 * Модальное окно симуляции входящих событий (Event Generator Modal).
 *
 * Назначение:
 * - Генерация тестовых входящих событий клиента через POST /api/events.
 * - Выбор пресетов доменных направлений.
 */
import React, { useState } from 'react'

const TOPIC_PRESETS = [
  {
    topic: 'Техническая поддержка',
    clientId: 'tg_user_8912',
    content: 'Ошибка авторизации через SSO в мобильном клиенте.',
  },
  {
    topic: 'Платежи и биллинг',
    clientId: 'crm_client_1042',
    content: 'Повторное списание абонентской платы за расчетный период.',
  },
  {
    topic: 'Общие вопросы',
    clientId: 'web_guest_303',
    content: 'Запрос регламента SLA и времени доступности технической поддержки.',
  },
]

export function CreateEventModal({ isOpen, onClose, onSubmit }) {
  const [clientId, setClientId] = useState('tg_user_8912')
  const [topic, setTopic] = useState('Техническая поддержка')
  const [content, setContent] = useState(
    'Ошибка авторизации через SSO в мобильном клиенте.'
  )
  const [isSubmitting, setIsSubmitting] = useState(false)

  if (!isOpen) return null

  const handleApplyPreset = (preset) => {
    setClientId(preset.clientId)
    setTopic(preset.topic)
    setContent(preset.content)
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    setIsSubmitting(true)

    const eventPayload = {
      external_event_id: `evt_client_${Date.now()}_${Math.random().toString(36).substring(2, 6)}`,
      event_type: 'client',
      external_client_id: clientId.trim(),
      topic: topic.trim(),
      content: content.trim(),
    }

    try {
      await onSubmit(eventPayload)
      onClose()
    } catch (err) {
      // Handled by parent
    } finally {
      setIsSubmitting(false)
    }
  }

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-content" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <div>
            <h3>Генерация входящего обращения</h3>
            <p className="modal-subtitle">Симуляция POST /api/events (event_type: client)</p>
          </div>
          <button className="modal-close-btn" onClick={onClose}>
            ✕
          </button>
        </div>

        {/* Preset chips */}
        <div className="canned-responses-section" style={{ marginBottom: '1rem' }}>
          <span className="canned-title">Пресеты направлений:</span>
          <div className="canned-chips-container">
            {TOPIC_PRESETS.map((p, idx) => (
              <button
                key={idx}
                type="button"
                className="canned-chip"
                onClick={() => handleApplyPreset(p)}
              >
                {p.topic}
              </button>
            ))}
          </div>
        </div>

        <form onSubmit={handleSubmit}>
          <div className="form-group">
            <label>Идентификатор клиента / канала:</label>
            <input
              type="text"
              className="form-control"
              value={clientId}
              onChange={(e) => setClientId(e.target.value)}
              placeholder="tg_user_8912"
              required
            />
          </div>

          <div className="form-group">
            <label>Направление (Topic):</label>
            <input
              type="text"
              className="form-control"
              value={topic}
              onChange={(e) => setTopic(e.target.value)}
              placeholder="Техническая поддержка"
              required
            />
          </div>

          <div className="form-group">
            <label>Содержание обращения:</label>
            <textarea
              className="form-control"
              rows={3}
              value={content}
              onChange={(e) => setContent(e.target.value)}
              placeholder="Текст вопроса клиента..."
              required
            ></textarea>
          </div>

          <div className="modal-footer">
            <button type="button" className="btn btn-secondary" onClick={onClose} disabled={isSubmitting}>
              Отмена
            </button>
            <button type="submit" className="btn btn-primary" disabled={isSubmitting}>
              {isSubmitting ? 'Отправка...' : 'Сгенерировать событие'}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}
