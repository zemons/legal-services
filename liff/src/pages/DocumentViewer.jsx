import React, { useState, useEffect } from 'react'
import { useParams } from 'react-router-dom'
import { getDocument, confirmDocument } from '../utils/api'
import { closeLiff } from '../utils/liff'

export default function DocumentViewer() {
  const { caseId } = useParams()
  const [doc, setDoc] = useState(null)
  const [loading, setLoading] = useState(true)
  const [confirming, setConfirming] = useState(false)
  const [confirmed, setConfirmed] = useState(false)
  const [error, setError] = useState(null)

  useEffect(() => {
    async function load() {
      try {
        const data = await getDocument(caseId)
        if (data.error) {
          setError(data.error)
        } else {
          setDoc(data)
        }
      } catch (e) {
        setError('ไม่สามารถโหลดเอกสารได้')
      } finally {
        setLoading(false)
      }
    }
    load()
  }, [caseId])

  async function handleAction(action) {
    setConfirming(true)
    try {
      await confirmDocument(caseId, action)
      setConfirmed(true)
    } catch (e) {
      setError('เกิดข้อผิดพลาด กรุณาลองใหม่')
    } finally {
      setConfirming(false)
    }
  }

  if (loading) {
    return (
      <div className="container">
        <div className="loading">กำลังโหลดเอกสาร...</div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="container">
        <div className="error-box">{error}</div>
      </div>
    )
  }

  if (confirmed) {
    return (
      <div className="container">
        <div className="success-box">
          <div className="success-icon">&#10003;</div>
          <h1>บันทึกแล้ว</h1>
          <p>ทีมทนายจะดำเนินการต่อให้</p>
          <button className="btn btn-primary" onClick={closeLiff}>ปิด</button>
        </div>
      </div>
    )
  }

  return (
    <div className="container">
      <h1>เอกสาร Draft</h1>

      {doc?.name && (
        <h2 className="doc-title">{doc.name}</h2>
      )}

      <div className="doc-meta">
        <span>เคส: {caseId}</span>
        {doc?.type && <span>ประเภท: {doc.type}</span>}
        {doc?.created_at && <span>สร้างเมื่อ: {doc.created_at}</span>}
      </div>

      <div className="doc-content">
        <pre>{doc?.content || 'ไม่มีเนื้อหา'}</pre>
      </div>

      <div className="doc-warning">
        &#9888; เอกสารนี้เป็น draft เบื้องต้น ต้องให้ทนายตรวจสอบก่อนใช้งาน
      </div>

      {doc?.pdf_url && (
        <a href={doc.pdf_url} className="btn btn-secondary" download>
          ดาวน์โหลด PDF
        </a>
      )}

      <div className="btn-group">
        <button
          className="btn btn-success"
          disabled={confirming}
          onClick={() => handleAction('approve')}
        >
          {confirming ? '...' : 'ยืนยัน'}
        </button>
        <button
          className="btn btn-warning"
          disabled={confirming}
          onClick={() => handleAction('revise')}
        >
          {confirming ? '...' : 'ขอแก้ไข'}
        </button>
      </div>
    </div>
  )
}
