const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:4000'

export async function submitIntake(data) {
  const resp = await fetch(`${API_BASE}/api/intake`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  })
  return resp.json()
}

export async function uploadFile(caseId, file) {
  const formData = new FormData()
  formData.append('file', file)
  formData.append('case_id', caseId)

  const resp = await fetch(`${API_BASE}/api/upload`, {
    method: 'POST',
    body: formData,
  })
  return resp.json()
}

export async function getDocument(caseId) {
  const resp = await fetch(`${API_BASE}/api/document/${caseId}`)
  return resp.json()
}

export async function confirmDocument(caseId, action) {
  const resp = await fetch(`${API_BASE}/api/document/${caseId}/confirm`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ action }),
  })
  return resp.json()
}
