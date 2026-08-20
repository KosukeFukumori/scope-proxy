import { useState } from 'react'

export function TokenValueDialog({ rawToken, onClose }: { rawToken: string; onClose: () => void }) {
  const [copied, setCopied] = useState(false)

  async function handleCopy() {
    await navigator.clipboard.writeText(rawToken)
    setCopied(true)
  }

  return (
    <div className="modal-backdrop" role="dialog" aria-modal="true" aria-labelledby="token-dialog-title">
      <div className="modal">
        <div className="stack stack--tight">
          <h2 id="token-dialog-title">トークンを発行しました</h2>
          <p className="alert alert--error">
            このトークンは二度と表示されません。今のうちに安全な場所へ保存してください。
          </p>
          <code className="token-value">{rawToken}</code>
        </div>
        <div className="modal__actions">
          <button type="button" className="btn" onClick={handleCopy}>
            {copied ? 'コピーしました' : 'コピー'}
          </button>
          <button type="button" className="btn btn--primary" onClick={onClose}>
            閉じる
          </button>
        </div>
      </div>
    </div>
  )
}
