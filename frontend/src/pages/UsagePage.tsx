import { useTranslation, Trans } from 'react-i18next'
import { Layout } from '../components/Layout'
import { PageHeader } from '../components/ui'

function Step({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div className="card">
      <div className="card__body stack stack--tight">
        <h2 style={{ fontSize: '1rem' }}>{title}</h2>
        {children}
      </div>
    </div>
  )
}

export function UsagePage() {
  const { t } = useTranslation()
  const origin = window.location.origin

  const curlExample = `curl -X GET \\\n  -H "Authorization: Bearer <YOUR_TOKEN>" \\\n  "${origin}/path/to/resource"`

  return (
    <Layout>
      <PageHeader title={t('usage.title')} description={t('usage.description')} />

      <div className="stack">
        <Step title={t('usage.step1.title')}>
          <p>{t('usage.step1.description')}</p>
        </Step>

        <Step title={t('usage.step2.title')}>
          <p>{t('usage.step2.description')}</p>
        </Step>

        <Step title={t('usage.step3.title')}>
          <p>
            <Trans i18nKey="usage.step3.description" components={{ code: <code /> }} />
          </p>
        </Step>

        <Step title={t('usage.step4.title')}>
          <p>{t('usage.step4.description')}</p>
          <pre className="token-usage">
            <code>{curlExample}</code>
          </pre>
          <p className="field__hint">{t('usage.step4.hint')}</p>
        </Step>

        <Step title={t('usage.errors.title')}>
          <ul className="stack stack--tight" style={{ paddingLeft: '1.25rem', listStyle: 'disc' }}>
            <li>{t('usage.errors.unauthorized')}</li>
            <li>{t('usage.errors.forbidden')}</li>
            <li>{t('usage.errors.notFound')}</li>
          </ul>
        </Step>
      </div>
    </Layout>
  )
}
