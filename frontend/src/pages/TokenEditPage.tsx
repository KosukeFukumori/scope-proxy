import { useState } from 'react'
import type { FormEvent } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { useNavigate, useParams } from 'react-router-dom'
import { createToken, getToken, updateToken } from '../api/tokens'
import { listOperations } from '../api/operations'
import { ApiError } from '../api/client'
import { Layout } from '../components/Layout'
import { OperationPermissionTable } from '../components/OperationPermissionTable'
import { TokenValueDialog } from '../components/TokenValueDialog'
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

  const createMutation = useMutation({
    mutationFn: () =>
      createToken({
        name,
        expires_at: expiresAt ? new Date(expiresAt).toISOString() : null,
        operation_ids: [...selectedIds],
      }),
    onSuccess: (result) => {
      queryClient.invalidateQueries({ queryKey: ['tokens'] })
      setIssuedRawToken(result.raw_token)
    },
  })

  const updateMutation = useMutation({
    mutationFn: () =>
      updateToken(tokenId!, {
        name,
        expires_at: expiresAt ? new Date(expiresAt).toISOString() : null,
        operation_ids: [...selectedIds],
      }),
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
      <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '1rem', maxWidth: '640px' }}>
        <label>
          名前
          <input
            type="text"
            value={name}
            onChange={(e) => setName(e.target.value)}
            required
            style={{ width: '100%', padding: '0.5rem', marginTop: '0.25rem' }}
          />
        </label>
        <label>
          有効期限(任意)
          <input
            type="datetime-local"
            value={expiresAt}
            onChange={(e) => setExpiresAt(e.target.value)}
            style={{ width: '100%', padding: '0.5rem', marginTop: '0.25rem' }}
          />
        </label>

        <div>
          <p style={{ marginBottom: '0.5rem', fontWeight: 600 }}>許可するオペレーション</p>
          <OperationPermissionTable operations={operations} selectedIds={selectedIds} onToggle={toggleOperation} />
        </div>

        {mutation.isError && (
          <p style={{ color: '#dc2626' }}>
            {mutation.error instanceof ApiError ? mutation.error.message : '保存に失敗しました'}
          </p>
        )}

        <button type="submit" disabled={mutation.isPending} style={{ alignSelf: 'flex-start', padding: '0.5rem 1rem' }}>
          {isEditing ? '保存' : '発行'}
        </button>
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
      <h1>{isEditing ? 'トークン編集' : 'トークン発行'}</h1>

      {isLoading ? (
        <p>読み込み中...</p>
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
