"""
PerimeterX Solver v2.0.0 - Web API
Flask server with lazy-loaded solver to prevent startup crashes
"""

import os
import json
import logging
import time
import uuid
import urllib.parse
from datetime import datetime
from typing import Optional
from flask import Flask, request, jsonify

# Load env
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# Logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Track import status
SOLVER_READY = False
IMPORT_ERROR = None

try:
    import tls_client
    from fingerprint import fingerprint_1, fingerprint_2
    from mods import encrypt_payload, generate_pc
    SOLVER_READY = True
    logger.info("All solver modules loaded successfully")
except Exception as e:
    IMPORT_ERROR = str(e)
    logger.error(f"Solver modules failed to load: {e}")


class PXSolver:
    USER_AGENT = (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36"
    )

    def __init__(self, app_id, ft, collector_uri, host, sid, vid, cts, proxy=None):
        self.app_id = app_id
        self.ft = ft
        self.collector_url = collector_uri
        self.host = host
        self.sid = sid
        self.vid = vid
        self.cts = cts

        self.session = tls_client.Session(
            client_identifier="chrome_127",
            random_tls_extension_order=True
        )

        if proxy:
            self.session.proxies = {
                'https': f'http://{proxy}',
                'http': f'http://{proxy}'
            }

        self.session.headers = {
            'accept': '*/*',
            'accept-language': 'en-US,en;q=0.9',
            'content-type': 'application/x-www-form-urlencoded',
            'origin': host,
            'priority': 'u=1, i',
            'sec-ch-ua': '"Not)A;Brand";v="99", "Google Chrome";v="127", "Chromium";v="127"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Windows"',
            'sec-fetch-dest': 'empty',
            'sec-fetch-mode': 'cors',
            'sec-fetch-site': 'cross-site',
            'user-agent': self.USER_AGENT,
        }

        self.st = int(time.time()) * 1000
        self.site_uuids = {"sid": sid, "vid": vid, "cts": cts}
        self.uuid = str(uuid.uuid4())
        self.pc_key = f"{self.uuid}:v6.7.9:{ft}"
        self.rsc = 1
        self.resp_1 = None
        self.resp_2 = None
        self.raw_payload = None
        self.fp_2 = None

    @staticmethod
    def parse_for_cookie(response):
        try:
            response_str = str(response.get('do', ''))
            token = response_str.split("bake|_px3|330|")[1].split("|")[0]
            return token
        except (IndexError, KeyError, AttributeError):
            return None

    def request_1(self):
        try:
            self.raw_payload = fingerprint_1(self.host, self.uuid, self.st)
            payload = {
                "payload": encrypt_payload(self.raw_payload),
                "appId": self.app_id,
                "tag": "v6.7.9",
                "uuid": self.uuid,
                "ft": self.ft,
                "seq": (self.rsc - 1),
                "en": "NTA",
                "pc": generate_pc(self.pc_key, self.raw_payload),
                "sid": self.sid,
                "rsc": self.rsc
            }
            for k in self.site_uuids:
                if self.site_uuids[k] is not None:
                    payload[k] = self.site_uuids[k]
            self.rsc += 1
            response = self.session.post(
                self.collector_url,
                data=urllib.parse.urlencode(payload, safe="="),
                timeout=10
            )
            if response.status_code != 200:
                logger.error(f"Request 1 failed: {response.status_code}")
                return False
            self.resp_1 = response.json()
            return True
        except Exception as e:
            logger.error(f"Request 1 error: {e}")
            return False

    def solve_request(self):
        try:
            if self.resp_1 is None:
                return False
            self.fp_2 = fingerprint_2(
                json.loads(self.raw_payload), self.resp_1, self.site_uuids
            )
            response_str = str(self.resp_1['do'])
            cs_value = response_str.split("cs|")[1].split("',")[0]
            payload_data = {
                "payload": encrypt_payload(self.fp_2),
                "appId": self.app_id,
                "tag": "v6.7.9",
                "uuid": self.uuid,
                "ft": self.ft,
                "seq": self.rsc - 1,
                "en": "NTA",
                "cs": cs_value,
                "pc": generate_pc(self.pc_key, self.fp_2),
                "sid": self.site_uuids['sid'],
                "vid": self.site_uuids['vid'],
                "cts": self.site_uuids['cts'],
                "rsc": self.rsc
            }
            response = self.session.post(
                self.collector_url,
                data=urllib.parse.urlencode(payload_data, safe="="),
                timeout=10
            )
            if response.status_code != 200:
                logger.error(f"Solve failed: {response.status_code}")
                return False
            self.resp_2 = response.json()
            return True
        except Exception as e:
            logger.error(f"Solve error: {e}")
            return False

    def solve(self):
        if not self.request_1():
            return None
        token = self.parse_for_cookie(self.resp_1)
        if token:
            return token
        if not self.solve_request():
            return None
        token = self.parse_for_cookie(self.resp_2)
        return token


