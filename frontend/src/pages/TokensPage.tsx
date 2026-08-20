import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { Link } from 'react-router-dom'
import { listTokens, revokeToken } from '../api/tokens'
import { Layout } from '../components/Layout'
import { Badge, EmptyState, Loading, PageHeader } from '../components/ui'
import { formatDateTime } from '../lib/format'
import type { TokenSummary } from '../types/api'

function StatusBadge({ token }: { token: TokenSummary }) {
  if (token.revoked_at !== null) {
    return <Badge tone="danger">失効済み</Badge>
  }
  if (token.expires_at !== null && new Date(token.expires_at) <= new Date()) {
    return <Badge tone="warning">期限切れ</Badge>
  }
  return <Badge tone="success">有効</Badge>
}

export function TokensPage() {
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
        title="トークン"
        description="発行したトークンごとに、許可するオペレーションを設定できます。"
        actions={
          <Link to="/tokens/new" className="btn btn--primary">
            新規発行
          </Link>
        }
      />

      {tokensQuery.isLoading && <Loading />}

      {!tokensQuery.isLoading && tokens.length === 0 && (
        <EmptyState
          title="トークンがまだありません"
          description="「新規発行」から最初のトークンを作成してください。"
          action={
            <Link to="/tokens/new" className="btn btn--primary">
              新規発行
            </Link>
          }
        />
      )}

      {tokens.length > 0 && (
        <div className="table-wrap">
          <table className="table">
            <thead>
              <tr>
                <th>名前</th>
                <th>状態</th>
                <th>発行日時</th>
                <th>有効期限</th>
                <th>最終使用</th>
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
                  <td className="td--num">{formatDateTime(token.created_at)}</td>
                  <td className="td--num">{formatDateTime(token.expires_at, '無期限')}</td>
                  <td className="td--num">{formatDateTime(token.last_used_at, '未使用')}</td>
                  <td className="td--actions">
                    {token.revoked_at === null && (
                      <button
                        type="button"
                        className="btn btn--sm btn--danger"
                        onClick={() => revokeMutation.mutate(token.id)}
                        disabled={revokeMutation.isPending}
                      >
                        失効
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
