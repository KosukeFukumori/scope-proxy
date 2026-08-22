import type { ReactNode } from 'react'
import { useTranslation } from 'react-i18next'
import { ErrorAlert } from './ui'

/** Generic confirmation modal, reusing the same visual style as TokenValueDialog. */
export function ConfirmDialog({
  title,
  message,
  confirmLabel,
  confirmDisabled,
  errorMessage,
  onConfirm,
  onCancel,
}: {
  title: string
  message: string
  confirmLabel: string
  confirmDisabled?: boolean
  errorMessage?: ReactNode
  onConfirm: () => void
  onCancel: () => void
}) {
  const { t } = useTranslation()

  return (
    <div className="modal-backdrop" role="dialog" aria-modal="true" aria-labelledby="confirm-dialog-title">
      <div className="modal">
        <div className="stack stack--tight">
          <h2 id="confirm-dialog-title">{title}</h2>
          <p>{message}</p>
          {errorMessage && <ErrorAlert>{errorMessage}</ErrorAlert>}
        </div>
        <div className="modal__actions">
          <button type="button" className="btn" onClick={onCancel} disabled={confirmDisabled}>
            {t('common.cancel')}
          </button>
          <button type="button" className="btn btn--danger" onClick={onConfirm} disabled={confirmDisabled}>
            {confirmLabel}
          </button>
        </div>
      </div>
    </div>
  )
}
