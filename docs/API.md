# PX Solver API — Documentação Completa

**Versão**: 2.1.0  
**Base URL**: `http://seu-servidor:3000`  
**Autor**: Jackson Tomelin — UniController

---

## Sumário

1. [Visão Geral](#visão-geral)
2. [Instalação e Deploy](#instalação-e-deploy)
3. [Configuração](#configuração)
4. [Autenticação](#autenticação)
5. [Endpoints da API](#endpoints-da-api)
6. [Dashboard Admin](#dashboard-admin)
7. [API Keys — Gerenciamento](#api-keys)
8. [Sites Suportados](#sites-suportados)
9. [Integração com FlareSolverr](#flaresolverr)
10. [Human Challenge (drc|1402)](#human-challenge)
11. [Exemplos de Uso](#exemplos-de-uso)
12. [Troubleshooting](#troubleshooting)

---

## Visão Geral

PX Solver é uma API para resolver challenges do **PerimeterX v6.7.9** e obter tokens `_px3` válidos. Suporta:

- Resolução HTTP de challenges PerimeterX
- Bypass de Cloudflare via FlareSolverr
- Resolução de Human Challenges (drc|1402) via Playwright
- Dashboard admin com gerenciamento de API keys
- Tracking de uso e estatísticas por cliente

### Arquitetura

```
Cliente → API (Flask) → PX Solver → PerimeterX Collector
                     ↘ FlareSolverr → Cloudflare Bypass
                     ↘ Playwright → Human Challenge
```

### Stack

- Python 3.12 + Flask
- tls-client (TLS fingerprint spoofing)
- Playwright + Chromium (human challenges)
- SQLite (API keys e tracking)
- Docker / Coolify

---

## Instalação e Deploy

### Docker (Recomendado)

```bash
git clone https://github.com/jacksontomelin/PerimeterX-Solver.git
cd PerimeterX-Solver
docker build -t px-solver .
docker run -d -p 3000:3000 \
  -v px-data:/app/data \
  -e ADMIN_TOKEN=sua-senha-admin \
  px-solver
```

### Coolify

1. Criar novo serviço com repositório GitHub
2. Build Pack: **Dockerfile**
3. Porta: **3000**
4. Adicionar volume: `/data/px-solver` → `/app/data`
5. Variáveis de ambiente (ver seção Configuração)
6. Deploy

### Local (Desenvolvimento)

```bash
pip install -r requirements.txt
playwright install --with-deps chromium
python solve.py
```

---

## Configuração

### Variáveis de Ambiente

| Variável | Obrigatória | Default | Descrição |
|----------|------------|---------|-----------|
| `PORT` | Não | `3000` | Porta do servidor |
| `ADMIN_TOKEN` | **Sim** | `pxadmin2024` | Senha do painel admin |
| `FLARESOLVERR_URL` | Não | — | URL do FlareSolverr para bypass Cloudflare |
| `BROWSER_PROXY` | Não | — | Proxy para o Playwright (residencial) |
| `RESIDENTIAL_PROXY` | Não | — | Alias para BROWSER_PROXY |
| `PX_DB_PATH` | Não | `/app/data/px_solver.db` | Caminho do banco SQLite |
| `HTTP_PROXY` | Não | — | Proxy para requisições HTTP do solver |

### Exemplo de configuração no Coolify

```
ADMIN_TOKEN=minha-senha-forte-123
FLARESOLVERR_URL=http://flaresolverr:8191
PORT=3000
```

---

## Autenticação

### Admin (Dashboard e gerenciamento)

Todas as rotas admin requerem o token de administrador:

```
Header: X-Admin-Token: sua-senha
Query:  ?admin_token=sua-senha
```

### API Key (Clientes)

Clientes usam API keys geradas pelo admin:

```
Header: X-API-Key: pxs_abc123def456...
Query:  ?api_key=pxs_abc123def456...
Body:   {"api_key": "pxs_abc123def456..."}
```

---

## Endpoints da API

### Geral

#### `GET /`

Informações do serviço e lista de endpoints.

**Response:**
```json
{
  "service": "PerimeterX Solver",
  "version": "2.1.0",
  "status": "running",
  "solver_ready": true,
  "dashboard": true
}
```

#### `GET /health`

Health check para monitoramento.

**Response:**
```json
{
  "status": "healthy",
  "solver_ready": true,
  "version": "2.1.0"
}
```

---

### Solver

#### `POST /api/solve`

Resolver um challenge PerimeterX e obter token `_px3`.

**Headers:**
```
Content-Type: application/json
X-API-Key: pxs_... (opcional, para tracking)
```

**Body:**
```json
{
  "app_id": "PX0OZADU9K",
  "ft": 221,
  "collector_uri": "https://collector-px0ozadu9k.px-cloud.net/api/v2/collector",
  "host": "https://airtable.com/login",
  "sid": "uuid-session-id",
  "vid": "uuid-visitor-id",
  "cts": "uuid-client-timestamp",
  "proxy": "user:pass@proxy.com:8080"
}
```

| Campo | Tipo | Obrigatório | Descrição |
|-------|------|------------|-----------|
| `app_id` | string | Sim | ID do PerimeterX (ex: PX0OZADU9K) |
| `ft` | integer | Sim | Fingerprint type (geralmente 221) |
| `collector_uri` | string | Sim | URL do collector PX |
| `host` | string | Sim | URL do site alvo |
| `sid` | string | Sim | Session ID (UUID) |
| `vid` | string | Sim | Visitor ID (UUID) |
| `cts` | string | Sim | Client timestamp (UUID) |
| `proxy` | string | Não | Proxy HTTP/SOCKS5 |
| `api_key` | string | Não | API key para tracking |

**Response (sucesso):**
```json
{
  "status": "success",
  "token": "1d6dab5f9baa1cec70c3fc16...",
  "time_ms": 450
}
```

**Response (erro):**
```json
{
  "status": "error",
  "message": "Failed to solve",
  "time_ms": 1200
}
```

---

### Teste de Sites

#### `GET /api/test-px?site={site}`

Detecta PerimeterX em um site e tenta resolver automaticamente.

**Query Parameters:**

| Param | Tipo | Default | Descrição |
|-------|------|---------|-----------|
| `site` | string | `crunchbase` | Nome do site para testar |
| `proxy` | string | — | Proxy para o browser (residencial) |
| `admin_token` | string | — | Token de admin |

**Sites disponíveis:** `airtable`, `fiverr`, `zillow`, `nordstrom`, `crunchbase`, `stockx`, `indeed`, `all`

**Exemplo:**
```
GET /api/test-px?site=airtable
GET /api/test-px?site=fiverr
GET /api/test-px?site=all
GET /api/test-px?site=nordstrom&proxy=user:pass@resi.com:8080
```

**Response (sucesso):**
```json
{
  "site": "airtable",
  "px_detected": true,
  "app_id": "PX0OZADU9K",
  "solve_attempt": {
    "status": "SUCCESS",
    "token": "1d6dab5f9baa1cec..."
  }
}
```

**Response (scan all):**
```json
{
  "status": "scan_complete",
  "results": {
    "airtable": {"px_detected": true, "app_id": "PX0OZADU9K"},
    "fiverr": {"px_detected": true, "app_id": "PXK3bezZfO"},
    "crunchbase": {"px_detected": false}
  }
}
```

---

## Dashboard Admin

### Acesso

```
GET /dashboard?admin_token=sua-senha
```

### Funcionalidades

- **KPIs**: Total de requests, tokens gerados, taxa de sucesso, keys ativas
- **Gráfico**: Uso dos últimos 7 dias
- **Top Sites**: Ranking dos sites mais acessados
- **API Keys**: Criar, ativar/desativar, ver limites
- **Requisições**: Log em tempo real de todas as chamadas
- **Teste PX**: Botões para testar cada site direto do dashboard
- **Tema**: Dark/Light mode toggle

---

## API Keys

### Listar Keys

```
GET /api/keys
Header: X-Admin-Token: sua-senha
```

**Response:**
```json
{
  "keys": [
    {
      "id": "a1b2c3d4",
      "key_prefix": "pxs_48f2a1b3...",
      "name": "Loja Auto Center",
      "is_active": 1,
      "daily_limit": 1000,
      "total_requests": 542,
      "total_tokens": 389,
      "created_at": "2026-08-23T07:00:00",
      "last_used_at": "2026-08-23T12:30:00"
    }
  ]
}
```

### Criar Key

```
POST /api/keys
Header: X-Admin-Token: sua-senha
Content-Type: application/json
```

**Body:**
```json
{
  "name": "Loja Auto Center",
  "daily_limit": 500,
  "expires_days": 30,
  "notes": "Plano básico"
}
```

| Campo | Tipo | Default | Descrição |
|-------|------|---------|-----------|
| `name` | string | "Unnamed Key" | Nome do cliente |
| `daily_limit` | integer | 1000 | Máximo de requests por dia |
| `rate_limit` | integer | 100 | Requests por minuto |
| `expires_days` | integer | null | Dias até expirar (null = nunca) |
| `notes` | string | "" | Observações internas |

**Response:**
```json
{
  "status": "created",
  "id": "a1b2c3d4",
  "key": "pxs_48f2a1b3c9d7e6f0a1b2c3d4e5f6a7b8c9d0e1f2",
  "prefix": "pxs_48f2a1b3",
  "name": "Loja Auto Center",
  "daily_limit": 500
}
```

> ⚠️ A `key` completa é mostrada **apenas uma vez**. Copie e guarde!

### Ativar/Desativar Key

```
POST /api/keys/{id}/toggle
Header: X-Admin-Token: sua-senha
Content-Type: application/json

{"active": false}
```

### Deletar Key

```
DELETE /api/keys/{id}
Header: X-Admin-Token: sua-senha
```

### Estatísticas por Key

```
GET /api/keys/{id}/stats
Header: X-Admin-Token: sua-senha
```

### Estatísticas Gerais

```
GET /api/stats
Header: X-Admin-Token: sua-senha
```

---

## Sites Suportados

### Resultados dos Testes (2026-08-23)

| Site | PerimeterX | App ID | Cloudflare | Token | TTL |
|------|-----------|--------|------------|-------|-----|
| **Airtable** | ✅ | PX0OZADU9K | ❌ | ✅ SUCCESS | 330s |
| **Fiverr** | ✅ | PXK3bezZfO | ✅ (bypass) | ✅ SUCCESS | 600s |
| **Zillow** | ✅ | PXHYx10rg3 | ❌ | ✅ SUCCESS | 1800s |
| **Nordstrom** | ✅ | Variável | Akamai | ❌ IP blocked | — |
| Crunchbase | ❌ | — | ✅ | N/A | — |
| StockX | ❌ | — | ✅ | N/A | — |
| Indeed | ❌ | — | ✅ | N/A | — |

### Como Adicionar um Novo Site

Editar o dicionário `SITES` em `solve.py`:

```python
SITES = {
    "meu-site": "https://www.meu-site.com",
    # ...
}
```

---

## FlareSolverr

### O que é

Serviço que bypassa proteção Cloudflare usando navegador real. Necessário para sites que combinam Cloudflare + PerimeterX (como Fiverr).

### Como Funciona

```
1. GET site.com → 403 (Cloudflare bloqueia)
2. FlareSolverr → Resolve challenge Cloudflare → cookies cf_clearance
3. GET site.com + cookies → 200 (HTML com PX detectado)
4. PX Solver → Resolve challenge PX → token _px3
```

### Configuração

```
FLARESOLVERR_URL=http://seu-flaresolverr:8191
```

### Deploy do FlareSolverr (Docker)

```bash
docker run -d -p 8191:8191 ghcr.io/flaresolverr/flaresolverr:latest
```

---

## Human Challenge

### O que é drc|1402

Quando o PerimeterX detecta atividade suspeita, retorna código `drc|1402` que requer interação humana (pressionar botão, arrastar, clicar). O solver resolve isso automaticamente usando Playwright + Chromium.

### Fluxo

```
1. request_1() → resposta com drc|1402
2. Playwright abre Chromium headless
3. Navega para o site
4. Detecta elemento de challenge (#px-captcha)
5. Executa gesto (press-and-hold, swipe, click)
6. Servidor valida → retorna _px3 token
```

### Tipos Suportados

| Tipo | Status | Descrição |
|------|--------|-----------|
| Hold and Release | ✅ | Pressionar e segurar por 3-5s |
| Swipe/Drag | ✅ | Arrastar elemento |
| Click | ✅ | Clicar em posição específica |
| Rotate | ⚠️ | Placeholder (não implementado) |

### Limitação: IP de Datacenter

Alguns sites (Nordstrom/Akamai) bloqueiam IPs de datacenter. Neste caso, é necessário proxy residencial:

```
BROWSER_PROXY=user:pass@residential-proxy.com:8080
```

Ou via query parameter:

```
GET /api/test-px?site=nordstrom&proxy=user:pass@resi.com:8080
```

---

## Exemplos de Uso

### Python

```python
import requests

# Sem API key (público)
response = requests.post("http://seu-servidor:3000/api/solve", json={
    "app_id": "PX0OZADU9K",
    "ft": 221,
    "collector_uri": "https://collector-px0ozadu9k.px-cloud.net/api/v2/collector",
    "host": "https://airtable.com/login",
    "sid": "uuid-gerado",
    "vid": "uuid-gerado",
    "cts": "uuid-gerado"
})

data = response.json()
if data["status"] == "success":
    px3_token = data["token"]
    print(f"Token: {px3_token}")
```

### Python com API Key

```python
response = requests.post(
    "http://seu-servidor:3000/api/solve",
    headers={"X-API-Key": "pxs_sua_api_key_aqui"},
    json={
        "app_id": "PX0OZADU9K",
        "ft": 221,
        "collector_uri": "https://collector-px0ozadu9k.px-cloud.net/api/v2/collector",
        "host": "https://airtable.com/login",
        "sid": "session-id",
        "vid": "visitor-id",
        "cts": "client-timestamp"
    }
)
```

### cURL

```bash
# Resolver challenge
curl -X POST http://seu-servidor:3000/api/solve \
  -H "Content-Type: application/json" \
  -H "X-API-Key: pxs_sua_key" \
  -d '{
    "app_id": "PX0OZADU9K",
    "ft": 221,
    "collector_uri": "https://collector-px0ozadu9k.px-cloud.net/api/v2/collector",
    "host": "https://airtable.com/login",
    "sid": "test-sid",
    "vid": "test-vid",
    "cts": "test-cts"
  }'

# Testar detecção
curl "http://seu-servidor:3000/api/test-px?site=airtable"

# Criar API key (admin)
curl -X POST "http://seu-servidor:3000/api/keys?admin_token=sua-senha" \
  -H "Content-Type: application/json" \
  -d '{"name": "Cliente XYZ", "daily_limit": 500}'
```

### JavaScript / Node.js

```javascript
const response = await fetch("http://seu-servidor:3000/api/solve", {
  method: "POST",
  headers: {
    "Content-Type": "application/json",
    "X-API-Key": "pxs_sua_key"
  },
  body: JSON.stringify({
    app_id: "PX0OZADU9K",
    ft: 221,
    collector_uri: "https://collector-px0ozadu9k.px-cloud.net/api/v2/collector",
    host: "https://airtable.com/login",
    sid: crypto.randomUUID(),
    vid: crypto.randomUUID(),
    cts: crypto.randomUUID()
  })
});

const data = await response.json();
console.log(data.token);
```

---

## Troubleshooting

### "Solver not ready"

```json
{"status": "error", "message": "Solver not ready: No module named 'tls_client'"}
```

**Solução**: Verificar que `requirements.txt` foi instalado no build.

### "Failed to solve" (sem token)

Possíveis causas:
1. **Fingerprints incompatíveis**: O solver usa fingerprints do Chrome 127 otimizados para Airtable. Outros sites podem precisar ajustes.
2. **drc|1402**: Site requer human challenge. Verificar se Playwright está instalado.
3. **IP bloqueado**: Site bloqueia IP de datacenter. Usar proxy residencial.

### "Host not in allowlist"

```json
{"response_body": "Host not in allowlist: collector-xxx.px-cloud.net"}
```

**Solução**: Ambiente bloqueia egress. Configurar proxy ou liberar firewall.

### Dashboard retorna 404

```json
{"status": "error", "message": "Endpoint not found"}
```

**Solução**: Verificar se `dashboard.py`, `db.py` e pasta `public/` estão no build. Checar `GET /` para ver se `"dashboard": true`.

### FlareSolverr "FAIL"

Verificar:
1. URL do FlareSolverr está correta (`FLARESOLVERR_URL`)
2. FlareSolverr está rodando e acessível
3. Testar manualmente: `curl http://flaresolverr:8191/v1 -d '{"cmd":"request.get","url":"https://google.com","maxTimeout":30000}'`

### API Key "daily_limit_exceeded"

```json
{"error": "Daily limit exceeded", "limit": 1000, "used": 1000}
```

**Solução**: Aumentar limite via dashboard ou `PUT /api/keys/{id}`.

### Banco de dados sumiu no redeploy

**Solução**: Adicionar volume persistente no Coolify:
- Source: `/data/px-solver`
- Destination: `/app/data`

---

## Estrutura do Projeto

```
PerimeterX-Solver/
├── solve.py              # Flask app principal + PX solver
├── human_challenge.py    # Playwright-based challenge solver
├── dashboard.py          # Rotas do dashboard admin
├── db.py                 # SQLite database (API keys, tracking)
├── proxy_manager.py      # Auto-detecção de proxy
├── requirements.txt      # Dependências Python
├── Dockerfile            # Build com Playwright/Chromium
├── Procfile              # Para deploy Nixpacks
├── public/
│   └── dashboard.html    # Frontend do dashboard
└── docs/
    └── API.md            # Esta documentação
```

---

## Changelog

### v2.1.0 (2026-08-23)

- Human challenge solver (drc|1402) via Playwright
- FlareSolverr integration para Cloudflare bypass
- Dashboard admin com layout RevendasDB
- API key management com limites diários
- Request tracking e estatísticas
- Proxy residencial support
- Auto-detecção de proxy
- 3/3 sites PX testados com sucesso (Airtable, Fiverr, Zillow)

### v2.0.0 (sessões anteriores)

- Refatoração de CLI para Flask web server
- tls-client com TLS fingerprint spoofing (Chrome 127)
- Endpoints: `/api/solve`, `/api/test-px`, `/health`
- Deploy Coolify com Nixpacks/Docker

---

## Licença

Projeto proprietário — UniController / Jackson Tomelin

---

*Documentação gerada em 2026-08-23*
*PX Solver v2.1.0 — UniController*
