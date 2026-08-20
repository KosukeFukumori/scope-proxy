import { useState } from 'react'
import type { FormEvent } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { useNavigate, useParams } from 'react-router-dom'
import { createToken, getToken, updateToken } from '../api/tokens'
import { listOperations } from '../api/operations'
import { Layout } from '../components/Layout'
import { OperationPermissionTable } from '../components/OperationPermissionTable'
import { TokenValueDialog } from '../components/TokenValueDialog'
import { ErrorAlert, Loading, PageHeader } from '../components/ui'
import { errorMessage } from '../lib/format'
import type { Operation, TokenDetail } from '../types/api'

function TokenForm({
  tokenId,
  initialToken,
  operations,
}: {
  tokenId: number | null
  initialToken: TokenDetail | null
  operations: Operation[]
}) {
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
                名前
              </label>
              <input
                id="token-name"
                className="input"
                type="text"
                value={name}
                onChange={(e) => setName(e.target.value)}
                placeholder="例: batch-job"
                required
              />
            </div>

            <div className="field">
              <label className="field__label" htmlFor="token-expires">
                有効期限
              </label>
              <input
                id="token-expires"
                className="input"
                type="datetime-local"
                value={expiresAt}
                onChange={(e) => setExpiresAt(e.target.value)}
              />
              <p className="field__hint">未入力の場合は無期限になります。</p>
            </div>
          </div>
        </div>

        <section className="stack stack--tight">
          <div className="section__header">
            <h2>許可するオペレーション</h2>
            <span className="muted" style={{ fontSize: '0.8rem' }}>
              {selectedIds.size} 件を選択中
            </span>
          </div>
          <OperationPermissionTable operations={operations} selectedIds={selectedIds} onToggle={toggleOperation} />
        </section>

        {mutation.isError && <ErrorAlert>{errorMessage(mutation.error, '保存に失敗しました')}</ErrorAlert>}

        <div className="row">
          <button type="submit" className="btn btn--primary" disabled={mutation.isPending}>
            {isEditing ? '保存' : '発行'}
          </button>
          <button type="button" className="btn" onClick={() => navigate('/tokens')}>
            キャンセル
          </button>
        </div>
      </form>

      {issuedRawToken && (
        <TokenValueDialog
          rawToken={issuedRawToken}
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
  const params = useParams<{ id: string }>()
  const tokenId = params.id ? Number(params.id) : null
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
        title={isEditing ? 'トークン編集' : 'トークン発行'}
        description="チェックを入れた operationId のみ、プロキシ経由でのアクセスが許可されます。"
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
    </Layout>
  )
}
