import liff from '@line/liff'

const LIFF_ID = import.meta.env.VITE_LIFF_ID || ''

let liffReady = false

export async function initLiff() {
  if (!LIFF_ID) {
    console.warn('VITE_LIFF_ID not set — running in dev mode')
    liffReady = true
    return
  }

  try {
    await liff.init({ liffId: LIFF_ID })
    liffReady = true

    if (!liff.isLoggedIn()) {
      liff.login()
    }
  } catch (err) {
    console.error('LIFF init failed:', err)
  }
}

export function getLiffProfile() {
  if (!liffReady || !LIFF_ID) return null
  return liff.getProfile()
}

export function closeLiff() {
  if (liffReady && LIFF_ID && liff.isInClient()) {
    liff.closeWindow()
  }
}

export function isInLiff() {
  return liffReady && LIFF_ID && liff.isInClient()
}
