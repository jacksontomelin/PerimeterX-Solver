# 🤖 PerimeterX Solver v6.7.9

A Python implementation to solve PerimeterX v6.7.9 challenges. This project includes complete reverse-engineering of the PX fingerprinting mechanism.

![Version](https://img.shields.io/badge/PX_Version-6.7.9-blue)
![Python](https://img.shields.io/badge/Python-3.8%2B-green)
![License](https://img.shields.io/badge/License-MIT-yellow)

## 📋 Features

- ✅ Complete PerimeterX v6.7.9 challenge solver
- ✅ TLS fingerprint spoofing (Chrome 127)
- ✅ Proper error handling and logging
- ✅ Environment variable configuration
- ✅ Proxy support
- ✅ Timeout handling
- ✅ Type hints and documentation

## 🚀 Installation

### Prerequisites
- Python 3.8+
- pip

### Setup

1. Clone the repository:
```bash
git clone https://github.com/jacksontomelin/PerimeterX-Solver.git
cd PerimeterX-Solver
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Create `.env` file (optional):
```bash
cp .env.example .env
```

## 📝 Usage

### Basic Usage

```python
from solve import PXSolver

solver = PXSolver(
    app_id="PX0OZADU9K",
    ft=221,
    collector_uri="https://collector-px0ozadu9k.px-cloud.net/api/v2/collector",
    host="https://airtable.com/login",
    sid="474b6227-54f2-11ef-a959-cc2d2dcd99ae",
    vid="49bf0cb5-5697-11ef-84ed-4e092214a776",
    cts="49bf1545-5697-11ef-84ed-422d064a3602"
)

token = solver.solve()
if token:
    print(f"Token: {token}")
```

### With Proxy

```python
solver = PXSolver(
    app_id="PX0OZADU9K",
    ft=221,
    collector_uri="https://collector-px0ozadu9k.px-cloud.net/api/v2/collector",
    host="https://airtable.com/login",
    sid="sid_value",
    vid="vid_value",
    cts="cts_value",
    proxy="proxy_host:proxy_port"
)

token = solver.solve()
```

### Environment Variables

Create a `.env` file:

```env
PX_APP_ID=PX0OZADU9K
PX_FT=221
PX_COLLECTOR_URI=https://collector-px0ozadu9k.px-cloud.net/api/v2/collector
PX_HOST=https://airtable.com/login
PX_SID=474b6227-54f2-11ef-a959-cc2d2dcd99ae
PX_VID=49bf0cb5-5697-11ef-84ed-4e092214a776
PX_CTS=49bf1545-5697-11ef-84ed-422d064a3602
PX_PROXY=optional_proxy_url
```

Run:
```bash
python solve.py
```

## 🔍 How It Works

### Phase 1: Initial Fingerprint (request_1)
- Sends basic browser fingerprint data
- Receives challenge data from server
- Generates pc (process completion) hash

### Phase 2: Challenge Response (solve_request)
- Generates extended fingerprint with device data
- Includes WebGL fingerprint information
- Submits response with calculated hashes
- Receives _px3 cookie token

## 📦 Project Structure

```
PerimeterX-Solver/
├── solve.py              # Main solver class (improved)
├── fingerprint.py        # Fingerprint generation
├── mods.py              # Encryption and hashing functions
├── pc_functions.py      # PC hash calculation (MD5 based)
├── key_map.json         # Fingerprint key mappings
├── requirements.txt     # Python dependencies
├── .env.example         # Environment variables template
├── README.md            # This file
└── LICENSE              # MIT License
```

## 🔧 Configuration

### app_id
Application ID from the PerimeterX script. Extract from:
- HTML: Look for `PX0OZADU9K` in scripts
- JavaScript: Check `window._pxAppConfig`

### ft (Fingerprint Type)
- Usually 221 for standard implementations
- May vary by application

### collector_uri
API endpoint URL. Format:
- `https://collector-{app_id}.px-cloud.net/api/v2/collector`
- May differ by version/region

### sid, vid, cts
Session identifiers. These MUST be extracted in real-time:
- Generated per-session on target website
- Have limited TTL (usually minutes)
- Recommend extraction via Selenium/Playwright

## ⚠️ Important Notes

1. **Session IDs are Time-Sensitive**
   - sid, vid, cts must be extracted fresh before each solve attempt
   - They expire after a few minutes
   - Use Selenium or Playwright to extract them automatically

2. **Collector URL May Change**
   - Different PerimeterX versions use different endpoints
   - May be `/api/v1/`, `/api/v2/`, or `/api/v3/`
   - Check latest documentation if getting 404 errors

3. **Hardcoded Fingerprint Values**
   - Some WebGL fingerprint values are hardcoded
   - May need updates for different browsers/devices
   - Check `fingerprint.py` for values starting with `PX1`

4. **Rate Limiting**
   - Don't make excessive requests
   - Implement exponential backoff for retries
   - Respect the target website's ToS

## 🐛 Debugging

Enable debug logging:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

Check logs for:
- `HTTP 404`: Collector URL is wrong
- `HTTP 403`: Access denied (rate limit or IP block)
- `JSON decode error`: Response is not valid JSON
- `Failed to parse cookie`: Response format changed

## 📚 Technical Details

### Fingerprinting
- Uses TLS 1.3 with Chrome 127 fingerprint
- Includes WebGL device info
- Calculates MD5-based PC hash
- Encodes payload with XOR encryption

### Encryption
- XOR encryption with key 50
- Base64 encoding of encrypted data
- Safe URL encoding for payload

### Hashing
- MD5-based PC calculation
- Key derivation from UUID and fingerprint type
- HMAC-style validation with server data

## 🤝 Contributing

Improvements welcome! Areas for enhancement:
- Dynamic fingerprint value extraction
- Automatic session ID collection
- Support for newer PX versions
- Better error recovery

## 📞 Support

For issues or questions:
1. Check if collector URL is correct (test with curl)
2. Verify session IDs are fresh
3. Check debug logs
4. Ensure Python 3.8+ and dependencies installed

## 📜 License

MIT License - See LICENSE file for details

## ⚖️ Disclaimer

This tool is for educational and authorized testing purposes only. Ensure you have permission before using this on any website. Unauthorized access to computer systems is illegal.

---

**Last Updated**: 2026-08-23  
**Version**: 2.0.0 (Improved)  
**Maintainer**: Jackson Tomelin
