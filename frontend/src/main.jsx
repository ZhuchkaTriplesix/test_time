/**
 * Точка входа клиентского SPA-приложения React/Vite.
 *
 * Назначение:
 * - Монтирование корневого компонента App в DOM-дерево (#root).
 * - Подключение глобальных стилей оформления (index.css).
 */
import React from 'react'
import ReactDOM from 'react-dom/client'
import { App } from './App'
import './index.css'

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
)
