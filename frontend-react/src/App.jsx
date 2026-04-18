import { useState, useRef, useEffect } from 'react'
import ReactMarkdown from 'react-markdown'

const API_URL = 'http://localhost:8000'

function App() {
  const [messages, setMessages] = useState([])
  const [input, setInput] = useState('')
  const [isStreaming, setIsStreaming] = useState(false)
  const [retryCount, setRetryCount] = useState(0)
  const [showRetry, setShowRetry] = useState(false)
  const messagesEndRef = useRef(null)

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  const getRetryDelay = () => {
    return Math.min(1000 * Math.pow(2, retryCount), 30000)
  }

  const handleRetry = async () => {
    if (messages.length === 0) return
    
    const lastUserMessage = messages.filter(m => m.role === 'user').pop()
    if (!lastUserMessage) return

    setShowRetry(false)
    setRetryCount(prev => prev + 1)
    
    const delay = getRetryDelay()
    await new Promise(r => setTimeout(r, delay))
    
    await sendMessage(lastUserMessage.content)
  }

  const sendMessage = async (messageText) => {
    const userMessage = messageText || input.trim()
    if (!userMessage || isStreaming) return

    if (!messageText) {
      setInput('')
      setMessages(prev => [...prev, { role: 'user', content: userMessage }])
    }
    
    setShowRetry(false)

    // Show thinking bubble BEFORE API call
    setMessages(prev => [...prev, { role: 'assistant', content: '', isTyping: true }])
    
    setIsStreaming(true)

    try {
      const response = await fetch(`${API_URL}/api/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: userMessage })
      })

      if (!response.ok) {
        throw new Error(`API error: ${response.status}`)
      }

      const reader = response.body.getReader()
      const decoder = new TextDecoder()
      let fullResponse = ''
      let hasError = false
      let errorMessage = ''

      while (true) {
        const { done, value } = await reader.read()
        if (done) break

        const chunk = decoder.decode(value)
        const lines = chunk.split('\n')

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            try {
              const data = JSON.parse(line.substring(6))
              
              // Handle error tokens
              if (data.error) {
                hasError = true
                errorMessage = data.error
                fullResponse += data.error
                setMessages(prev => {
                  const newMessages = [...prev]
                  const lastMsg = newMessages[newMessages.length - 1]
                  if (lastMsg && lastMsg.role === 'assistant') {
                    lastMsg.content = fullResponse
                    lastMsg.isError = true
                  }
                  return newMessages
                })
              }
              // Handle normal tokens
              else if (data.token && data.token.trim()) {
                fullResponse += data.token
                setMessages(prev => {
                  const newMessages = [...prev]
                  const lastMsg = newMessages[newMessages.length - 1]
                  if (lastMsg && lastMsg.role === 'assistant') {
                    lastMsg.content = fullResponse
                  }
                  return newMessages
                })
              }
            } catch (err) {
              // Skip invalid JSON
            }
          }
        }
      }

      // Show retry button if there was an error
      if (hasError) {
        setShowRetry(true)
        setRetryCount(0) // Reset retry count on error
      }

    } catch (error) {
      setMessages(prev => [
        ...prev,
        { role: 'assistant', content: `Connection error: ${error.message}`, isError: true }
      ])
      setShowRetry(true)
      setRetryCount(0)
    } finally {
      setMessages(prev => {
        const newMessages = [...prev]
        const lastMsg = newMessages[newMessages.length - 1]
        if (lastMsg && lastMsg.role === 'assistant') {
          lastMsg.isTyping = false
        }
        return newMessages
      })
      setIsStreaming(false)
    }
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    setRetryCount(0)
    await sendMessage(null)
  }

  const handleClear = async () => {
    try {
      await fetch(`${API_URL}/api/reset`, { method: 'POST' })
    } catch (e) {
      console.error('Failed to clear:', e)
    }
    setMessages([])
    setShowRetry(false)
    setRetryCount(0)
  }

  return (
    <div className="app">
      <div className="header">
        <h1>💬 LLM Chat</h1>
      </div>

      <div className="chat-container">
        {messages.length === 0 && (
          <p style={{ textAlign: 'center', color: '#666', marginTop: '20px' }}>
            Send a message to start chatting!
          </p>
        )}

        {messages.map((msg, idx) => (
          <div key={idx} className={`message ${msg.role}`} style={msg.isError ? { background: '#ffebee', color: '#c62828' } : {}}>
            {msg.isTyping ? (
              <>
                <ReactMarkdown>{msg.content || '...'}</ReactMarkdown><span className="typing-indicator">|</span>
              </>
            ) : (
              <ReactMarkdown>{msg.content}</ReactMarkdown>
            )}
          </div>
        ))}
        <div ref={messagesEndRef} />
      </div>

      {showRetry && (
        <div style={{ padding: '10px 20px' }}>
          <button 
            onClick={handleRetry}
            style={{
              padding: '10px 20px',
              background: '#ff9800',
              color: 'white',
              border: 'none',
              borderRadius: '20px',
              cursor: 'pointer',
              fontWeight: 'bold'
            }}
          >
            🔄 Try Again
          </button>
        </div>
      )}

      <button className="clear-btn" onClick={handleClear}>
        Clear Conversation
      </button>

      <form className="input-container" onSubmit={handleSubmit}>
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Type your message..."
          disabled={isStreaming}
        />
        <button type="submit" disabled={isStreaming || !input.trim()}>
          Send
        </button>
      </form>
    </div>
  )
}

export default App