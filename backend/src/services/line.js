const { messagingApi } = require('@line/bot-sdk')

const config = {
  channelAccessToken: process.env.LINE_CHANNEL_ACCESS_TOKEN || '',
  channelSecret: process.env.LINE_CHANNEL_SECRET || '',
}

let _client = null

function getClient() {
  if (!_client) {
    _client = new messagingApi.MessagingApiClient({
      channelAccessToken: config.channelAccessToken,
    })
  }
  return _client
}

async function replyText(replyToken, text) {
  const client = getClient()
  return client.replyMessage({
    replyToken,
    messages: [{ type: 'text', text }],
  })
}

async function pushText(userId, text) {
  const client = getClient()
  return client.pushMessage({
    to: userId,
    messages: [{ type: 'text', text }],
  })
}

async function pushQuickReply(userId, text, actions) {
  const client = getClient()
  return client.pushMessage({
    to: userId,
    messages: [{
      type: 'text',
      text,
      quickReply: {
        items: actions.map(a => ({
          type: 'action',
          action: { type: 'message', label: a.label, text: a.text },
        })),
      },
    }],
  })
}

async function getProfile(userId) {
  const client = getClient()
  return client.getProfile(userId)
}

module.exports = {
  config,
  getClient,
  replyText,
  pushText,
  pushQuickReply,
  getProfile,
}