# ====== FLASK ROUTES ======

@app.route('/', methods=['GET'])
def home():
    return jsonify({
        "service": "PerimeterX Solver",
        "version": "2.0.0",
        "status": "running",
        "solver_ready": SOLVER_READY,
        "import_error": IMPORT_ERROR,
        "endpoints": {
            "GET /": "This page",
            "GET /health": "Health check",
            "POST /api/solve": "Solve PX challenge",
            "GET /api/test-px?site=crunchbase": "Auto-test solver against PX site"
        },
        "test_sites": ["crunchbase", "zillow", "fiverr", "stockx", "airtable"],
        "timestamp": datetime.now().isoformat()
    })


@app.route('/health', methods=['GET'])
def health():
    return jsonify({
        "status": "healthy",
        "solver_ready": SOLVER_READY,
        "import_error": IMPORT_ERROR,
        "version": "2.0.0",
        "timestamp": datetime.now().isoformat()
    })


@app.route('/api/solve', methods=['POST'])
def solve_api():
    if not SOLVER_READY:
        return jsonify({
            "status": "error",
            "message": f"Solver not ready: {IMPORT_ERROR}"
        }), 503

    try:
        data = request.get_json()
        if not data:
            return jsonify({"status": "error", "message": "JSON body required"}), 400

        required = ['app_id', 'ft', 'collector_uri', 'host', 'sid', 'vid', 'cts']
        missing = [f for f in required if f not in data]
        if missing:
            return jsonify({"status": "error", "message": f"Missing: {', '.join(missing)}"}), 400

        solver = PXSolver(
            app_id=data['app_id'],
            ft=int(data['ft']),
            collector_uri=data['collector_uri'],
            host=data['host'],
            sid=data['sid'],
            vid=data['vid'],
            cts=data['cts'],
            proxy=data.get('proxy')
        )
        token = solver.solve()

        if token:
            return jsonify({"status": "success", "token": token})
        else:
            return jsonify({"status": "error", "message": "Failed to solve"}), 500

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route('/api/test-px', methods=['GET'])
def test_px():
    """
    Teste automático do PX Solver.
    GET /api/test-px?site=crunchbase
    GET /api/test-px?site=all
    """
    import re
    import traceback
    import requests as req
    import uuid as uuid_mod

    site = request.args.get('site', 'crunchbase')

    SITES = {
        "crunchbase": "https://www.crunchbase.com",
        "zillow": "https://www.zillow.com",
        "fiverr": "https://www.fiverr.com",
        "stockx": "https://stockx.com",
        "airtable": "https://airtable.com/login",
        "indeed": "https://www.indeed.com",
        "nordstrom": "https://www.nordstrom.com",
    }

    if site == "all":
        results = {}
        for s in SITES:
            try:
                px = _detect_px(s, SITES[s])
                results[s] = px
            except Exception as e:
                results[s] = {"status": "error", "error": str(e)}
        return jsonify({"status": "scan_complete", "results": results, "timestamp": datetime.now().isoformat()})

    if site not in SITES:
        return jsonify({
            "status": "error",
            "message": f"Site '{site}' não suportado",
            "available": list(SITES.keys()) + ["all"],
            "usage": "GET /api/test-px?site=all"
        }), 400

    result = _detect_px(site, SITES[site])

    # Se encontrou PX e solver está pronto, tentar resolver
    if result.get("px_detected") and result.get("app_id") and SOLVER_READY:
        solve_debug = _try_solve(
            app_id=result["app_id"],
            collector_uri=result.get("collector_uri"),
            host=SITES[site]
        )
        result["solve_attempt"] = solve_debug

    return jsonify(result)


