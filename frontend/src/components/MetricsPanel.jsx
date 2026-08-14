/**
 * Компонент верхней панели ключевых метрик (KPI).
 *
 * Назначение:
 * - Отображение счетчиков: Всего создано, Отвечено сотрудниками, Просрочено.
 * - Отображение непрерывной медианы первого ответа, рассчитанной в PostgreSQL.
 */
import React from 'react'

export function MetricsPanel({ metrics }) {
  const medianFormatted =
    metrics?.median_first_response_time_seconds !== null &&
    metrics?.median_first_response_time_seconds !== undefined
      ? `${metrics.median_first_response_time_seconds} сек`
      : '—'

  return (
    <div className="metrics-grid">
      <div className="metric-card">
        <div className="metric-header">
          <span className="metric-label">Всего создано</span>
          <span className="metric-icon">📥</span>
        </div>
        <div className="metric-value">{metrics?.total_created ?? 0}</div>
        <div className="metric-sub">Все входящие обращения</div>
      </div>

      <div className="metric-card">
        <div className="metric-header">
          <span className="metric-label">Отвечено сотрудниками</span>
          <span className="metric-icon">✅</span>
        </div>
        <div className="metric-value">{metrics?.total_answered ?? 0}</div>
        <div className="metric-sub">Успешно закрытые тикеты</div>
      </div>

      <div className="metric-card">
        <div className="metric-header">
          <span className="metric-label">Просрочено (Overdue)</span>
          <span className="metric-icon">🚨</span>
        </div>
        <div className="metric-value" style={{ color: '#f87171' }}>
          {metrics?.total_overdue ?? 0}
        </div>
        <div className="metric-sub">Нарушение SLA (&gt; 180 сек)</div>
      </div>

      <div className="metric-card">
        <div className="metric-header">
          <span className="metric-label">Медианное время ответа</span>
          <span className="metric-icon">⏱️</span>
        </div>
        <div className="metric-value" style={{ color: '#38bdf8' }}>
          {medianFormatted}
        </div>
        <div className="metric-sub">PostgreSQL percentile_cont(0.5)</div>
      </div>
    </div>
  )
}
