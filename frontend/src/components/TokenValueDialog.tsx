import { useState } from 'react'
import { useTranslation } from 'react-i18next'
import type { Operation } from '../types/api'

export function TokenValueDialog({
  rawToken,
  sampleOperation,
  onClose,
}: {
  rawToken: string
  sampleOperation: Operation | null
  onClose: () => void
}) {
  const { t } = useTranslation()
  const [copied, setCopied] = useState(false)
  const [usageCopied, setUsageCopied] = useState(false)

  const samplePath = sampleOperation?.path ?? '/path/to/resource'
  const sampleMethod = (sampleOperation?.method ?? 'GET').toUpperCase()
  const origin = window.location.origin
  const usageCommand = `curl -X ${sampleMethod} \\\n  -H "Authorization: Bearer ${rawToken}" \\\n  "${origin}${samplePath}"`

  async function handleCopy() {
    await navigator.clipboard.writeText(rawToken)
    setCopied(true)
  }

  async function handleUsageCopy() {
    await navigator.clipboard.writeText(usageCommand)
    setUsageCopied(true)
  }

  return (
    <div className="modal-backdrop" role="dialog" aria-modal="true" aria-labelledby="token-dialog-title">
      <div className="modal">
        <div className="stack stack--tight">
          <h2 id="token-dialog-title">{t('tokenValueDialog.title')}</h2>
          <p className="alert alert--error">{t('tokenValueDialog.warning')}</p>
          <code className="token-value">{rawToken}</code>

          <div className="stack stack--tight">
            <p className="field__label">{t('tokenValueDialog.usageTitle')}</p>
            <p className="field__hint">{t('tokenValueDialog.usageDescription')}</p>
            <pre className="token-usage">
              <code>{usageCommand}</code>
            </pre>
            <button type="button" className="btn btn--sm" onClick={handleUsageCopy}>
              {usageCopied ? t('tokenValueDialog.copied') : t('tokenValueDialog.copyUsage')}
            </button>
          </div>
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
