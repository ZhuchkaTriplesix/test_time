/**
 * Модальное окно симуляции входящих клиентских обращений (POST /api/events).
 *
 * Назначение:
 * - Генерация новых тестовых обращений от клиентов с выбором темы и текста.
 * - Быстрые пресеты обращений для удобства тестирования и демонстрации работы SLA.
 */
import React, { useState } from 'react'

const TOPIC_PRESETS = [
  {
    topic: 'Техническая поддержка',
    clientId: 'tg_user_ivan_45',
    content: 'Не могу войти в личный кабинет через мобильное приложение, пишет ошибку сети.',
  },
  {
    topic: 'Платежи и биллинг',
    clientId: 'crm_client_elena_88',
    content: 'Списались деньги за подписку Premium дважды за август. Пожалуйста, оформите возврат.',
  },
  {
    topic: 'Общие вопросы',
    clientId: 'tg_alex_99',
    content: 'Подскажите график работы службы поддержки в праздничные дни.',
  },
]

export function CreateEventModal({ isOpen, onClose, onSubmit }) {
  const [clientId, setClientId] = useState('tg_user_ivan_45')
  const [topic, setTopic] = useState('Техническая поддержка')
  const [content, setContent] = useState(
    'Не могу войти в личный кабинет через мобильное приложение, пишет ошибку сети.'
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
            <h3>📥 Создание нового обращения клиента</h3>
            <p className="modal-subtitle">Симуляция входящего события через POST /api/events</p>
          </div>
          <button className="modal-close-btn" onClick={onClose}>
            ✕
          </button>
        </div>

        {/* Preset chips */}
        <div className="canned-responses-section" style={{ marginBottom: '1rem' }}>
          <label className="canned-title">Быстрые примеры обращений:</label>
          <div className="canned-chips-container">
            {TOPIC_PRESETS.map((p, idx) => (
              <button
                key={idx}
                type="button"
                className="canned-chip"
                onClick={() => handleApplyPreset(p)}
              >
                📌 {p.topic}
              </button>
            ))}
          </div>
        </div>

        <form onSubmit={handleSubmit}>
          <div className="form-group">
            <label>ID клиента / канала:</label>
            <input
              type="text"
              className="form-control"
              value={clientId}
              onChange={(e) => setClientId(e.target.value)}
              placeholder="Например: tg_user_8912"
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
              placeholder="Например: Техническая поддержка"
              required
            />
          </div>

          <div className="form-group">
            <label>Текст сообщения клиента:</label>
            <textarea
              className="form-control"
              rows={3}
              value={content}
              onChange={(e) => setContent(e.target.value)}
              placeholder="Опишите вопрос клиента..."
              required
            ></textarea>
          </div>

          <div className="modal-footer">
            <button type="button" className="btn btn-secondary" onClick={onClose} disabled={isSubmitting}>
              Отмена
            </button>
            <button type="submit" className="btn btn-primary" disabled={isSubmitting}>
              {isSubmitting ? 'Отправка...' : '+ Создать обращение'}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}
