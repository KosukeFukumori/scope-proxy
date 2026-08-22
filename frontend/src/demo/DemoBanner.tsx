import { useTranslation } from 'react-i18next'
import { resetDemoState } from './mockApi'

const IS_DEMO = import.meta.env.MODE === 'demo'

export function DemoBanner() {
  const { t } = useTranslation()

  if (!IS_DEMO) return null

  return (
    <div className="demo-banner">
      <span>{t('demo.banner')}</span>
      <button
        type="button"
        className="btn btn--sm"
        onClick={() => {
          resetDemoState()
          window.location.reload()
        }}
      >
        {t('demo.reset')}
      </button>
    </div>
  )
}
