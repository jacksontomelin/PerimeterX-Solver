# 🎉 PerimeterX Solver v2.1.0 - Human Challenge Support

**Data de release**: 2026-08-23  
**Status**: Production Ready  
**Commit**: `f8f5941`

---

## ✨ O que é novo?

### 🎯 Human Challenge Solver (drc|1402)

O PerimeterX v6.7.9 retorna `drc|1402` quando precisa de um **human challenge visual** — um desafio que requer um navegador real para resolver. A partir da v2.1.0, o **PerimeterX Solver resolve automaticamente** esses desafios usando **Playwright**.

#### Tipos de desafios suportados:

- ✅ **Hold and Release** - Pressione e segure por X segundos (padrão)
- ✅ **Swipe** - Arraste mouse de ponto A para ponto B
- ✅ **Click** - Clique em coordenada específica
- ⚠️ **Rotate** - Placeholder (não implementado)

---

## 🔧 Mudanças técnicas

### Novos arquivos

| Arquivo | Linhas | Descrição |
|---------|--------|-----------|
| `human_challenge.py` | 450+ | Classe HumanChallengeSolver com Playwright |
| `HUMAN_CHALLENGE_GUIDE.md` | 250+ | Documentação completa do solver |
| `example_human_challenge.py` | 300+ | 5 exemplos de uso (sync, async, reuse, debug) |
| `install-playwright.sh` | 30 | Script para instalar Playwright e browsers |

### Arquivos modificados

| Arquivo | Mudanças | Descrição |
|---------|----------|-----------|
| `solve.py` | +50 linhas | Integração de detecção e handling de drc\|1402 |
| `requirements.txt` | +1 linha | Adicionado `playwright>=1.40.0` |

### Stats

```
 6 files changed, 1123 insertions(+), 3 deletions(-)
 
 human_challenge.py             450 lines (novo)
 example_human_challenge.py     300 lines (novo)
 HUMAN_CHALLENGE_GUIDE.md       250 lines (novo)
 solve.py                        +50 lines
 install-playwright.sh            30 lines (novo)
 requirements.txt                 +1 line
```

---

## 🚀 Como usar

### 1. Instalação

```bash
# Instalar dependências
pip install -r requirements.txt

# Instalar Playwright e browsers
bash install-playwright.sh
```

### 2. Uso automático (recomendado)

O solver detecta automaticamente `drc|1402` e resolve:

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
)

token = solver.solve()  # ✅ Detecta e resolve drc|1402 automaticamente!
```

### 3. Uso manual

Para mais controle, use diretamente:

```python
from human_challenge import solve_human_challenge_sync

# Síncrono (mais simples)
success, token = solve_human_challenge_sync(
    url="https://site.com/login",
    proxy=None,
    headless=True,
    timeout_ms=30000
)

# Assíncrono (melhor performance)
import asyncio
from human_challenge import solve_human_challenge

async def resolver():
    success, token = await solve_human_challenge(
        url="https://site.com/login",
        proxy="proxy.com:8080"
    )

asyncio.run(resolver())
```

---

## 📊 Fluxo de detecção

```
PXSolver.solve()
    │
    ├─ request_1() → PerimeterX response
    │
    ├─ Detectar "drc|1402" na resposta?
    │   │
    │   ├─ SIM → HumanChallengeSolver + Playwright
    │   │         ├─ Abrir navegador Chromium
    │   │         ├─ Extrair dados do challenge
    │   │         ├─ Executar gesto (hold/swipe/click)
    │   │         └─ Retornar _px3 token ✅
    │   │
    │   └─ NÃO → solve_request() normal (HTTP)
    │
    └─ Retornar _px3 token
```

---

## 🎮 Exemplos de uso

### Exemplo 1: Síncrono (mais simples)

```python
from human_challenge import solve_human_challenge_sync

success, token = solve_human_challenge_sync(
    url="https://example.com/login",
    headless=True
)

if success:
    print(f"✅ Resolvido! Token: {token}")
```

### Exemplo 2: Assíncrono com debug

```python
import asyncio
from human_challenge import HumanChallengeSolver

