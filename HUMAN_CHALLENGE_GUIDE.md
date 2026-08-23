# PerimeterX Human Challenge Solver (drc|1402)

## 🎯 O que é drc|1402?

O `drc|1402` é um código retornado pelo PerimeterX v6.7.9 indicando um **human challenge visual**. Significa que o servidor quer confirmação humana através de um desafio interativo que **requer um navegador real** — não pode ser resolvido só com HTTP requests.

### Exemplos de desafios drc|1402:

1. **Hold and Release** (mais comum)
   - Usuário pressiona mouse button
   - Segura por X segundos
   - Libera
   - Movimento é enviado ao servidor

2. **Swipe**
   - Arrastar mouse de ponto A para ponto B
   - Movimento contínuo é rastreado

3. **Click**
   - Clicar em área específica da tela
   - Coordenadas validadas

4. **Rotate** (menos comum)
   - Girar imagem até posição específica

## ⚙️ Instalação

### Pré-requisitos
- Python 3.8+
- pip

### 1. Instalar dependências base

```bash
pip install -r requirements.txt
```

### 2. Instalar Playwright e browsers

```bash
bash install-playwright.sh
```

Ou manualmente:

```bash
pip install playwright>=1.40.0
playwright install chromium
```

## 🚀 Uso

### Uso Síncrono (Recomendado para scripts simples)

```python
from human_challenge import solve_human_challenge_sync

success, token = solve_human_challenge_sync(
    url="https://site-com-px.com/login",
    proxy=None,  # Seu proxy se tiver
    headless=True,
    timeout_ms=30000
)

if success:
    print(f"Token obtido: {token}")
else:
    print("Falha ao resolver challenge")
```

### Uso Assíncrono (Para aplicações complexas)

```python
import asyncio
from human_challenge import solve_human_challenge

async def main():
    success, token = await solve_human_challenge(
        url="https://site.com",
        proxy="proxy.com:8080",
        headless=True
    )

asyncio.run(main())
```

### Integração com PXSolver

O solver automaticamente detecta `drc|1402` e tenta resolver:

```python
from solve import PXSolver

solver = PXSolver(
    app_id="PX0OZADU9K",
    ft=221,
    collector_uri="https://collector.px-cloud.net/...",
    host="https://site.com",
    sid="...",
    vid="...",
    cts="...",
    proxy=None
)

token = solver.solve()  # Detecta e resolve automaticamente
```

## 📊 Como funciona

### Fluxo de detecção drc|1402:

```
1. PXSolver.solve()
   ↓
2. request_1() → PerimeterX response
   ↓
3. Verificar se resposta contém "drc|1402"
   ↓
4. SIM → Usar HumanChallengeSolver (Playwright)
   NÃO → Continuar com solve_request() normal
   ↓
5. Playwright abre navegador, extrai challenge do DOM
   ↓
6. Detecta tipo (hold, swipe, click, rotate)
   ↓
7. Executa gesto (press/hold, move mouse, click)
   ↓
8. Aguarda resposta do servidor
   ↓
9. Retorna _px3 token
```

### Detecção de challenge no PerimeterX response:

```python
is_human_challenge, drc_code = PXSolver.detect_human_challenge(response)

# Retorna:
# is_human_challenge = True/False
# drc_code = "1402" ou outro código
```

## 🔍 Debugging

### Ver logs detalhados:

```python
import logging

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Agora você verá:
# - Timestamp de cada ação
# - Coordenadas de mouse
# - Dados do challenge extraído
# - Sucessos/falhas
```

### Usar headless=False para ver o navegador:

```python
success, token = solve_human_challenge_sync(
    url="https://site.com",
    headless=False  # Mostra janela do navegador
)
```

### Extrair dados do challenge manualmente:

```python
from human_challenge import HumanChallengeSolver
import asyncio

async def debug():
    solver = HumanChallengeSolver(headless=False)
    await solver.launch_browser()
    await solver.create_context()
    
    await solver.page.goto("https://site.com")
    
    # Extrair dados
    challenge = await solver._extract_challenge_data()
    
    if challenge:
        print(f"Tipo: {challenge.challenge_type.value}")
        print(f"Duração: {challenge.duration_ms}ms")
        print(f"Posição: {challenge.start_x}, {challenge.start_y}")

asyncio.run(debug())
```

## 🎮 Tipos de challenges resolvidos

| Tipo | Status | Descrição |
|------|--------|-----------|
| Hold and Release | ✅ Completo | Pressionar e segurer por X ms |
| Swipe | ✅ Completo | Arrastar mouse de A para B |
| Click | ✅ Completo | Clicar em coordenada específica |
| Rotate | ⚠️ Placeholder | Não implementado ainda |

## ⚠️ Limitações e considerações

1. **Playwright necessário**: Sem Playwright instalado, fallback para solve_request() normal
2. **Timeout**: Default 30 segundos por challenge
3. **Proxy**: Você pode usar proxy HTTP/SOCKS5
4. **Headless**: Se headless=True, nenhuma janela aparece (melhor para servidores)
5. **Performance**: Resolver com navegador real é mais lento que HTTP puro

## 🔗 Proxy support

```python
# Com proxy HTTP
success, token = solve_human_challenge_sync(
    url="https://site.com",
    proxy="http://proxy.com:8080",
    headless=True
)

# Com proxy SOCKS5
success, token = solve_human_challenge_sync(
    url="https://site.com",
    proxy="socks5://proxy.com:1080",
    headless=True
)
```

## 📝 Ambiente (ENV)

Você pode configurar via `.env`:

```env
# .env
PX_HEADLESS=true
PX_TIMEOUT_MS=30000
PX_PROXY=http://proxy:8080
```

## 🐛 Troubleshooting

### "Playwright not installed"
```bash
pip install playwright>=1.40.0
playwright install chromium
```

### "Timeout exceeded while solving"
- Aumentar `timeout_ms` (padrão 30000ms)
- Verificar conexão de rede
- Tentar sem proxy se usando

### "Cannot extract challenge data"
- PerimeterX pode ter mudado estrutura do DOM
- Usar `headless=False` para ver o que está acontecendo
- Verificar se é realmente um challenge visual

### "Token not found after solving"
- Challenge foi resolvido mas token não foi retornado
- Pode ser variação de PerimeterX
- Verificar se navegador permaneceu na página correta

## 📚 Referências

- [PerimeterX Documentation](https://docs.perimeterx.com/)
- [Playwright Python Docs](https://playwright.dev/python/)
- [PerimeterX Challenge Types](https://docs.perimeterx.com/pxcloud/docs/human-challenge)

## 📝 Changelog

### v2.0.0 - Human Challenge Support
- ✅ Detecção automática de drc|1402
- ✅ Playwright integration
- ✅ Hold and Release solver
- ✅ Swipe solver
- ✅ Click solver
- ⚠️ Rotate solver (placeholder)

---

**Última atualização**: 2026-08-23
**Status**: Produção pronta (PerimeterX v6.7.9+)
