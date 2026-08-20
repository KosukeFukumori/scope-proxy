import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { Link } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import { listTokens, revokeToken } from '../api/tokens'
import { Layout } from '../components/Layout'
import { Badge, EmptyState, Loading, PageHeader } from '../components/ui'
import { formatDateTime } from '../lib/format'
import type { TokenSummary } from '../types/api'

function StatusBadge({ token }: { token: TokenSummary }) {
  const { t } = useTranslation()
  if (token.revoked_at !== null) {
    return <Badge tone="danger">{t('tokens.status.revoked')}</Badge>
  }
  if (token.expires_at !== null && new Date(token.expires_at) <= new Date()) {
    return <Badge tone="warning">{t('tokens.status.expired')}</Badge>
  }
  return <Badge tone="success">{t('tokens.status.active')}</Badge>
}

export function TokensPage() {
  const { t, i18n } = useTranslation()
  const queryClient = useQueryClient()
  const tokensQuery = useQuery({ queryKey: ['tokens'], queryFn: listTokens })

  const revokeMutation = useMutation({
    mutationFn: (id: number) => revokeToken(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['tokens'] })
    },
  })

  const tokens = tokensQuery.data ?? []

  return (
    <Layout>
      <PageHeader
        title={t('tokens.title')}
        description={t('tokens.description')}
        actions={
          <Link to="/tokens/new" className="btn btn--primary">
            {t('tokens.newToken')}
          </Link>
        }
      />

      {tokensQuery.isLoading && <Loading />}

      {!tokensQuery.isLoading && tokens.length === 0 && (
        <EmptyState
          title={t('tokens.empty.title')}
          description={t('tokens.empty.description')}
          action={
            <Link to="/tokens/new" className="btn btn--primary">
              {t('tokens.newToken')}
            </Link>
          }
        />
      )}

      {tokens.length > 0 && (
        <div className="table-wrap">
          <table className="table">
            <thead>
              <tr>
                <th>{t('tokens.table.name')}</th>
                <th>{t('tokens.table.status')}</th>
                <th>{t('tokens.table.createdAt')}</th>
                <th>{t('tokens.table.expiresAt')}</th>
                <th>{t('tokens.table.lastUsedAt')}</th>
                <th />
              </tr>
            </thead>
            <tbody>
              {tokens.map((token) => (
                <tr key={token.id}>
                  <td>
                    <Link to={`/tokens/${token.id}`}>{token.name}</Link>
                  </td>
                  <td>
                    <StatusBadge token={token} />
                  </td>
                  <td className="td--num">{formatDateTime(token.created_at, undefined, i18n.resolvedLanguage)}</td>
                  <td className="td--num">
                    {formatDateTime(token.expires_at, t('tokens.noExpiry'), i18n.resolvedLanguage)}
                  </td>
                  <td className="td--num">
                    {formatDateTime(token.last_used_at, t('tokens.notUsed'), i18n.resolvedLanguage)}
                  </td>
                  <td className="td--actions">
                    {token.revoked_at === null && (
                      <button
                        type="button"
                        className="btn btn--sm btn--danger"
                        onClick={() => revokeMutation.mutate(token.id)}
                        disabled={revokeMutation.isPending}
                      >
                        {t('tokens.revoke')}
                      </button>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </Layout>
  )
}