async def resolver_com_debug():
    solver = HumanChallengeSolver(
        headless=False,  # Mostra janela do navegador
        slow_motion_ms=500  # Adiciona delay para debug
    )
    
    try:
        await solver.launch_browser()
        success, token = await solver.solve_challenge("https://site.com")
        
        if success:
            print(f"✅ Token: {token}")
    finally:
        await solver.close()

asyncio.run(resolver_com_debug())
```

### Exemplo 3: Reutilizar contexto

```python
async def resolver_multiplas_urls():
    solver = HumanChallengeSolver()
    await solver.launch_browser()
    
    urls = [
        "https://site1.com/login",
        "https://site2.com/checkout",
        "https://site3.com/protected"
    ]
    
    for url in urls:
        success, token = await solver.solve_challenge(url)
        if success:
            print(f"✅ {url}: {token[:30]}...")
    
    await solver.close()

asyncio.run(resolver_multiplas_urls())
```

---

## 🔍 Debugging

### Ver logs detalhados

```python
import logging

logging.basicConfig(level=logging.DEBUG)
# Agora você verá cada ação: mouse position, challenge type, etc.
```

### Usar headless=False para visualizar

```python
solver = HumanChallengeSolver(headless=False)
# Abre janela do Chromium - pode ver o desafio sendo resolvido
```

### Extrair dados do challenge

```python
challenge = await solver._extract_challenge_data()
# Retorna: ChallengeData(type='hold_and_release', duration_ms=3000, ...)
```

---

## ⚡ Performance

| Operação | Tempo | Notas |
|----------|-------|-------|
| Launcher browser | ~2s | Uma vez por sessão |
| Navegar para URL | ~3-5s | Depende da rede |
| Resolver challenge | ~4-6s | Hold-and-release típico |
| Total por URL | ~9-13s | HTTP puro: ~200ms |

**Impacto**: Human challenges são ~50x mais lentos que HTTP puro, mas necessários para contornar defesas visuais.

---

## 🔐 Segurança

- ✅ Playwright roda em headless (sem GUI)
- ✅ Proxy support (HTTP, SOCKS5)
- ✅ User-Agent spoofing (Chrome 127)
- ✅ TLS fingerprint matching (tls-client + Playwright)
- ✅ Não salva cookies ou histórico
- ✅ Contexto isolado por instância

---

## 📚 Documentação

- **[HUMAN_CHALLENGE_GUIDE.md](./HUMAN_CHALLENGE_GUIDE.md)** - Guia completo
- **[example_human_challenge.py](./example_human_challenge.py)** - 5 exemplos práticos
- **[README.md](./README.md)** - Documentação geral do solver

---

## 🐛 Changelog

### v2.1.0 (2026-08-23)
- ✨ Novo módulo human_challenge.py com HumanChallengeSolver
- ✨ Auto-detecção de drc|1402 em respostas PerimeterX
- ✨ Integração Playwright para resolução visual
- ✨ Suporte para hold-and-release, swipe, click
- 📚 Documentação completa (HUMAN_CHALLENGE_GUIDE.md)
- 🧪 5 exemplos de uso (example_human_challenge.py)
- 📦 Script de instalação (install-playwright.sh)

### v2.0.0 (anterior)
- Refatoração completa do solver
- Type hints 100%
- Logging estruturado
- Error handling robusto
- Flask web server

---

## 🚀 Próximas features

- [ ] Rotate challenge solver
- [ ] WebSocket challenge support
- [ ] Challenge data caching
- [ ] Multi-browser support (Firefox, WebKit)
- [ ] Challenge analytics/logging
- [ ] Proxy rotation support

---

## 📞 Suporte

Se encontrar problemas:

1. **Verificar instalação**: `bash install-playwright.sh`
2. **Verificar logs**: `logging.basicConfig(level=logging.DEBUG)`
3. **Testar exemplo**: `python example_human_challenge.py`
4. **Usar headless=False**: Ver o que está acontecendo visualmente

---

## 📝 Licença

MIT License - veja [LICENSE](./LICENSE)

---

**Desenvolvido com ❤️ por Jackson Tomelin**  
**PerimeterX Solver v2.1.0** | Produção | Agosto 2026
