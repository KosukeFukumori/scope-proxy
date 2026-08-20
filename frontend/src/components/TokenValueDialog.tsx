import { useState } from 'react'

export function TokenValueDialog({ rawToken, onClose }: { rawToken: string; onClose: () => void }) {
  const [copied, setCopied] = useState(false)

  async function handleCopy() {
    await navigator.clipboard.writeText(rawToken)
    setCopied(true)
  }

  return (
    <div
      style={{
        position: 'fixed',
        inset: 0,
        background: 'rgba(0,0,0,0.4)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        zIndex: 50,
      }}
    >
      <div style={{ background: '#fff', borderRadius: '8px', padding: '1.5rem', width: '480px' }}>
        <h2 style={{ marginTop: 0 }}>トークンを発行しました</h2>
        <p style={{ color: '#dc2626', fontWeight: 600 }}>
          このトークンは二度と表示されません。今のうちに安全な場所へ保存してください。
        </p>
        <code
          style={{
            display: 'block',
            wordBreak: 'break-all',
            background: '#f3f4f6',
            padding: '0.75rem',
            borderRadius: '6px',
            marginBottom: '1rem',
          }}
        >
          {rawToken}
        </code>
        <div style={{ display: 'flex', gap: '0.5rem', justifyContent: 'flex-end' }}>
          <button onClick={handleCopy}>{copied ? 'コピーしました' : 'コピー'}</button>
          <button onClick={onClose}>閉じる</button>
        </div>
      </div>
    </div>
  )
}
