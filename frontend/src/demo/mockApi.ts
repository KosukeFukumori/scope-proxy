import { ApiError } from '../api/errors'
import type {
  BackendConfig,
  Operation,
  SchemaRefreshResult,
  SchemaSnapshot,
  TokenCreateResponse,
  TokenDetail,
  User,
} from '../types/api'

/**
 * In-browser stand-in for the FastAPI backend, used only for the static GitHub Pages demo
 * build (`npm run build:demo`). It reimplements just enough of the real API surface for the
 * admin UI to be explorable without a server. State lives in sessionStorage so it survives
 * reloads within a tab but resets for a fresh visitor.
 */

export const DEMO_CREDENTIALS = { username: 'admin', password: 'demo-password' }

interface DemoUser extends User {
  password: string
}

interface DemoToken extends TokenDetail {
  rawToken: string
}

interface DemoState {
  loggedIn: boolean
  users: DemoUser[]
  backendConfig: BackendConfig
  operations: Operation[]
  snapshots: SchemaSnapshot[]
  tokens: DemoToken[]
  nextTokenId: number
  nextSnapshotId: number
}

const STORAGE_KEY = 'scope-proxy-demo-state'

function isoNow(): string {
  return new Date().toISOString()
}

/** Mimics the backend's hash-based operation ids: the id is opaque while
 * `openapi_operation_id` carries the human-readable operationId. */
function demoOperation(
  id: string,
  method: string,
  path: string,
  summary: string,
  isActive = true,
): Operation {
  return {
    operation_id: `demo-hash-${id}`,
    method,
    path,
    openapi_operation_id: id,
    summary,
    is_active: isActive,
  }
}

function seedOperations(): Operation[] {
  return [
    demoOperation('listPets', 'GET', '/pets', 'List all pets'),
    demoOperation('createPet', 'POST', '/pets', 'Create a pet'),
    demoOperation('getPet', 'GET', '/pets/{petId}', 'Get a pet by id'),
    demoOperation('updatePet', 'PATCH', '/pets/{petId}', 'Update a pet'),
    demoOperation('deletePet', 'DELETE', '/pets/{petId}', 'Delete a pet'),
    demoOperation('listOrders', 'GET', '/orders', 'List orders'),
    demoOperation('createOrder', 'POST', '/orders', 'Create an order'),
    demoOperation('legacyExport', 'GET', '/legacy/export', 'Deprecated bulk export', false),
  ]
}

function seedState(): DemoState {
  const now = Date.now()
  const daysAgo = (days: number) => new Date(now - days * 24 * 60 * 60 * 1000).toISOString()

  const operations = seedOperations()

  const tokens: DemoToken[] = [
    {
      id: 'demo-token-batch',
      name: 'batch-job',
      created_at: daysAgo(14),
      expires_at: null,
      revoked_at: null,
      last_used_at: daysAgo(1),
      operation_ids: ['demo-hash-listPets', 'demo-hash-getPet'],
      rawToken: 'sp_demo_batch_job_do_not_use',
    },
    {
      id: 'demo-token-order-sync',
      name: 'order-sync',
      created_at: daysAgo(30),
      expires_at: daysAgo(-30),
      revoked_at: null,
      last_used_at: daysAgo(2),
      operation_ids: ['demo-hash-listOrders', 'demo-hash-createOrder'],
      rawToken: 'sp_demo_order_sync_do_not_use',
    },
    {
      id: 'demo-token-old-migration',
      name: 'old-migration-script',
      created_at: daysAgo(90),
      expires_at: null,
      revoked_at: daysAgo(20),
      last_used_at: daysAgo(21),
      operation_ids: ['demo-hash-listPets', 'demo-hash-createPet', 'demo-hash-deletePet'],
      rawToken: 'sp_demo_old_migration_do_not_use',
    },
  ]

  return {
    loggedIn: false,
    users: [{ id: 1, username: DEMO_CREDENTIALS.username, password: DEMO_CREDENTIALS.password }],
    backendConfig: {
      id: 1,
      endpoint_url: 'https://petstore.example.com',
      openapi_url: 'https://petstore.example.com/openapi.json',
      last_fetched_at: daysAgo(1),
      last_sync_status: 'success',
      last_sync_error: null,
      schema_sync_interval_seconds: null,
      effective_schema_sync_interval_seconds: 0,
    },
    operations,
    snapshots: [
      {
        id: 2,
        fetched_at: daysAgo(1),
        spec_hash: 'sha256:9f2b...c41a',
        diff_summary: 'Added: legacyExport (GET /legacy/export)',
      },
      {
        id: 1,
        fetched_at: daysAgo(14),
        spec_hash: 'sha256:1ac0...77e2',
        diff_summary: 'Initial fetch: 7 operations',
      },
    ],
    tokens,
    nextTokenId: 1,
    nextSnapshotId: 3,
  }
}