def _detect_px(site_name, url):
    """Detecta PerimeterX em um site via múltiplos métodos"""
    import re
    import requests as req

    result = {
        "site": site_name,
        "url": url,
        "px_detected": False,
        "app_id": None,
        "collector_uri": None,
        "detection_methods": [],
        "antibot_signals": [],
    }

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml",
        "Accept-Language": "en-US,en;q=0.9",
    }

    try:
        resp = req.get(url, headers=headers, timeout=15, allow_redirects=True)
        result["http_status"] = resp.status_code
        result["final_url"] = resp.url
        html = resp.text
        resp_headers = dict(resp.headers)
    except Exception as e:
        result["error"] = f"Fetch failed: {e}"
        return result

    # === METHOD 1: Check response headers for PX cookies ===
    set_cookie = resp_headers.get("Set-Cookie", "") + resp_headers.get("set-cookie", "")
    px_cookies = []
    for cookie_name in ["_pxhd", "_pxvid", "_px3", "_px2", "_pxde", "_pxff"]:
        if cookie_name in set_cookie:
            px_cookies.append(cookie_name)
    if px_cookies:
        result["px_detected"] = True
        result["detection_methods"].append(f"PX cookies in headers: {px_cookies}")

    # === METHOD 2: Check for PX script tags ===
    # Pattern: //client.px-cloud.net/PXxxxxx/main.min.js
    px_scripts = re.findall(r'(?:src|href)\s*=\s*["\']([^"\']*px-cloud[^"\']*)["\']', html, re.I)
    px_scripts += re.findall(r'(?:src|href)\s*=\s*["\']([^"\']*px-cdn[^"\']*)["\']', html, re.I)
    if px_scripts:
        result["px_detected"] = True
        result["detection_methods"].append(f"PX script tags: {px_scripts}")
        # Extract app_id from script URL
        for script in px_scripts:
            m = re.search(r'/(PX[0-9A-Za-z]+)/', script)
            if m:
                result["app_id"] = m.group(1)

    # === METHOD 3: Check HTML for PX references ===
    px_refs = []
    patterns = {
        "px-cloud.net": r'px-cloud\.net',
        "px-cdn.net": r'px-cdn\.net',
        "_pxAppId": r'_pxAppId',
        "PXAppId": r'PX[0-9A-Z]{6,12}',
        "perimeterx": r'[Pp]erimeter[Xx]',
        "human-challenge": r'human-challenge',
        "px_cookie": r'_px[23hv]',
        "pxConfig": r'_?px[Cc]onfig',
        "px-captcha": r'px-captcha',
    }
    for name, pat in patterns.items():
        if re.search(pat, html):
            px_refs.append(name)

    if px_refs:
        if any(r in px_refs for r in ["px-cloud.net", "px-cdn.net", "_pxAppId", "pxConfig", "px-captcha"]):
            result["px_detected"] = True
        result["detection_methods"].append(f"HTML references: {px_refs}")

    # === METHOD 4: Extract app_id from HTML/JS ===
    if not result["app_id"]:
        # Try various patterns
        for pat in [
            r'"appId"\s*:\s*"(PX[^"]+)"',
            r"'appId'\s*:\s*'(PX[^']+)'",
            r'_pxAppId\s*=\s*["\']([^"\']+)',
            r'appId:\s*["\']?(PX[0-9A-Za-z]+)',
            r'client\.px-cloud\.net/(PX[^/]+)/',
        ]:
            m = re.search(pat, html)
            if m:
                result["app_id"] = m.group(1)
                break

    # === METHOD 5: Extract all PX-like IDs ===
    all_px_ids = list(set(re.findall(r'PX[0-9A-Z]{6,12}', html)))
    if all_px_ids:
        result["px_ids_in_html"] = all_px_ids
        if not result["app_id"]:
            result["app_id"] = all_px_ids[0]
        if not result["px_detected"]:
            result["px_detected"] = True
            result["detection_methods"].append(f"PX IDs in HTML: {all_px_ids}")

    # === METHOD 6: Try fetching PX script directly ===
    if not result["px_detected"]:
        # Some sites load PX via known paths
        px_paths = [
            f"{url.rstrip('/')}/px/client/main.min.js",
        ]
        for px_url in px_paths:
            try:
                r = req.head(px_url, headers=headers, timeout=5, allow_redirects=True)
                if r.status_code == 200:
                    result["px_detected"] = True
                    result["detection_methods"].append(f"PX script accessible at {px_url}")
            except:
                pass

    # === Build collector URI ===
    if result["app_id"] and not result["collector_uri"]:
        aid = result["app_id"].lower()
        result["collector_uri"] = f"https://collector-{aid}.px-cloud.net/api/v2/collector"

    # === Other antibot signals ===
    for sig, pat in {
        "Cloudflare": r'cloudflare|cf-ray|__cf_',
        "DataDome": r'datadome',
        "Akamai": r'akamai|_abck',
        "reCAPTCHA": r'recaptcha|grecaptcha',
        "hCaptcha": r'hcaptcha',
        "Kasada": r'kasada',
        "Shape/F5": r'shape\.com|_imp_apg_r_',
    }.items():
        if re.search(pat, html, re.I) or re.search(pat, str(resp_headers), re.I):
            result["antibot_signals"].append(sig)

    return result


