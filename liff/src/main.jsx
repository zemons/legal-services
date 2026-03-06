import React from 'react'
import ReactDOM from 'react-dom/client'
import { BrowserRouter, Routes, Route } from 'react-router-dom'
import { initLiff } from './utils/liff'
import IntakeForm from './pages/IntakeForm'
import DocumentViewer from './pages/DocumentViewer'
import './styles.css'

initLiff()

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<IntakeForm />} />
        <Route path="/intake" element={<IntakeForm />} />
        <Route path="/document/:caseId" element={<DocumentViewer />} />
      </Routes>
    </BrowserRouter>
  </React.StrictMode>
)
