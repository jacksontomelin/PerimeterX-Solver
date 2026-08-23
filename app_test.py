#!/usr/bin/env python3
"""
PerimeterX Solver - Aplicação com Endpoints de Teste
Acesse: http://seu-url/test para ver todos os testes
"""

from flask import Flask, request, jsonify
import json
from datetime import datetime
from solve import PXSolver
import logging

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ====== ENDPOINTS DE TESTE ======

@app.route('/', methods=['GET'])
def home():
    """Página principal com informações"""
    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>PerimeterX Solver</title>
        <style>
            body { font-family: Arial; margin: 20px; }
            .test-link { display: block; margin: 10px 0; padding: 10px; background: #f0f0f0; border-radius: 5px; }
            .endpoint { background: #e3f2fd; padding: 15px; margin: 10px 0; border-radius: 5px; }
            code { background: #f5f5f5; padding: 2px 5px; border-radius: 3px; }
        </style>
    </head>
    <body>
        <h1>✅ PerimeterX Solver</h1>
        <p>Aplicação funcionando no Coolify!</p>
        
        <h2>🧪 Endpoints de Teste</h2>
        <div class="endpoint">
            <p><strong>/health</strong> - Health check</p>
            <a href="/health" class="test-link">Testar →</a>
        </div>
        
        <div class="endpoint">
            <p><strong>/status</strong> - Status da aplicação</p>
            <a href="/status" class="test-link">Testar →</a>
        </div>
        
        <div class="endpoint">
            <p><strong>/api/solve</strong> - Solver API (POST)</p>
            <p>Método: POST</p>
            <p>Payload:</p>
            <code>{
  "app_id": "PX0OZADU9K",
  "ft": 221,
  "collector_uri": "https://...",
  "host": "https://airtable.com",
  "sid": "...",
  "vid": "...",
  "cts": "..."
}</code>
            <a href="/test-solver" class="test-link">Testar com dados de exemplo →</a>
        </div>
        
        <div class="endpoint">
            <p><strong>/info</strong> - Informações da aplicação</p>
            <a href="/info" class="test-link">Testar →</a>
        </div>
        
        <h2>📝 Instruções</h2>
        <p>1. Acesse <code>/health</code> para verificar se está tudo OK</p>
        <p>2. Acesse <code>/status</code> para ver o status</p>
        <p>3. Acesse <code>/info</code> para ver informações</p>
        <p>4. Use <code>/api/solve</code> para resolver desafios do PerimeterX</p>
    </body>
    </html>
    """
    return html, 200, {'Content-Type': 'text/html; charset=utf-8'}

@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({
        "status": "healthy",
        "service": "PerimeterX Solver",
        "timestamp": datetime.now().isoformat(),
        "version": "2.0.0"
    }), 200

@app.route('/status', methods=['GET'])
def status():
    """Status endpoint"""
    return jsonify({
        "status": "running",
        "app": "PerimeterX Solver v2.0.0",
        "framework": "Flask",
        "timestamp": datetime.now().isoformat(),
        "endpoints": {
            "home": "/",
            "health": "/health",
            "status": "/status",
            "info": "/info",
            "solve": "/api/solve (POST)",
            "test": "/test-solver"
        }
    }), 200

@app.route('/info', methods=['GET'])
def info():
    """Informações da aplicação"""
    return jsonify({
        "name": "PerimeterX Solver",
        "version": "2.0.0",
        "description": "PerimeterX v6.7.9 Challenge Solver",
        "features": [
            "TLS fingerprint spoofing (Chrome 127)",
            "PX fingerprinting",
            "Cookie extraction",
            "MD5-based PC hash calculation"
        ],
        "endpoints_available": [
            "GET  /",
            "GET  /health",
            "GET  /status",
            "GET  /info",
            "POST /api/solve"
        ],
        "timestamp": datetime.now().isoformat()
    }), 200

@app.route('/api/solve', methods=['POST'])
def solve_api():
    """API endpoint para resolver desafios PerimeterX"""
    try:
        data = request.get_json()
        
        logger.info(f"Received solve request for app_id: {data.get('app_id')}")
        
        # Validar dados
        required_fields = ['app_id', 'ft', 'collector_uri', 'host', 'sid', 'vid', 'cts']
        missing = [f for f in required_fields if f not in data]
        
        if missing:
            return jsonify({
                "status": "error",
                "message": f"Missing fields: {', '.join(missing)}",
                "required_fields": required_fields
            }), 400
        
        # Criar solver
        solver = PXSolver(
            app_id=data['app_id'],
            ft=data['ft'],
            collector_uri=data['collector_uri'],
            host=data['host'],
            sid=data['sid'],
            vid=data['vid'],
            cts=data['cts'],
            proxy=data.get('proxy')
        )
        
        # Resolver
        token = solver.solve()
        
        if token:
            return jsonify({
                "status": "success",
                "token": token,
                "timestamp": datetime.now().isoformat()
            }), 200
        else:
            return jsonify({
                "status": "error",
                "message": "Failed to solve challenge",
                "timestamp": datetime.now().isoformat()
            }), 500
            
    except Exception as e:
        logger.error(f"Error in solve_api: {str(e)}")
        return jsonify({
            "status": "error",
            "message": str(e),
            "timestamp": datetime.now().isoformat()
        }), 500

@app.route('/test-solver', methods=['GET'])
def test_solver():
    """Endpoint de teste com dados de exemplo"""
    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Teste do Solver</title>
        <style>
            body { font-family: Arial; margin: 20px; }
            form { max-width: 600px; }
            input, textarea { width: 100%; padding: 10px; margin: 10px 0; box-sizing: border-box; }
            button { padding: 10px 20px; background: #4CAF50; color: white; border: none; border-radius: 5px; cursor: pointer; }
            button:hover { background: #45a049; }
            #result { margin-top: 20px; padding: 15px; background: #f5f5f5; border-radius: 5px; }
            .error { color: red; }
            .success { color: green; }
        </style>
    </head>
    <body>
        <h1>🧪 Teste do PerimeterX Solver</h1>
        
        <h2>Enviar Dados para Resolver</h2>
        <form id="testForm">
            <label>App ID:</label>
            <input type="text" name="app_id" value="PX0OZADU9K" required>
            
            <label>Fingerprint Type (ft):</label>
            <input type="number" name="ft" value="221" required>
            
            <label>Collector URI:</label>
            <input type="text" name="collector_uri" 
                   value="https://collector-px0ozadu9k.px-cloud.net/api/v2/collector" required>
            
            <label>Host:</label>
            <input type="text" name="host" value="https://airtable.com/login" required>
            
            <label>Session ID (sid):</label>
            <input type="text" name="sid" value="test-sid-12345" required>
            
            <label>Visitor ID (vid):</label>
            <input type="text" name="vid" value="test-vid-67890" required>
            
            <label>Client Timestamp (cts):</label>
            <input type="text" name="cts" value="test-cts-abcde" required>
            
            <label>Proxy (opcional):</label>
            <input type="text" name="proxy" placeholder="proxy_host:port">
            
            <button type="submit">Enviar para Resolver</button>
        </form>
        
        <div id="result"></div>
        
        <script>
            document.getElementById('testForm').addEventListener('submit', async (e) => {
                e.preventDefault();
                
                const formData = new FormData(e.target);
                const data = Object.fromEntries(formData);
                
                // Remover campo vazio de proxy
                if (!data.proxy) delete data.proxy;
                
                try {
                    const response = await fetch('/api/solve', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json'
                        },
                        body: JSON.stringify(data)
                    });
                    
                    const result = await response.json();
                    const resultDiv = document.getElementById('result');
                    
                    if (response.ok) {
                        resultDiv.innerHTML = `
                            <h3 class="success">✅ Sucesso!</h3>
                            <pre>${JSON.stringify(result, null, 2)}</pre>
                        `;
                    } else {
                        resultDiv.innerHTML = `
                            <h3 class="error">❌ Erro</h3>
                            <pre>${JSON.stringify(result, null, 2)}</pre>
                        `;
                    }
                } catch (error) {
                    document.getElementById('result').innerHTML = `
                        <h3 class="error">❌ Erro na requisição</h3>
                        <p>${error.message}</p>
                    `;
                }
            });
        </script>
    </body>
    </html>
    """
    return html, 200, {'Content-Type': 'text/html; charset=utf-8'}

# ====== ERROR HANDLERS ======

@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors"""
    return jsonify({
        "status": "error",
        "message": "Endpoint not found",
        "available_endpoints": [
            "GET  /",
            "GET  /health",
            "GET  /status",
            "GET  /info",
            "POST /api/solve",
            "GET  /test-solver"
        ]
    }), 404

@app.errorhandler(500)
def server_error(error):
    """Handle 500 errors"""
    return jsonify({
        "status": "error",
        "message": "Internal server error",
        "error": str(error)
    }), 500

# ====== MAIN ======

if __name__ == '__main__':
    logger.info("Starting PerimeterX Solver Application")
    logger.info("Available endpoints:")
    logger.info("  GET  http://localhost:5000/          - Home page with links")
    logger.info("  GET  http://localhost:5000/health    - Health check")
    logger.info("  GET  http://localhost:5000/status    - Status")
    logger.info("  GET  http://localhost:5000/info      - Info")
    logger.info("  POST http://localhost:5000/api/solve - Solver API")
    logger.info("  GET  http://localhost:5000/test-solver - Test form")
    
    app.run(host='0.0.0.0', port=5000, debug=False)
