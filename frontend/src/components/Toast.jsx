/**
 * Компонент системных Toast-уведомлений.
 *
 * Назначение:
 * - Вывод неблокирующих подтверждений операций и ошибок.
 */
import React, { useEffect } from 'react'

export function Toast({ toast, onClose }) {
  useEffect(() => {
    if (!toast) return
    const timer = setTimeout(() => {
      onClose()
    }, 4000)
    return () => clearTimeout(timer)
  }, [toast, onClose])

  if (!toast) return null

  const isError = toast.type === 'error'

  return (
    <div className={`toast-container ${isError ? 'toast-error' : 'toast-success'}`}>
      <div className="toast-body">
        <div className="toast-title">{toast.title}</div>
        {toast.message && <div className="toast-message">{toast.message}</div>}
      </div>
      <button className="toast-close" onClick={onClose}>
        ✕
      </button>
    </div>
  )
}
