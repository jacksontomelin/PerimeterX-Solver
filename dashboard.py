"""
Dashboard routes for PX Solver API
Admin panel + API key management + usage tracking
"""

from flask import Blueprint, request, jsonify, render_template_string
from functools import wraps
import os
import time
import logging

from db import (
    generate_api_key, validate_api_key, list_api_keys,
    toggle_api_key, delete_api_key, update_api_key,
    log_request, get_overview_stats, get_key_stats
)

logger = logging.getLogger(__name__)

dashboard_bp = Blueprint('dashboard', __name__)

ADMIN_TOKEN = os.environ.get("ADMIN_TOKEN", "pxadmin2024")


def admin_required(f):
    """Middleware: require admin token"""
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get("X-Admin-Token") or request.args.get("admin_token")
        if token != ADMIN_TOKEN:
            return jsonify({"error": "Unauthorized", "message": "Set X-Admin-Token header or ?admin_token="}), 401
        return f(*args, **kwargs)
    return decorated


def api_key_required(f):
    """Middleware: require valid API key"""
    @wraps(f)
    def decorated(*args, **kwargs):
        api_key = request.headers.get("X-API-Key") or request.args.get("api_key")
        if not api_key:
            return jsonify({"error": "Missing API key", "message": "Set X-API-Key header or ?api_key="}), 401
        
        key_info = validate_api_key(api_key)
        if not key_info:
            return jsonify({"error": "Invalid or expired API key"}), 403
        if key_info.get("error") == "daily_limit_exceeded":
            return jsonify({"error": "Daily limit exceeded", "limit": key_info["limit"], "used": key_info["used"]}), 429
        
        request.api_key_info = key_info
        return f(*args, **kwargs)
    return decorated


# ============================================================
# DASHBOARD HTML
# ============================================================

@dashboard_bp.route('/dashboard')
@admin_required
def dashboard_page():
    """Admin dashboard page"""
    stats = get_overview_stats()
    keys = list_api_keys()
    admin_token = request.args.get("admin_token", "")
    
    return render_template_string(DASHBOARD_HTML, stats=stats, keys=keys, admin_token=admin_token)


# ============================================================
# API KEY MANAGEMENT ENDPOINTS
# ============================================================

@dashboard_bp.route('/api/keys', methods=['GET'])
@admin_required
def api_keys_list():
    """List all API keys"""
    return jsonify({"keys": list_api_keys()})


@dashboard_bp.route('/api/keys', methods=['POST'])
@admin_required
def api_keys_create():
    """Create new API key"""
    data = request.get_json() or {}
    name = data.get("name", "Unnamed Key")
    daily_limit = data.get("daily_limit", 1000)
    rate_limit = data.get("rate_limit", 100)
    expires_days = data.get("expires_days")
    notes = data.get("notes", "")
    
    result = generate_api_key(name, daily_limit, rate_limit, expires_days, notes)
    return jsonify({"status": "created", **result}), 201


@dashboard_bp.route('/api/keys/<key_id>', methods=['PUT'])
@admin_required
def api_keys_update(key_id):
    """Update API key"""
    data = request.get_json() or {}
    update_api_key(key_id, **data)
    return jsonify({"status": "updated"})


@dashboard_bp.route('/api/keys/<key_id>', methods=['DELETE'])
@admin_required
def api_keys_delete(key_id):
    """Delete API key"""
    delete_api_key(key_id)
    return jsonify({"status": "deleted"})


@dashboard_bp.route('/api/keys/<key_id>/toggle', methods=['POST'])
@admin_required
def api_keys_toggle(key_id):
    """Toggle API key active/inactive"""
    data = request.get_json() or {}
    active = data.get("active", True)
    toggle_api_key(key_id, active)
    return jsonify({"status": "toggled", "active": active})


@dashboard_bp.route('/api/keys/<key_id>/stats', methods=['GET'])
@admin_required
def api_keys_stats(key_id):
    """Get stats for specific API key"""
    return jsonify(get_key_stats(key_id))


# ============================================================
# STATS ENDPOINTS
# ============================================================

@dashboard_bp.route('/api/stats', methods=['GET'])
@admin_required
def api_stats():
    """Get overview statistics"""
    return jsonify(get_overview_stats())


# ============================================================
# DASHBOARD HTML TEMPLATE
# ============================================================

