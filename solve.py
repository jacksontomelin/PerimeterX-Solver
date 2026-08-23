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
            "POST /api/solve": "Solve PX challenge"
        },
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


@app.errorhandler(404)
def not_found(e):
    return jsonify({
        "status": "error",
        "message": "Endpoint not found",
        "available": ["GET /", "GET /health", "POST /api/solve"]
    }), 404


if __name__ == "__main__":
    port = int(os.getenv("PORT", 3000))
    logger.info(f"Starting PX Solver API on 0.0.0.0:{port}")
    logger.info(f"Solver ready: {SOLVER_READY}")
    if IMPORT_ERROR:
        logger.error(f"Import error: {IMPORT_ERROR}")
    app.run(host='0.0.0.0', port=port, debug=False)
