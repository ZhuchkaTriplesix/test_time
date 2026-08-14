/**
 * Панель инструментов фильтрации и синхронизации данных (Filter & Sync Toolbar).
 *
 * Назначение:
 * - Строгая фильтрация таблицы обращений по доменному направлению (Topic).
 * - Индикация статуса фоновой синхронизации (Polling 10s) и времени последнего обновления.
 */
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
        <span className="filter-label">Направление:</span>
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

      <div className="controls-actions">
        <div className="sync-status-indicator">
          <span className={`status-dot ${isAutoRefresh ? 'dot-active' : 'dot-paused'}`}></span>
          <span className="sync-text">
            {isAutoRefresh ? 'Auto-sync: 10s' : 'Sync: Paused'}
            {lastUpdated ? ` • ${lastUpdated.toLocaleTimeString()}` : ''}
          </span>
        </div>

        <button
          className="btn btn-secondary btn-sm"
          onClick={onToggleAutoRefresh}
          title={isAutoRefresh ? 'Приостановить автообновление' : 'Включить автообновление'}
        >
          {isAutoRefresh ? 'Pause' : 'Resume'}
        </button>

        <button
          className="btn btn-secondary btn-sm"
          onClick={onManualRefresh}
          disabled={isLoading}
        >
          {isLoading ? 'Syncing...' : 'Refresh'}
        </button>
      </div>
    </div>
  )
}