DASHBOARD_HTML = """
<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>PX Solver — Dashboard</title>
<style>
  :root {
    --bg: #0a0e17; --surface: #111827; --surface2: #1a2332;
    --border: #1e2d3d; --text: #e2e8f0; --text2: #94a3b8;
    --accent: #22d3ee; --accent2: #06b6d4; --green: #34d399;
    --red: #f87171; --yellow: #fbbf24; --purple: #a78bfa;
    --radius: 10px;
  }
  * { margin:0; padding:0; box-sizing:border-box; }
  body { background:var(--bg); color:var(--text); font-family:'Inter',system-ui,sans-serif; }
  
  .header {
    background:linear-gradient(135deg, #0f172a 0%, #1e1b4b 100%);
    border-bottom:1px solid var(--border);
    padding:20px 32px; display:flex; align-items:center; justify-content:space-between;
  }
  .header h1 { font-size:20px; font-weight:700; letter-spacing:-0.5px; }
  .header h1 span { color:var(--accent); }
  .header .badge {
    background:var(--green); color:#000; font-size:11px; font-weight:700;
    padding:4px 10px; border-radius:20px; letter-spacing:0.5px;
  }
  
  .container { max-width:1200px; margin:0 auto; padding:24px; }
  
  .stats-grid {
    display:grid; grid-template-columns:repeat(auto-fit,minmax(170px,1fr));
    gap:14px; margin-bottom:28px;
  }
  .stat-card {
    background:var(--surface); border:1px solid var(--border);
    border-radius:var(--radius); padding:18px;
  }
  .stat-card .label { font-size:11px; color:var(--text2); text-transform:uppercase; letter-spacing:1px; margin-bottom:6px; }
  .stat-card .value { font-size:28px; font-weight:700; letter-spacing:-1px; }
  .stat-card .value.accent { color:var(--accent); }
  .stat-card .value.green { color:var(--green); }
  .stat-card .value.yellow { color:var(--yellow); }
  .stat-card .value.purple { color:var(--purple); }
  
  .section { margin-bottom:28px; }
  .section-title {
    font-size:14px; font-weight:600; color:var(--text2);
    text-transform:uppercase; letter-spacing:1.5px; margin-bottom:14px;
    display:flex; align-items:center; justify-content:space-between;
  }
  
  .table-wrap {
    background:var(--surface); border:1px solid var(--border);
    border-radius:var(--radius); overflow:hidden;
  }
  table { width:100%; border-collapse:collapse; font-size:13px; }
  th { background:var(--surface2); color:var(--text2); font-weight:600;
       padding:10px 14px; text-align:left; font-size:11px; text-transform:uppercase; letter-spacing:0.5px; }
  td { padding:10px 14px; border-top:1px solid var(--border); }
  tr:hover td { background:var(--surface2); }
  
  .badge-sm { padding:3px 8px; border-radius:4px; font-size:11px; font-weight:600; }
  .badge-green { background:#065f4620; color:var(--green); }
  .badge-red { background:#7f1d1d20; color:var(--red); }
  .badge-yellow { background:#78350f20; color:var(--yellow); }
  .badge-cyan { background:#164e6320; color:var(--accent); }
  
  .key-text { font-family:'JetBrains Mono',monospace; font-size:12px; color:var(--accent); }
  
  .btn {
    padding:8px 16px; border-radius:6px; border:none; cursor:pointer;
    font-size:12px; font-weight:600; transition:0.15s;
  }
  .btn-accent { background:var(--accent); color:#000; }
  .btn-accent:hover { background:var(--accent2); }
  .btn-red { background:transparent; border:1px solid var(--red); color:var(--red); }
  .btn-red:hover { background:var(--red); color:#fff; }
  .btn-sm { padding:4px 10px; font-size:11px; }
  
  .modal-bg {
    position:fixed; inset:0; background:rgba(0,0,0,0.7); display:none;
    align-items:center; justify-content:center; z-index:100;
  }
  .modal-bg.active { display:flex; }
  .modal {
    background:var(--surface); border:1px solid var(--border);
    border-radius:12px; padding:28px; width:420px; max-width:95vw;
  }
  .modal h3 { margin-bottom:18px; font-size:16px; }
  .modal label { display:block; font-size:12px; color:var(--text2); margin-bottom:4px; margin-top:12px; }
  .modal input, .modal textarea {
    width:100%; padding:8px 12px; background:var(--surface2); border:1px solid var(--border);
    border-radius:6px; color:var(--text); font-size:13px; outline:none;
  }
  .modal input:focus { border-color:var(--accent); }
  .modal .actions { margin-top:20px; display:flex; gap:10px; justify-content:flex-end; }
  
  .chart-bar-wrap { display:flex; align-items:flex-end; gap:4px; height:80px; margin-top:8px; }
  .chart-bar {
    flex:1; background:var(--accent); border-radius:3px 3px 0 0;
    min-width:12px; position:relative; transition:0.3s;
  }
  .chart-bar:hover { opacity:0.8; }
  .chart-bar .tip {
    position:absolute; top:-22px; left:50%; transform:translateX(-50%);
    font-size:10px; color:var(--text2); white-space:nowrap; display:none;
  }
  .chart-bar:hover .tip { display:block; }
  .chart-labels { display:flex; gap:4px; margin-top:4px; }
  .chart-labels span { flex:1; text-align:center; font-size:9px; color:var(--text2); }
  
  .key-reveal {
    background:var(--surface2); border:1px solid var(--accent);
    border-radius:8px; padding:14px; margin-top:12px; word-break:break-all;
    font-family:'JetBrains Mono',monospace; font-size:13px; color:var(--green);
  }
  
  @media(max-width:640px) {
    .stats-grid { grid-template-columns:repeat(2,1fr); }
    .container { padding:14px; }
    table { font-size:11px; }
    th, td { padding:8px 10px; }
  }
</style>
</head>
<body>

<div class="header">
  <h1><span>PX</span> Solver — Admin Dashboard</h1>
  <span class="badge">v2.1.0 LIVE</span>
</div>

<div class="container">

  <!-- STATS -->
  <div class="stats-grid">
    <div class="stat-card">
      <div class="label">Total Requests</div>
      <div class="value accent">{{ stats.total_requests }}</div>
    </div>
    <div class="stat-card">
      <div class="label">Tokens Gerados</div>
      <div class="value green">{{ stats.total_tokens }}</div>
    </div>
    <div class="stat-card">
      <div class="label">Taxa de Sucesso</div>
      <div class="value yellow">{{ stats.success_rate }}%</div>
    </div>
    <div class="stat-card">
      <div class="label">Keys Ativas</div>
      <div class="value purple">{{ stats.active_keys }}</div>
    </div>
    <div class="stat-card">
      <div class="label">Hoje — Requests</div>
      <div class="value accent">{{ stats.today_requests }}</div>
    </div>
    <div class="stat-card">
      <div class="label">Hoje — Tokens</div>
      <div class="value green">{{ stats.today_tokens }}</div>
    </div>
  </div>

  <!-- CHART -->
  <div class="section">
    <div class="section-title">Últimos 7 dias</div>
    <div class="stat-card">
      <div class="chart-bar-wrap">
        {% set max_val = stats.weekly|map(attribute='reqs')|max if stats.weekly else 1 %}
        {% for day in stats.weekly %}
        <div class="chart-bar" style="height:{{ (day.reqs / (max_val if max_val > 0 else 1) * 100)|int }}%">
          <span class="tip">{{ day.reqs }} req / {{ day.tokens }} tok</span>
        </div>
        {% endfor %}
        {% if not stats.weekly %}
        <div style="color:var(--text2);font-size:12px;padding:20px;">Sem dados ainda</div>
        {% endif %}
      </div>
      <div class="chart-labels">
        {% for day in stats.weekly %}
        <span>{{ day.date[5:] }}</span>
        {% endfor %}
      </div>
    </div>
  </div>

  <!-- API KEYS -->
  <div class="section">
    <div class="section-title">
      API Keys
      <button class="btn btn-accent" onclick="openModal()">+ Nova Key</button>
    </div>
    <div class="table-wrap">
      <table>
        <tr>
          <th>Nome</th><th>Prefixo</th><th>Requests</th><th>Tokens</th>
          <th>Limite/dia</th><th>Status</th><th>Ações</th>
        </tr>
        {% for k in keys %}
        <tr>
          <td><strong>{{ k.name }}</strong></td>
          <td><span class="key-text">{{ k.key_prefix }}...</span></td>
          <td>{{ k.total_requests }}</td>
          <td>{{ k.total_tokens }}</td>
          <td>{{ k.daily_limit }}</td>
          <td>
            {% if k.is_active %}
            <span class="badge-sm badge-green">Ativa</span>
            {% else %}
            <span class="badge-sm badge-red">Inativa</span>
            {% endif %}
          </td>
          <td>
            <button class="btn btn-sm {% if k.is_active %}btn-red{% else %}btn-accent{% endif %}"
                    onclick="toggleKey('{{ k.id }}', {{ 'false' if k.is_active else 'true' }})">
              {{ 'Desativar' if k.is_active else 'Ativar' }}
            </button>
          </td>
        </tr>
        {% endfor %}
        {% if not keys %}
        <tr><td colspan="7" style="text-align:center;color:var(--text2);padding:30px;">Nenhuma API key criada</td></tr>
        {% endif %}
      </table>
    </div>
  </div>

  <!-- TOP SITES -->
  <div class="section">
    <div class="section-title">Sites Mais Acessados</div>
    <div class="table-wrap">
      <table>
        <tr><th>Site</th><th>Requests</th><th>Tokens</th><th>Taxa</th></tr>
        {% for s in stats.top_sites %}
        <tr>
          <td><strong>{{ s.site or 'N/A' }}</strong></td>
          <td>{{ s.total }}</td>
          <td>{{ s.tokens or 0 }}</td>
          <td>
            {% set rate = ((s.tokens or 0) / s.total * 100)|round(1) if s.total > 0 else 0 %}
            <span class="badge-sm {% if rate > 50 %}badge-green{% elif rate > 0 %}badge-yellow{% else %}badge-red{% endif %}">
              {{ rate }}%
            </span>
          </td>
        </tr>
        {% endfor %}
        {% if not stats.top_sites %}
        <tr><td colspan="4" style="text-align:center;color:var(--text2);padding:30px;">Sem dados ainda</td></tr>
        {% endif %}
      </table>
    </div>
  </div>

  <!-- RECENT REQUESTS -->
  <div class="section">
    <div class="section-title">Últimas Requisições</div>
    <div class="table-wrap">
      <table>
        <tr><th>Hora</th><th>Site</th><th>Key</th><th>Status</th><th>Token</th><th>Tempo</th></tr>
        {% for r in stats.recent_requests %}
        <tr>
          <td style="font-size:11px;color:var(--text2)">{{ r.timestamp[11:19] if r.timestamp else '' }}</td>
          <td>{{ r.site or 'N/A' }}</td>
          <td><span class="key-text">{{ r.key_name or 'public' }}</span></td>
          <td>
            <span class="badge-sm {% if r.status == 'SUCCESS' %}badge-green{% else %}badge-yellow{% endif %}">
              {{ r.status }}
            </span>
          </td>
          <td>{{ '✅' if r.token_obtained else '—' }}</td>
          <td style="font-size:11px;color:var(--text2)">{{ r.response_time_ms or '—' }}ms</td>
        </tr>
        {% endfor %}
        {% if not stats.recent_requests %}
        <tr><td colspan="6" style="text-align:center;color:var(--text2);padding:30px;">Sem requisições ainda</td></tr>
        {% endif %}
      </table>
    </div>
  </div>

</div>

<!-- MODAL: New API Key -->
<div class="modal-bg" id="newKeyModal">
  <div class="modal">
    <h3>Nova API Key</h3>
    <label>Nome do cliente</label>
    <input id="keyName" placeholder="Ex: Loja Auto Center">
    <label>Limite diário</label>
    <input id="keyLimit" type="number" value="1000">
    <label>Expirar em (dias, vazio = nunca)</label>
    <input id="keyExpires" type="number" placeholder="30">
    <label>Notas</label>
    <textarea id="keyNotes" rows="2" placeholder="Observações..."></textarea>
    <div id="keyResult"></div>
    <div class="actions">
      <button class="btn btn-red" onclick="closeModal()">Cancelar</button>
      <button class="btn btn-accent" onclick="createKey()">Criar Key</button>
    </div>
  </div>
</div>

<script>
const ADMIN = '{{ admin_token }}';
const BASE = window.location.origin;

function openModal() { document.getElementById('newKeyModal').classList.add('active'); }
function closeModal() {
  document.getElementById('newKeyModal').classList.remove('active');
  document.getElementById('keyResult').innerHTML = '';
}

async function createKey() {
  const res = await fetch(BASE + '/api/keys?admin_token=' + ADMIN, {
    method:'POST', headers:{'Content-Type':'application/json'},
    body: JSON.stringify({
      name: document.getElementById('keyName').value,
      daily_limit: parseInt(document.getElementById('keyLimit').value) || 1000,
      expires_days: parseInt(document.getElementById('keyExpires').value) || null,
      notes: document.getElementById('keyNotes').value,
    })
  });
  const data = await res.json();
  if (data.key) {
    document.getElementById('keyResult').innerHTML =
      '<div class="key-reveal">⚠️ Copie agora (não será mostrada novamente):<br><br><strong>' + data.key + '</strong></div>';
    setTimeout(() => location.reload(), 8000);
  }
}

async function toggleKey(id, active) {
  await fetch(BASE + '/api/keys/' + id + '/toggle?admin_token=' + ADMIN, {
    method:'POST', headers:{'Content-Type':'application/json'},
    body: JSON.stringify({active})
  });
  location.reload();
}
</script>
</body>
</html>
"""
