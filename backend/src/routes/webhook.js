const express = require('express')
const crypto = require('crypto')
const line = require('../services/line')
const adkcode = require('../services/adkcode')
const odoo = require('../services/odoo')

const router = express.Router()

// LINE webhook needs raw body for signature verification
router.post('/', express.raw({ type: '*/*' }), async (req, res) => {
  const signature = req.headers['x-line-signature']
  const body = req.body.toString()

  if (!verifySignature(body, signature)) {
    return res.status(403).json({ error: 'Invalid signature' })
  }

  const data = JSON.parse(body)
  const events = data.events || []

  // Process events async — respond 200 immediately
  res.json({ status: 'ok' })

  for (const event of events) {
    try {
      await handleEvent(event)
    } catch (err) {
      console.error('Webhook event error:', err.message)
    }
  }
})

function verifySignature(body, signature) {
  const secret = line.config.channelSecret
  if (!secret) return false
  const hash = crypto.createHmac('sha256', secret).update(body).digest('base64')
  return crypto.timingSafeEqual(Buffer.from(hash), Buffer.from(signature || ''))
}

async function handleEvent(event) {
  const userId = event.source?.userId

  if (event.type === 'follow' && userId) {
    // New friend — create partner in Odoo
    try {
      const profile = await line.getProfile(userId)
      await odoo.findOrCreatePartner(userId, profile.displayName)
    } catch (e) {
      console.error('Follow event error:', e.message)
    }
    return
  }

  if (event.type === 'message' && event.message?.type === 'text') {
    const text = event.message.text
    const replyToken = event.replyToken

    // Route to AI agent
    const result = await adkcode.askLegalQuestion(text, userId)
    const reply = result.response || result.error || 'ขออภัย ไม่สามารถตอบได้ในขณะนี้'

    await line.replyText(replyToken, reply)
    return
  }
}

module.exports = router
