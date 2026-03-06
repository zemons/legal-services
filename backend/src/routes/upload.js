const express = require('express')
const multer = require('multer')
const path = require('path')
const fs = require('fs')

const router = express.Router()

const UPLOAD_DIR = process.env.UPLOAD_DIR || './uploads'

const storage = multer.diskStorage({
  destination: (req, file, cb) => {
    const caseId = req.body.case_id || 'unknown'
    const dir = path.join(UPLOAD_DIR, String(caseId))
    fs.mkdirSync(dir, { recursive: true })
    cb(null, dir)
  },
  filename: (req, file, cb) => {
    const timestamp = Date.now()
    const ext = path.extname(file.originalname)
    cb(null, `${timestamp}${ext}`)
  },
})

const upload = multer({
  storage,
  limits: { fileSize: 20 * 1024 * 1024 }, // 20MB
  fileFilter: (req, file, cb) => {
    const allowed = ['.pdf', '.jpg', '.jpeg', '.png', '.gif', '.doc', '.docx']
    const ext = path.extname(file.originalname).toLowerCase()
    if (allowed.includes(ext)) {
      cb(null, true)
    } else {
      cb(new Error(`File type ${ext} not allowed`))
    }
  },
})

// POST /api/upload — upload case documents
router.post('/', upload.array('file', 10), (req, res) => {
  if (!req.files || req.files.length === 0) {
    return res.status(400).json({ error: 'No files uploaded' })
  }

  const files = req.files.map(f => ({
    filename: f.filename,
    original: f.originalname,
    size: f.size,
    path: f.path,
  }))

  res.json({
    status: 'success',
    case_id: req.body.case_id,
    files_uploaded: files.length,
    files,
  })
})

module.exports = router
