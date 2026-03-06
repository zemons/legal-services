const express = require('express')
const adkcode = require('../services/adkcode')

const router = express.Router()

// POST /api/chat — send message to AI agent
router.post('/', async (req, res) => {
  try {
    const { message, session_id, agent } = req.body

    if (!message) {
      return res.status(400).json({ error: 'message is required' })
    }

    const result = await adkcode.chat(message, session_id, agent)
    res.json(result)
  } catch (err) {
    console.error('Chat error:', err.message)
    res.status(500).json({ error: 'AI service unavailable' })
  }
})

module.exports = router
