const ADKCODE_URL = process.env.ADKCODE_URL || 'http://localhost:8080'

/**
 * Send a chat message to the AI agent and get a response.
 */
async function chat(message, sessionId = null, agentName = 'orchestrator') {
  const resp = await fetch(`${ADKCODE_URL}/api/chat`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      message,
      session_id: sessionId,
      agent: agentName,
    }),
  })
  return resp.json()
}

/**
 * Ask intake_analyst to analyze case data and produce a summary.
 */
async function analyzeIntake(intakeData) {
  const prompt = [
    'วิเคราะห์ข้อมูลคดีต่อไปนี้และสรุปประเด็นสำคัญ:',
    `ชื่อ: ${intakeData.name}`,
    `ประเภทคดี: ${intakeData.case_type}`,
    `รายละเอียด: ${intakeData.description}`,
    '',
    'กรุณา:',
    '1. สรุปประเด็นสำคัญ 2-3 บรรทัด',
    '2. ประเมินความเร่งด่วน (สูง/กลาง/ต่ำ)',
    '3. แนะนำแนวทางดำเนินการเบื้องต้น',
  ].join('\n')

  return chat(prompt, null, 'intake_analyst')
}

/**
 * Ask legal_advisor a legal question with RAG context.
 */
async function askLegalQuestion(question, sessionId = null) {
  return chat(question, sessionId, 'legal_advisor')
}

/**
 * Ask doc_drafter to draft a document.
 */
async function draftDocument(templateName, fields) {
  const fieldLines = Object.entries(fields)
    .map(([k, v]) => `- ${k}: ${v}`)
    .join('\n')

  const prompt = [
    `Draft เอกสาร: ${templateName}`,
    'ข้อมูลที่ได้รับ:',
    fieldLines,
    '',
    'กรุณา draft เอกสารให้สมบูรณ์ โดยเติมข้อมูลที่มีและระบุส่วนที่ยังขาด',
  ].join('\n')

  return chat(prompt, null, 'doc_drafter')
}

module.exports = {
  chat,
  analyzeIntake,
  askLegalQuestion,
  draftDocument,
}
