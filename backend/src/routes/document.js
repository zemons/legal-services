const express = require('express')
const odoo = require('../services/odoo')
const line = require('../services/line')

const router = express.Router()

// GET /api/document/:caseId — get draft document for a case
router.get('/:caseId', async (req, res) => {
  try {
    const caseId = parseInt(req.params.caseId)
    if (!caseId) {
      return res.status(400).json({ error: 'Invalid case ID' })
    }

    const lead = await odoo.getLead(caseId)
    if (!lead) {
      return res.status(404).json({ error: 'Case not found' })
    }

    // Return case info + draft content
    res.json({
      case_id: caseId,
      name: lead.name,
      type: lead.case_type,
      status: lead.case_status,
      content: lead.case_summary || 'ยังไม่มี draft เอกสาร',
      created_at: lead.create_date,
    })
  } catch (err) {
    console.error('Document fetch error:', err.message)
    res.status(500).json({ error: 'Failed to fetch document' })
  }
})

// POST /api/document/:caseId/confirm — client approves or requests revision
router.post('/:caseId/confirm', async (req, res) => {
  try {
    const caseId = parseInt(req.params.caseId)
    const { action } = req.body // 'approve' or 'revise'

    if (!caseId || !action) {
      return res.status(400).json({ error: 'case_id and action required' })
    }

    const lead = await odoo.getLead(caseId)
    if (!lead) {
      return res.status(404).json({ error: 'Case not found' })
    }

    if (action === 'approve') {
      await odoo.updateLeadStatus(caseId, 'in_progress')
    }

    // Notify lawyer via LINE if linked
    // (lawyer notification would go through Odoo line_integration module)

    res.json({
      status: 'success',
      case_id: caseId,
      action,
    })
  } catch (err) {
    console.error('Document confirm error:', err.message)
    res.status(500).json({ error: 'Failed to process confirmation' })
  }
})

module.exports = router
