import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { Link } from 'react-router-dom'
import { listTokens, revokeToken } from '../api/tokens'
import { Layout } from '../components/Layout'

export function TokensPage() {
  const queryClient = useQueryClient()
  const tokensQuery = useQuery({ queryKey: ['tokens'], queryFn: listTokens })

  const revokeMutation = useMutation({
    mutationFn: (id: number) => revokeToken(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['tokens'] })
    },
  })

  return (
    <Layout>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <h1>トークン一覧</h1>
        <Link to="/tokens/new">
          <button>新規発行</button>
        </Link>
      </div>

      {tokensQuery.isLoading && <p>読み込み中...</p>}

      {tokensQuery.data && tokensQuery.data.length === 0 && (
        <p style={{ color: '#6b7280' }}>トークンがまだありません。</p>
      )}

      {tokensQuery.data && tokensQuery.data.length > 0 && (
        <table>
          <thead>
            <tr>
              <th>名前</th>
              <th>発行日時</th>
              <th>有効期限</th>
              <th>最終使用</th>
              <th>状態</th>
              <th></th>
            </tr>
          </thead>
          <tbody>
            {tokensQuery.data.map((token) => {
              const revoked = token.revoked_at !== null
              const expired = token.expires_at !== null && new Date(token.expires_at) <= new Date()
              return (
                <tr key={token.id}>
                  <td>
                    <Link to={`/tokens/${token.id}`}>{token.name}</Link>
                  </td>
                  <td>{new Date(token.created_at).toLocaleString()}</td>
                  <td>{token.expires_at ? new Date(token.expires_at).toLocaleString() : '無期限'}</td>
                  <td>{token.last_used_at ? new Date(token.last_used_at).toLocaleString() : '未使用'}</td>
                  <td>{revoked ? '失効済み' : expired ? '期限切れ' : '有効'}</td>
                  <td>
                    {!revoked && (
                      <button onClick={() => revokeMutation.mutate(token.id)} disabled={revokeMutation.isPending}>
                        失効
                      </button>
                    )}
                  </td>
                </tr>
              )
            })}
          </tbody>
        </table>
      )}
    </Layout>
  )
}
