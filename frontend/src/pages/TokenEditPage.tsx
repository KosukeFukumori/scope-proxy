import { useState } from 'react'
import type { FormEvent } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { useNavigate, useParams } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import { createToken, getToken, listTokenLogs, updateToken } from '../api/tokens'
import { listOperations } from '../api/operations'
import { Layout } from '../components/Layout'
import { OperationPermissionTable } from '../components/OperationPermissionTable'
import { TokenValueDialog } from '../components/TokenValueDialog'
import { Badge, EmptyState, ErrorAlert, Loading, PageHeader } from '../components/ui'
import { errorMessage, formatDateTime } from '../lib/format'
import type { Operation, TokenDetail } from '../types/api'

function StatusBadge({ status }: { status: number }) {
  if (status >= 500) {
    return <Badge tone="danger">{status}</Badge>
  }
  if (status >= 400) {
    return <Badge tone="warning">{status}</Badge>
  }
  return <Badge tone="success">{status}</Badge>
}

function TokenLogsSection({ tokenId }: { tokenId: string }) {
  const { t, i18n } = useTranslation()
  const logsQuery = useQuery({ queryKey: ['tokenLogs', tokenId], queryFn: () => listTokenLogs(tokenId) })
  const logs = logsQuery.data ?? []

  return (
    <section className="section">
      <div className="section__header">
        <h2>{t('tokenEdit.logs.title')}</h2>
      </div>

      {logsQuery.isLoading && <Loading />}

      {!logsQuery.isLoading && logs.length === 0 && <EmptyState title={t('tokenEdit.logs.empty')} />}

      {logs.length > 0 && (
        <div className="table-wrap">
          <table className="table">
            <thead>
              <tr>
                <th>{t('tokenEdit.logs.table.time')}</th>
                <th>{t('tokenEdit.logs.table.method')}</th>
                <th>{t('tokenEdit.logs.table.path')}</th>
                <th>{t('tokenEdit.logs.table.status')}</th>
                <th>{t('tokenEdit.logs.table.latency')}</th>
              </tr>
            </thead>
            <tbody>
              {logs.map((log) => (
                <tr key={log.id}>
                  <td className="td--num">{formatDateTime(log.created_at, undefined, i18n.resolvedLanguage)}</td>
                  <td>{log.method}</td>
                  <td>{log.path}</td>
                  <td>
                    <StatusBadge status={log.status} />
                  </td>
                  <td className="td--num">{log.latency_ms} ms</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </section>
  )
}

function TokenForm({
  tokenId,
  initialToken,
  operations,
}: {
  tokenId: string | null
  initialToken: TokenDetail | null
  operations: Operation[]
}) {
  const operationById = new Map(operations.map((operation) => [operation.operation_id, operation]))
  const { t } = useTranslation()
  const isEditing = tokenId !== null
  const navigate = useNavigate()
  const queryClient = useQueryClient()

  const [name, setName] = useState(initialToken?.name ?? '')
  const [expiresAt, setExpiresAt] = useState(initialToken?.expires_at?.slice(0, 16) ?? '')
  const [selectedIds, setSelectedIds] = useState<Set<string>>(new Set(initialToken?.operation_ids ?? []))
  const [issuedRawToken, setIssuedRawToken] = useState<string | null>(null)

  function toggleOperation(operationId: string) {
    setSelectedIds((prev) => {
      const next = new Set(prev)
      if (next.has(operationId)) {
        next.delete(operationId)
      } else {
        next.add(operationId)
      }
      return next
    })
  }

  const payload = () => ({
    name,
    expires_at: expiresAt ? new Date(expiresAt).toISOString() : null,
    operation_ids: [...selectedIds],
  })

  const createMutation = useMutation({
    mutationFn: () => createToken(payload()),
    onSuccess: (result) => {
      queryClient.invalidateQueries({ queryKey: ['tokens'] })
      setIssuedRawToken(result.raw_token)
    },
  })

  const updateMutation = useMutation({
    mutationFn: () => updateToken(tokenId!, payload()),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['tokens'] })
      navigate('/tokens')
    },
  })

  const mutation = isEditing ? updateMutation : createMutation

  function handleSubmit(event: FormEvent) {
    event.preventDefault()
    mutation.mutate()
  }

  return (
    <>
      <form className="stack" onSubmit={handleSubmit}>
        <div className="card">
          <div className="card__body stack">
            <div className="field">
              <label className="field__label" htmlFor="token-name">
                {t('tokenEdit.form.nameLabel')}
              </label>
              <input
                id="token-name"
                className="input"
                type="text"
                value={name}
                onChange={(e) => setName(e.target.value)}
                placeholder={t('tokenEdit.form.namePlaceholder')}
                required
              />
            </div>

            <div className="field">
              <label className="field__label" htmlFor="token-expires">
                {t('tokenEdit.form.expiresLabel')}
              </label>
              <input
                id="token-expires"
                className="input"
                type="datetime-local"
                value={expiresAt}
                onChange={(e) => setExpiresAt(e.target.value)}
              />
              <p className="field__hint">{t('tokenEdit.form.expiresHint')}</p>
            </div>
          </div>
        </div>

        <section className="stack stack--tight">
          <div className="section__header">
            <h2>{t('tokenEdit.form.permissionsTitle')}</h2>
            <span className="muted" style={{ fontSize: '0.8rem' }}>
              {t('tokenEdit.form.selectedCount', { count: selectedIds.size })}
            </span>
          </div>
          <OperationPermissionTable operations={operations} selectedIds={selectedIds} onToggle={toggleOperation} />
        </section>

        {mutation.isError && <ErrorAlert>{errorMessage(mutation.error, t('tokenEdit.form.saveError'))}</ErrorAlert>}

        <div className="row">
          <button type="submit" className="btn btn--primary" disabled={mutation.isPending}>
            {isEditing ? t('tokenEdit.form.save') : t('tokenEdit.form.issue')}
          </button>
          <button type="button" className="btn" onClick={() => navigate('/tokens')}>
            {t('tokenEdit.form.cancel')}
          </button>
        </div>
      </form>

      {issuedRawToken && (
        <TokenValueDialog
          rawToken={issuedRawToken}
          sampleOperation={operationById.get([...selectedIds][0] ?? '') ?? null}
          onClose={() => {
            setIssuedRawToken(null)
            navigate('/tokens')
          }}
        />
      )}
    </>
  )
}

export function TokenEditPage() {
  const { t } = useTranslation()
  const params = useParams<{ id: string }>()
  const tokenId = params.id ?? null
  const isEditing = tokenId !== null

  const operationsQuery = useQuery({ queryKey: ['operations', 'all'], queryFn: () => listOperations() })
  const tokenQuery = useQuery({
    queryKey: ['token', tokenId],
    queryFn: () => getToken(tokenId!),
    enabled: isEditing,
  })

  const operations = operationsQuery.data ?? []
  const isLoading = operationsQuery.isLoading || (isEditing && tokenQuery.isLoading)

  return (
    <Layout>
      <PageHeader
        title={isEditing ? t('tokenEdit.titleEdit') : t('tokenEdit.titleNew')}
        description={t('tokenEdit.description')}
      />

      {isLoading ? (
        <Loading />
      ) : (
        <TokenForm
          key={tokenId ?? 'new'}
          tokenId={tokenId}
          initialToken={tokenQuery.data ?? null}
          operations={operations}
        />
      )}

      {tokenId && !isLoading && <TokenLogsSection tokenId={tokenId} />}
    </Layout>
  )
}
