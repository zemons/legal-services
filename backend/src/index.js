const express = require('express')
const cors = require('cors')
const path = require('path')

const chatRoutes = require('./routes/chat')
const intakeRoutes = require('./routes/intake')
const uploadRoutes = require('./routes/upload')
const documentRoutes = require('./routes/document')
const webhookRoutes = require('./routes/webhook')

const app = express()
const PORT = process.env.PORT || 4000

// LINE webhook needs raw body — mount before json parser
app.use('/webhook/line', webhookRoutes)

app.use(cors())
app.use(express.json())
app.use('/uploads', express.static(path.join(__dirname, '../uploads')))

app.use('/api/chat', chatRoutes)
app.use('/api/intake', intakeRoutes)
app.use('/api/upload', uploadRoutes)
app.use('/api/document', documentRoutes)

app.get('/health', (req, res) => {
  res.json({ status: 'ok', service: 'legal-backend' })
})

app.listen(PORT, () => {
  console.log(`Legal Backend API running on port ${PORT}`)
})
