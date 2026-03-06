const xmlrpc = require('xmlrpc')

const ODOO_URL = process.env.ODOO_URL || 'http://localhost:8069'
const ODOO_DB = process.env.ODOO_DB || 'legal'
const ODOO_USER = process.env.ODOO_USER || 'admin'
const ODOO_PASSWORD = process.env.ODOO_PASSWORD || 'admin'

// Parse URL for xmlrpc client
const url = new URL(ODOO_URL)
const clientOpts = {
  host: url.hostname,
  port: parseInt(url.port) || (url.protocol === 'https:' ? 443 : 80),
  path: '/xmlrpc/2/common',
}
const objectOpts = { ...clientOpts, path: '/xmlrpc/2/object' }

function createClient(opts) {
  if (url.protocol === 'https:') {
    return xmlrpc.createSecureClient(opts)
  }
  return xmlrpc.createClient(opts)
}

// Cache uid after first auth
let _uid = null

function authenticate() {
  return new Promise((resolve, reject) => {
    if (_uid) return resolve(_uid)
    const client = createClient(clientOpts)
    client.methodCall('authenticate', [ODOO_DB, ODOO_USER, ODOO_PASSWORD, {}], (err, uid) => {
      if (err) return reject(err)
      if (!uid) return reject(new Error('Odoo authentication failed'))
      _uid = uid
      resolve(uid)
    })
  })
}

function execute(model, method, args, kwargs = {}) {
  return new Promise(async (resolve, reject) => {
    try {
      const uid = await authenticate()
      const client = createClient(objectOpts)
      client.methodCall(
        'execute_kw',
        [ODOO_DB, uid, ODOO_PASSWORD, model, method, args, kwargs],
        (err, result) => {
          if (err) return reject(err)
          resolve(result)
        }
      )
    } catch (e) {
      reject(e)
    }
  })
}

// ---------------------------------------------------------------------------
// CRM Lead (Legal Case) operations
// ---------------------------------------------------------------------------

async function createLead(data) {
  const vals = {
    name: data.description ? data.description.substring(0, 80) : 'New Legal Case',
    contact_name: data.name || '',
    phone: data.phone || '',
    description: data.description || '',
    case_type: data.case_type || '',
    case_status: 'intake',
    type: 'opportunity',
  }

  // Link to existing partner by LINE user ID
  if (data.line_user_id) {
    vals.line_user_id = data.line_user_id
    const partners = await execute('res.partner', 'search_read', [
      [['line_user_id', '=', data.line_user_id]]
    ], { fields: ['id'], limit: 1 })
    if (partners.length > 0) {
      vals.partner_id = partners[0].id
    }
  }

  // AI summary from intake_analyst
  if (data.ai_summary) {
    vals.case_summary = data.ai_summary
  }

  const leadId = await execute('crm.lead', 'create', [vals])
  return { id: leadId, ...vals }
}

async function getLead(leadId) {
  const leads = await execute('crm.lead', 'read', [[leadId]], {
    fields: [
      'name', 'contact_name', 'phone', 'description',
      'case_type', 'case_status', 'case_summary',
      'court_id', 'statute_deadline', 'opposing_party',
      'partner_id', 'line_user_id',
    ]
  })
  return leads.length > 0 ? leads[0] : null
}

async function updateLeadStatus(leadId, status) {
  await execute('crm.lead', 'write', [[leadId], { case_status: status }])
  return { id: leadId, case_status: status }
}

async function searchLeads(filters = [], limit = 20) {
  return execute('crm.lead', 'search_read', [filters], {
    fields: ['id', 'name', 'case_type', 'case_status', 'contact_name', 'create_date'],
    limit,
    order: 'create_date desc',
  })
}

// ---------------------------------------------------------------------------
// Partner / LINE user mapping
// ---------------------------------------------------------------------------

async function findOrCreatePartner(lineUserId, displayName) {
  const existing = await execute('res.partner', 'search_read', [
    [['line_user_id', '=', lineUserId]]
  ], { fields: ['id', 'name'], limit: 1 })

  if (existing.length > 0) {
    return existing[0]
  }

  const id = await execute('res.partner', 'create', [{
    name: displayName || `LINE User ${lineUserId.substring(0, 8)}`,
    line_user_id: lineUserId,
  }])
  return { id, name: displayName }
}

// ---------------------------------------------------------------------------
// Court dates
// ---------------------------------------------------------------------------

async function getCourtDates(leadId) {
  return execute('legal.court.date', 'search_read', [
    [['lead_id', '=', leadId]]
  ], {
    fields: ['date_time', 'purpose', 'court_id', 'room', 'notes'],
    order: 'date_time asc',
  })
}

module.exports = {
  authenticate,
  execute,
  createLead,
  getLead,
  updateLeadStatus,
  searchLeads,
  findOrCreatePartner,
  getCourtDates,
}