let state: DemoState | undefined

function loadState(): DemoState {
  if (state) return state
  try {
    const raw = sessionStorage.getItem(STORAGE_KEY)
    state = raw ? (JSON.parse(raw) as DemoState) : seedState()
  } catch {
    state = seedState()
  }
  return state
}

function saveState() {
  if (!state) return
  try {
    sessionStorage.setItem(STORAGE_KEY, JSON.stringify(state))
  } catch {
    // sessionStorage may be unavailable (e.g. private browsing); demo still works, just
    // without persistence across reloads.
  }
}

export function resetDemoState() {
  state = seedState()
  try {
    sessionStorage.removeItem(STORAGE_KEY)
  } catch {
    // ignore
  }
}

function currentUser(s: DemoState): User {
  const admin = s.users[0]
  return { id: admin.id, username: admin.username }
}

function toSummary(token: DemoToken): TokenDetail {
  const { rawToken: _rawToken, ...summary } = token
  return summary
}

function requireLogin(s: DemoState) {
  if (!s.loggedIn) {
    throw new ApiError(401, 'Not authenticated')
  }
}

async function sleep(ms: number) {
  await new Promise((resolve) => setTimeout(resolve, ms))
}

const ROUTES: {
  method: string
  pattern: RegExp
  handler: (s: DemoState, match: RegExpMatchArray, body: unknown, query: URLSearchParams) => unknown
}[] = [
  {
    method: 'POST',
    pattern: /^\/_admin\/api\/login$/,
    handler: (s, _m, body) => {
      const { username, password } = (body ?? {}) as { username?: string; password?: string }
      const admin = s.users[0]
      if (username !== admin.username || password !== admin.password) {
        throw new ApiError(401, 'Invalid username or password')
      }
      s.loggedIn = true
      return currentUser(s)
    },
  },
  {
    method: 'POST',
    pattern: /^\/_admin\/api\/logout$/,
    handler: (s) => {
      s.loggedIn = false
      return undefined
    },
  },
  {
    method: 'GET',
    pattern: /^\/_admin\/api\/me$/,
    handler: (s) => {
      requireLogin(s)
      return currentUser(s)
    },
  },
  {
    method: 'PATCH',
    pattern: /^\/_admin\/api\/me\/password$/,
    handler: (s, _m, body) => {
      requireLogin(s)
      const admin = s.users[0]
      const { current_password, new_password } = (body ?? {}) as {
        current_password?: string
        new_password?: string
      }
      if (current_password !== admin.password) {
        throw new ApiError(400, 'Current password is incorrect')
      }
      if (new_password) admin.password = new_password
      return undefined
    },
  },
  {
    method: 'PATCH',
    pattern: /^\/_admin\/api\/me\/username$/,
    handler: (s, _m, body) => {
      requireLogin(s)
      const admin = s.users[0]
      const { username } = (body ?? {}) as { username?: string }
      if (username) admin.username = username
      return currentUser(s)
    },
  },
  {
    method: 'GET',
    pattern: /^\/_admin\/api\/backend-config$/,
    handler: (s) => {
      requireLogin(s)
      return s.backendConfig
    },
  },
  {
    method: 'PUT',
    pattern: /^\/_admin\/api\/backend-config$/,
    handler: (s, _m, body) => {
      requireLogin(s)
      const { endpoint_url, openapi_url, schema_sync_interval_seconds } = (body ?? {}) as {
        endpoint_url?: string
        openapi_url?: string
        schema_sync_interval_seconds?: number | null
      }
      const urlChanged =
        (endpoint_url !== undefined && endpoint_url !== s.backendConfig.endpoint_url) ||
        (openapi_url !== undefined && openapi_url !== s.backendConfig.openapi_url)
      if (urlChanged) {
        // Mirror the real backend: switching the target wipes operations and permissions.
        s.operations = []
        s.tokens = s.tokens.map((token) => ({ ...token, operation_ids: [] }))
        s.backendConfig = { ...s.backendConfig, last_fetched_at: null }
      }
      s.backendConfig = {
        ...s.backendConfig,
        endpoint_url: endpoint_url ?? s.backendConfig.endpoint_url,
        openapi_url: openapi_url ?? s.backendConfig.openapi_url,
        schema_sync_interval_seconds: schema_sync_interval_seconds ?? null,
        effective_schema_sync_interval_seconds: schema_sync_interval_seconds ?? 0,
      }
      return s.backendConfig
    },
  },
  {
    method: 'POST',
    pattern: /^\/_admin\/api\/backend-config\/refresh$/,
    handler: (s) => {
      requireLogin(s)
      s.backendConfig = { ...s.backendConfig, last_fetched_at: isoNow() }
      // After a backend switch the operations list is empty; "fetching" the schema
      // re-seeds it so the demo shows a schema-change diff, like the real backend.
      const added: string[] = []
      if (s.operations.length === 0) {
        s.operations = seedOperations()
        for (const op of s.operations) {
          added.push(`${op.method} ${op.path}`)
        }
      }
      const diffSummary = JSON.stringify({
        added,
        updated: [],
        removed: [],
        skipped_admin_conflict: [],
      })
      const snapshot: SchemaSnapshot = {
        id: s.nextSnapshotId++,
        fetched_at: isoNow(),
        spec_hash: `sha256:demo-${Math.random().toString(16).slice(2, 10)}`,
        diff_summary: diffSummary,
      }
      if (added.length > 0) {
        s.snapshots = [snapshot, ...s.snapshots]
      }
      const response: SchemaRefreshResult = { snapshot, diff_summary: diffSummary }
      return response
    },
  },
  {
    method: 'GET',
    pattern: /^\/_admin\/api\/operations$/,
    handler: (s, _m, _body, query) => {
      requireLogin(s)
      const isActive = query.get('is_active')
      if (isActive === null) return s.operations
      const want = isActive === 'true'
      return s.operations.filter((op) => op.is_active === want)
    },
  },
  {
    method: 'GET',
    pattern: /^\/_admin\/api\/schema-snapshots$/,
    handler: (s) => {
      requireLogin(s)
      return s.snapshots
    },
  },
  {
    method: 'GET',
    pattern: /^\/_admin\/api\/tokens$/,
    handler: (s) => {
      requireLogin(s)
      return s.tokens.map(toSummary)
    },
  },
  {
    method: 'POST',
    pattern: /^\/_admin\/api\/tokens$/,
    handler: (s, _m, body) => {
      requireLogin(s)
      const { name, expires_at, operation_ids } = (body ?? {}) as {
        name?: string
        expires_at?: string | null
        operation_ids?: string[]
      }
      const rawToken = `sp_demo_${Math.random().toString(36).slice(2, 12)}`
      const token: DemoToken = {
        id: `demo-token-${s.nextTokenId++}`,
        name: name ?? 'untitled',
        created_at: isoNow(),
        expires_at: expires_at ?? null,
        revoked_at: null,
        last_used_at: null,
        operation_ids: operation_ids ?? [],
        rawToken,
      }
      s.tokens = [token, ...s.tokens]
      const response: TokenCreateResponse = { ...toSummary(token), raw_token: rawToken }
      return response
    },
  },
  {
    method: 'GET',
    pattern: /^\/_admin\/api\/tokens\/([^/]+)$/,
    handler: (s, m) => {
      requireLogin(s)
      const token = s.tokens.find((t) => t.id === m[1])
      if (!token) throw new ApiError(404, 'Token not found')
      return toSummary(token)
    },
  },
  {
    method: 'PATCH',
    pattern: /^\/_admin\/api\/tokens\/([^/]+)$/,
    handler: (s, m, body) => {
      requireLogin(s)
      const token = s.tokens.find((t) => t.id === m[1])
      if (!token) throw new ApiError(404, 'Token not found')
      const { name, expires_at, operation_ids } = (body ?? {}) as {
        name?: string
        expires_at?: string | null
        operation_ids?: string[]
      }
      if (name !== undefined) token.name = name
      if (expires_at !== undefined) token.expires_at = expires_at
      if (operation_ids !== undefined) token.operation_ids = operation_ids
      return toSummary(token)
    },
  },
  {
    method: 'POST',
    pattern: /^\/_admin\/api\/tokens\/([^/]+)\/revoke$/,
    handler: (s, m) => {
      requireLogin(s)
      const token = s.tokens.find((t) => t.id === m[1])
      if (!token) throw new ApiError(404, 'Token not found')
      token.revoked_at = isoNow()
      return toSummary(token)
    },
  },
  {
    method: 'DELETE',
    pattern: /^\/_admin\/api\/tokens\/([^/]+)$/,
    handler: (s, m) => {
      requireLogin(s)
      const before = s.tokens.length
      s.tokens = s.tokens.filter((t) => t.id !== m[1])
      if (s.tokens.length === before) throw new ApiError(404, 'Token not found')
      return undefined
    },
  },
]

export async function mockRequest<T>(path: string, init?: RequestInit): Promise<T> {
  await sleep(150)

  const method = (init?.method ?? 'GET').toUpperCase()
  const [pathname, search] = path.split('?')
  const query = new URLSearchParams(search ?? '')
  const s = loadState()

  const body = init?.body ? (JSON.parse(init.body as string) as unknown) : undefined

  for (const route of ROUTES) {
    if (route.method !== method) continue
    const match = pathname.match(route.pattern)
    if (!match) continue
    const result = route.handler(s, match, body, query)
    saveState()
    return result as T
  }

  throw new ApiError(404, `No demo mock for ${method} ${pathname}`)
}
