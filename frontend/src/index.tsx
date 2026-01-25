/**
 * React entry point for Purisa frontend
 */
import { createRoot } from 'react-dom/client'
import { ThemeProvider } from './contexts/ThemeContext'
import App from './App'
import './output.css'

const container = document.getElementById('root')
if (!container) {
  throw new Error('Root element not found')
}

const root = createRoot(container)
root.render(
  <ThemeProvider>
    <App />
  </ThemeProvider>
)
