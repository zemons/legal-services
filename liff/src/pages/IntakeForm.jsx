import React, { useState, useEffect } from 'react'
import { submitIntake, uploadFile } from '../utils/api'
import { getLiffProfile, closeLiff } from '../utils/liff'

const CASE_TYPES = [
  { value: 'civil', label: 'แพ่ง (สัญญา, หนี้สิน, ละเมิด)' },
  { value: 'criminal', label: 'อาญา (ยักยอก, ฉ้อโกง, ทำร้าย)' },
  { value: 'family', label: 'ครอบครัว (หย่า, แบ่งทรัพย์, บุตร)' },
  { value: 'inheritance', label: 'มรดก (พินัยกรรม, แบ่งมรดก)' },
  { value: 'land', label: 'ที่ดิน (กรรมสิทธิ์, บุกรุก)' },
  { value: 'labor', label: 'แรงงาน (เลิกจ้าง, ค่าชดเชย)' },
  { value: 'construction', label: 'ก่อสร้าง (ผู้รับเหมาทิ้งงาน)' },
  { value: 'insurance', label: 'ประกันภัย (รถยนต์, อุบัติเหตุ)' },
  { value: 'document', label: 'งานเอกสาร (สัญญา, มอบอำนาจ)' },
  { value: 'consult', label: 'ที่ปรึกษา (จัดตั้งบริษัท, Due Diligence)' },
  { value: 'debt', label: 'บังคับคดี / ติดตามหนี้' },
  { value: 'other', label: 'อื่นๆ' },
]

export default function IntakeForm() {
  const [step, setStep] = useState(1)
  const [submitting, setSubmitting] = useState(false)
  const [result, setResult] = useState(null)
  const [lineProfile, setLineProfile] = useState(null)

  const [form, setForm] = useState({
    name: '',
    phone: '',
    case_type: '',
    description: '',
    line_user_id: '',
  })
  const [files, setFiles] = useState([])

  useEffect(() => {
    async function loadProfile() {
      try {
        const profile = await getLiffProfile()
        if (profile) {
          setLineProfile(profile)
          setForm(prev => ({
            ...prev,
            name: profile.displayName || '',
            line_user_id: profile.userId || '',
          }))
        }
      } catch (e) {
        // Not in LIFF — dev mode
      }
    }
    loadProfile()
  }, [])

  function handleChange(e) {
    setForm({ ...form, [e.target.name]: e.target.value })
  }

  function handleFileChange(e) {
    setFiles(Array.from(e.target.files))
  }

  async function handleSubmit(e) {
    e.preventDefault()
    setSubmitting(true)

    try {
      const res = await submitIntake(form)

      if (res.case_id && files.length > 0) {
        for (const file of files) {
          await uploadFile(res.case_id, file)
        }
      }

      setResult(res)
      setStep(3)
    } catch (err) {
      setResult({ error: err.message })
    } finally {
      setSubmitting(false)
    }
  }

  // Step 1: Basic info
  if (step === 1) {
    return (
      <div className="container">
        <h1>ปรึกษาทนายความ</h1>
        <p className="subtitle">กรอกข้อมูลเบื้องต้นเพื่อรับคำปรึกษา</p>

        <div className="form-group">
          <label>ชื่อ-นามสกุล</label>
          <input
            type="text"
            name="name"
            value={form.name}
            onChange={handleChange}
            placeholder="ชื่อจริง นามสกุล"
            required
          />
        </div>

        <div className="form-group">
          <label>เบอร์โทรศัพท์</label>
          <input
            type="tel"
            name="phone"
            value={form.phone}
            onChange={handleChange}
            placeholder="08x-xxx-xxxx"
            required
          />
        </div>

        <div className="form-group">
          <label>ประเภทคดี</label>
          <select name="case_type" value={form.case_type} onChange={handleChange} required>
            <option value="">-- เลือกประเภท --</option>
            {CASE_TYPES.map(t => (
              <option key={t.value} value={t.value}>{t.label}</option>
            ))}
          </select>
        </div>

        <button
          className="btn btn-primary"
          disabled={!form.name || !form.phone || !form.case_type}
          onClick={() => setStep(2)}
        >
          ถัดไป
        </button>
      </div>
    )
  }

  // Step 2: Description + file upload
  if (step === 2) {
    return (
      <div className="container">
        <h1>รายละเอียดคดี</h1>
        <p className="subtitle">อธิบายปัญหาของคุณ (ไม่ต้องเป็นทางการ)</p>

        <form onSubmit={handleSubmit}>
          <div className="form-group">
            <label>รายละเอียด</label>
            <textarea
              name="description"
              value={form.description}
              onChange={handleChange}
              rows={5}
              placeholder="เล่าปัญหาของคุณ เช่น ถูกเลิกจ้างไม่เป็นธรรม, ลูกหนี้ไม่ยอมจ่าย, ต้องการทำสัญญา..."
              required
            />
          </div>

          <div className="form-group">
            <label>แนบเอกสาร (ถ้ามี)</label>
            <input
              type="file"
              onChange={handleFileChange}
              multiple
              accept="image/*,.pdf"
              capture="environment"
            />
            <p className="hint">ถ่ายรูปเอกสาร หรือแนบไฟล์ PDF ได้</p>
          </div>

          {files.length > 0 && (
            <div className="file-list">
              {files.map((f, i) => (
                <div key={i} className="file-item">{f.name}</div>
              ))}
            </div>
          )}

          <div className="btn-group">
            <button type="button" className="btn btn-secondary" onClick={() => setStep(1)}>
              ย้อนกลับ
            </button>
            <button type="submit" className="btn btn-primary" disabled={submitting || !form.description}>
              {submitting ? 'กำลังส่ง...' : 'ส่งข้อมูล'}
            </button>
          </div>
        </form>
      </div>
    )
  }

  // Step 3: Success
  return (
    <div className="container">
      <div className="success-box">
        <div className="success-icon">&#10003;</div>
        <h1>รับเรื่องแล้ว</h1>
        {result?.case_id && (
          <p>หมายเลขเคส: <strong>{result.case_id}</strong></p>
        )}
        <p>ทีมทนายจะติดต่อกลับทาง LINE ภายใน 24 ชั่วโมง</p>
        <button className="btn btn-primary" onClick={closeLiff}>
          ปิด
        </button>
      </div>
    </div>
  )
}
