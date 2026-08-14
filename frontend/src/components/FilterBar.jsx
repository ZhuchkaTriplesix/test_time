import React from 'react'

export function FilterBar({
  selectedTopic,
  onTopicChange,
  topics,
  isAutoRefresh,
  onToggleAutoRefresh,
  onManualRefresh,
  isLoading,
  lastUpdated,
}) {
  return (
    <div className="controls-bar">
      <div className="filter-group">
        <label htmlFor="topic-select">Направление:</label>
        <select
          id="topic-select"
          className="select-input"
          value={selectedTopic}
          onChange={(e) => onTopicChange(e.target.value)}
        >
          <option value="">Все направления ({topics?.length || 0})</option>
          {topics?.map((topic) => (
            <option key={topic} value={topic}>
              {topic}
            </option>
          ))}
        </select>
      </div>

      <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
        <div className="refresh-indicator">
          {isAutoRefresh && <span className="pulse-dot"></span>}
          <span>
            {isAutoRefresh ? 'Автообновление (10с)' : 'Пауза'}
            {lastUpdated ? ` • ${lastUpdated.toLocaleTimeString()}` : ''}
          </span>
        </div>

        <button
          className="btn btn-secondary"
          onClick={onToggleAutoRefresh}
          title="Включить/выключить периодический опрос"
        >
          {isAutoRefresh ? '⏸ Пауза' : '▶ Авто'}
        </button>

        <button
          className="btn btn-secondary"
          onClick={onManualRefresh}
          disabled={isLoading}
        >
          🔄 Обновить
        </button>
      </div>
    </div>
  )
}
