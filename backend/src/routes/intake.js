const express = require('express')
const odoo = require('../services/odoo')
const adkcode = require('../services/adkcode')
const line = require('../services/line')

const router = express.Router()

// POST /api/intake — submit new case intake from LIFF
router.post('/', async (req, res) => {
  try {
    const { name, phone, case_type, description, line_user_id } = req.body

    if (!name || !case_type || !description) {
      return res.status(400).json({ error: 'name, case_type, description are required' })
    }

    // 1. AI analyzes the intake
    let aiSummary = ''
    try {
      const analysis = await adkcode.analyzeIntake({ name, case_type, description })
      aiSummary = analysis.response || ''
    } catch (e) {
      console.error('AI analysis skipped:', e.message)
    }

    // 2. Create CRM Lead in Odoo
    const lead = await odoo.createLead({
      name,
      phone,
      case_type,
      description,
      line_user_id,
      ai_summary: aiSummary,
    })

    // 3. Notify client via LINE
    if (line_user_id) {
      try {
        await line.pushText(line_user_id,
          `รับเรื่องแล้วค่ะ\nหมายเลขเคส: ${lead.id}\nประเภท: ${case_type}\n\nทีมทนายจะติดต่อกลับภายใน 24 ชั่วโมง`
        )
      } catch (e) {
        console.error('LINE push failed:', e.message)
      }
    }

    res.json({
      status: 'success',
      case_id: lead.id,
      ai_summary: aiSummary,
    })
  } catch (err) {
    console.error('Intake error:', err.message)
    res.status(500).json({ error: 'Failed to create case' })
  }
})

module.exports = router
