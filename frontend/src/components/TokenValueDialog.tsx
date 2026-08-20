import { useState } from 'react'
import { useTranslation } from 'react-i18next'

export function TokenValueDialog({ rawToken, onClose }: { rawToken: string; onClose: () => void }) {
  const { t } = useTranslation()
  const [copied, setCopied] = useState(false)

  async function handleCopy() {
    await navigator.clipboard.writeText(rawToken)
    setCopied(true)
  }

  return (
    <div className="modal-backdrop" role="dialog" aria-modal="true" aria-labelledby="token-dialog-title">
      <div className="modal">
        <div className="stack stack--tight">
          <h2 id="token-dialog-title">{t('tokenValueDialog.title')}</h2>
          <p className="alert alert--error">{t('tokenValueDialog.warning')}</p>
          <code className="token-value">{rawToken}</code>
        </div>
        <div className="modal__actions">
          <button type="button" className="btn" onClick={handleCopy}>
            {copied ? t('tokenValueDialog.copied') : t('tokenValueDialog.copy')}
          </button>
          <button type="button" className="btn btn--primary" onClick={onClose}>
            {t('common.close')}
          </button>
        </div>
      </div>
    </div>
  )
}
