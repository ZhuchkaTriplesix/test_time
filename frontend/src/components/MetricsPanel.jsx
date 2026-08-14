/**
 * Компонент панели ключевых показателей эффективности (KPI Metrics Bar).
 *
 * Назначение:
 * - Вывод операционных счетчиков: объем входящих, закрытые тикеты, нарушения SLA.
 * - Вывод медианного времени первой реакции (Percentile 50 / TTFR) из СУБД.
 */
import React from 'react'

export function MetricsPanel({ metrics }) {
  const medianFormatted =
    metrics?.median_first_response_time_seconds !== null &&
    metrics?.median_first_response_time_seconds !== undefined
      ? `${Number(metrics.median_first_response_time_seconds).toFixed(1)}s`
      : 'N/A'

  const totalCreated = metrics?.total_created ?? 0
  const totalAnswered = metrics?.total_answered ?? 0
  const totalOverdue = metrics?.total_overdue ?? 0

  const answeredRate = totalCreated > 0 ? Math.round((totalAnswered / totalCreated) * 100) : 0
  const breachRate = totalCreated > 0 ? Math.round((totalOverdue / totalCreated) * 100) : 0

  return (
    <div className="metrics-grid">
      <div className="metric-card">
        <div className="metric-header">
          <span className="metric-label">Всего обращений</span>
          <span className="metric-badge-neutral">INFLOW</span>
        </div>
        <div className="metric-value-row">
          <span className="metric-value-num">{totalCreated}</span>
        </div>
        <div className="metric-footer">
          <span className="metric-footer-text">Входящий поток событий</span>
        </div>
      </div>

      <div className="metric-card">
        <div className="metric-header">
          <span className="metric-label">Закрыто операторами</span>
          <span className="metric-badge-success">{answeredRate}%</span>
        </div>
        <div className="metric-value-row">
          <span className="metric-value-num text-success">{totalAnswered}</span>
        </div>
        <div className="metric-footer">
          <span className="metric-footer-text">Первичный ответ зафиксирован</span>
        </div>
      </div>

      <div className="metric-card">
        <div className="metric-header">
          <span className="metric-label">Нарушения SLA (&gt;180с)</span>
          <span className={`metric-badge-${totalOverdue > 0 ? 'danger' : 'neutral'}`}>
            {breachRate}%
          </span>
        </div>
        <div className="metric-value-row">
          <span className={`metric-value-num ${totalOverdue > 0 ? 'text-danger' : 'text-muted'}`}>
            {totalOverdue}
          </span>
        </div>
        <div className="metric-footer">
          <span className="metric-footer-text">Критические просрочки (Overdue)</span>
        </div>
      </div>

      <div className="metric-card">
        <div className="metric-header">
          <span className="metric-label">Медиана ответа (TTFR)</span>
          <span className="metric-badge-accent">P50</span>
        </div>
        <div className="metric-value-row">
          <span className="metric-value-num text-accent">{medianFormatted}</span>
        </div>
        <div className="metric-footer">
          <span className="metric-footer-text">PostgreSQL percentile_cont(0.5)</span>
        </div>
      </div>
    </div>
  )
}