def _try_solve(app_id, collector_uri, host):
    """Tenta resolver PX challenge"""
    import uuid as uuid_mod
    import traceback

    if not collector_uri:
        collector_uri = f"https://collector-{app_id.lower()}.px-cloud.net/api/v2/collector"

    sid = str(uuid_mod.uuid4())
    vid = str(uuid_mod.uuid4())
    cts = str(uuid_mod.uuid4())

    debug = {
        "app_id": app_id,
        "collector_uri": collector_uri,
        "host": host,
        "sid": sid,
        "vid": vid,
    }

    try:
        solver = PXSolver(
            app_id=app_id,
            ft=221,
            collector_uri=collector_uri,
            host=host,
            sid=sid,
            vid=vid,
            cts=cts
        )
        token = solver.solve()

        if token:
            debug["status"] = "SUCCESS"
            debug["token"] = token[:80] + "..." if len(str(token)) > 80 else token
        else:
            debug["status"] = "FAIL"
            debug["message"] = "Solver returned None (expected with generated session IDs)"
            if solver.resp_1:
                debug["resp_1"] = {
                    "type": str(type(solver.resp_1).__name__),
                    "keys": list(solver.resp_1.keys()) if isinstance(solver.resp_1, dict) else None,
                    "preview": str(solver.resp_1)[:300]
                }
            else:
                debug["resp_1"] = None
                debug["resp_1_note"] = "First request failed - collector may have rejected"

    except Exception as e:
        debug["status"] = "ERROR"
        debug["error"] = str(e)
        debug["traceback"] = traceback.format_exc().split("\n")[-3:]

    return debug




@app.errorhandler(404)
def not_found(e):
    return jsonify({
        "status": "error",
        "message": "Endpoint not found",
        "available": ["GET /", "GET /health", "POST /api/solve", "GET /api/test-px?site=crunchbase"]
    }), 404


if __name__ == "__main__":
    port = int(os.getenv("PORT", 3000))
    logger.info(f"Starting PX Solver API on 0.0.0.0:{port}")
    logger.info(f"Solver ready: {SOLVER_READY}")
    if IMPORT_ERROR:
        logger.error(f"Import error: {IMPORT_ERROR}")
    app.run(host='0.0.0.0', port=port, debug=False)
