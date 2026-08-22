import { useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { Link } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import { deleteToken, listTokens, revokeToken } from '../api/tokens'
import { Layout } from '../components/Layout'
import { Badge, EmptyState, Loading, PageHeader } from '../components/ui'
import { formatDateTime } from '../lib/format'
import type { TokenSummary } from '../types/api'

type StatusFilter = 'all' | 'active' | 'revoked' | 'expired'

function getTokenStatus(token: TokenSummary): 'active' | 'revoked' | 'expired' {
  if (token.revoked_at !== null) {
    return 'revoked'
  }
  if (token.expires_at !== null && new Date(token.expires_at) <= new Date()) {
    return 'expired'
  }
  return 'active'
}

function StatusBadge({ token }: { token: TokenSummary }) {
  const { t } = useTranslation()
  const status = getTokenStatus(token)
  if (status === 'revoked') {
    return <Badge tone="danger">{t('tokens.status.revoked')}</Badge>
  }
  if (status === 'expired') {
    return <Badge tone="warning">{t('tokens.status.expired')}</Badge>
  }
  return <Badge tone="success">{t('tokens.status.active')}</Badge>
}

export function TokensPage() {
  const { t, i18n } = useTranslation()
  const queryClient = useQueryClient()
  const [filter, setFilter] = useState<StatusFilter>('all')
  const tokensQuery = useQuery({ queryKey: ['tokens'], queryFn: listTokens })

  const FILTERS: { value: StatusFilter; label: string }[] = [
    { value: 'all', label: t('tokens.filters.all') },
    { value: 'active', label: t('tokens.filters.active') },
    { value: 'revoked', label: t('tokens.filters.revoked') },
    { value: 'expired', label: t('tokens.filters.expired') },
  ]

  const revokeMutation = useMutation({
    mutationFn: (id: string) => revokeToken(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['tokens'] })
    },
  })

  const deleteMutation = useMutation({
    mutationFn: (id: string) => deleteToken(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['tokens'] })
    },
  })

  const allTokens = tokensQuery.data ?? []
  const tokens = filter === 'all' ? allTokens : allTokens.filter((token) => getTokenStatus(token) === filter)

  const handleDelete = (id: string) => {
    if (window.confirm(t('tokens.confirmDelete'))) {
      deleteMutation.mutate(id)
    }
  }

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

      <div className="segmented">
        {FILTERS.map((item) => (
          <button
            key={item.value}
            type="button"
            className={filter === item.value ? 'segmented__item is-active' : 'segmented__item'}
            onClick={() => setFilter(item.value)}
          >
            {item.label}
          </button>
        ))}
      </div>

      {tokensQuery.isLoading && <Loading />}

      {!tokensQuery.isLoading && allTokens.length === 0 && (
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

      {!tokensQuery.isLoading && allTokens.length > 0 && tokens.length === 0 && (
        <EmptyState title={t('tokens.filterEmpty.title')} description={t('tokens.filterEmpty.description')} />
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
                    {token.revoked_at !== null && (
                      <button
                        type="button"
                        className="btn btn--sm btn--danger"
                        onClick={() => handleDelete(token.id)}
                        disabled={deleteMutation.isPending}
                      >
                        {t('tokens.delete')}
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
