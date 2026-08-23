"""
PerimeterX Solver v6.7.9
Improved version with proper error handling, logging, and configuration management
"""

import tls_client
import uuid
import time
import json
import logging
import os
from typing import Optional
from dotenv import load_dotenv
from fingerprint import fingerprint_1, fingerprint_2
from mods import encrypt_payload, generate_pc
import urllib.parse

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class PXSolver:
    """
    PerimeterX v6.7.9 Solver
    
    Attributes:
        app_id: Application ID from PerimeterX script
        ft: Fingerprint type
        collector_uri: API endpoint URL
        host: Target website URL
        sid: Session ID
        vid: Visitor ID
        cts: Client timestamp
        proxy: Optional proxy URL
    """
    
    # Default user agent matching Chrome 127
    USER_AGENT = (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36"
    )
    
    def __init__(
        self,
        app_id: str,
        ft: int,
        collector_uri: str,
        host: str,
        sid: str,
        vid: str,
        cts: str,
        proxy: Optional[str] = None
    ):
        """Initialize PX Solver with required parameters"""
        
        self.app_id = app_id
        self.ft = ft
        self.collector_url = collector_uri
        self.host = host
        self.sid = sid
        self.vid = vid
        self.cts = cts
        
        logger.debug(f"Initializing PXSolver for app_id: {app_id}")
        
        # Initialize TLS session with Chrome 127 fingerprint
        self.session = tls_client.Session(
            client_identifier="chrome_127",
            random_tls_extension_order=True
        )
        
        # Configure proxy if provided
        if proxy:
            logger.info(f"Using proxy: {proxy}")
            self.session.proxies = {
                'https': f'http://{proxy}',
                'http': f'http://{proxy}'
            }
        
        # Set request headers
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
        
        # Initialize timestamps and UUIDs
        self.st = int(time.time()) * 1000
        self.site_uuids = {
            "sid": sid,
            "vid": vid,
            "cts": cts
        }
        self.uuid = str(uuid.uuid4())
        self.pc_key = f"{self.uuid}:v6.7.9:{ft}"
        self.rsc = 1
        
        # Store responses
        self.resp_1 = None
        self.resp_2 = None
        self.raw_payload = None
        self.fp_2 = None

    @staticmethod
    def parse_for_cookie(response: dict) -> Optional[str]:
        """
        Extract _px3 cookie from response
        
        Args:
            response: Response dictionary from collector API
            
        Returns:
            Cookie token string or None if not found
        """
        try:
            response_str = str(response.get('do', ''))
            token = response_str.split("bake|_px3|330|")[1].split("|")[0]
            logger.debug(f"Successfully parsed token from response")
            return token
        except (IndexError, KeyError, AttributeError) as e:
            logger.warning(f"Failed to parse cookie: {e}")
            return None

    def request_1(self) -> bool:
        """
        First fingerprint request
        
        Returns:
            True if successful, False otherwise
        """
        try:
            logger.info("Sending first fingerprint request...")
            
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
            
            # Add optional site UUIDs
            for site_key in self.site_uuids:
                if self.site_uuids[site_key] is not None:
                    payload[site_key] = self.site_uuids[site_key]
            
            self.rsc += 1
            
            # Send request
            response = self.session.post(
                self.collector_url,
                data=urllib.parse.urlencode(payload, safe="="),
                timeout=10
            )
            
            logger.debug(f"Response status: {response.status_code}")
            
            if response.status_code != 200:
                logger.error(
                    f"Request 1 failed with status {response.status_code}: {response.text[:200]}"
                )
                return False
            
            self.resp_1 = response.json()
            logger.info("First request completed successfully")
            return True
            
        except Exception as e:
            logger.error(f"Request 1 failed: {type(e).__name__}: {e}")
            return False

    def solve_request(self) -> bool:
        """
        Second fingerprint request to solve the challenge
        
        Returns:
            True if successful, False otherwise
        """
        try:
            logger.info("Sending solve request...")
            
            if self.resp_1 is None:
                logger.error("resp_1 is None, cannot proceed")
                return False
            
            self.fp_2 = fingerprint_2(
                json.loads(self.raw_payload),
                self.resp_1,
                self.site_uuids
            )
            
            # Extract cs value from response
            try:
                response_str = str(self.resp_1['do'])
                cs_value = response_str.split("cs|")[1].split("',")[0]
            except (IndexError, KeyError) as e:
                logger.error(f"Failed to extract cs value: {e}")
                return False
            
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
            
            # Send request
            response = self.session.post(
                self.collector_url,
                data=urllib.parse.urlencode(payload_data, safe="="),
                timeout=10
            )
            
            logger.debug(f"Response status: {response.status_code}")
            
            if response.status_code != 200:
                logger.error(
                    f"Solve request failed with status {response.status_code}: {response.text[:200]}"
                )
                return False
            
            self.resp_2 = response.json()
            logger.info("Solve request completed successfully")
            return True
            
        except Exception as e:
            logger.error(f"Solve request failed: {type(e).__name__}: {e}")
            return False

    def solve(self) -> Optional[str]:
        """
        Solve PerimeterX challenge
        
        Returns:
            _px3 cookie token if successful, None otherwise
        """
        logger.info(f"Starting to solve PX challenge for {self.host}")
        
        # Try first request
        if not self.request_1():
            logger.error("Failed to send initial request")
            return None
        
        # Check if token found in first response
        token = self.parse_for_cookie(self.resp_1)
        if token:
            logger.info("✅ Token found in first request")
            return token
        
        # Try solve request
        if not self.solve_request():
            logger.error("Failed to send solve request")
            return None
        
        # Check if token found in second response
        token = self.parse_for_cookie(self.resp_2)
        if token:
            logger.info("✅ Token found in solve request")
            return token
        
        logger.warning("❌ No token found in either response")
        return None


def main():
    """Main execution function"""
    
    # Get configuration from environment variables or defaults
    app_id = os.getenv("PX_APP_ID", "PX0OZADU9K")
    ft = int(os.getenv("PX_FT", "221"))
    collector_uri = os.getenv(
        "PX_COLLECTOR_URI",
        "https://collector-px0ozadu9k.px-cloud.net/api/v2/collector"
    )
    host = os.getenv("PX_HOST", "https://airtable.com/login")
    sid = os.getenv(
        "PX_SID",
        "474b6227-54f2-11ef-a959-cc2d2dcd99ae"
    )
    vid = os.getenv(
        "PX_VID",
        "49bf0cb5-5697-11ef-84ed-4e092214a776"
    )
    cts = os.getenv(
        "PX_CTS",
        "49bf1545-5697-11ef-84ed-422d064a3602"
    )
    proxy = os.getenv("PX_PROXY", None)
    
    logger.info("="*70)
    logger.info("PerimeterX Solver v6.7.9")
    logger.info("="*70)
    logger.info(f"Target: {host}")
    logger.info(f"App ID: {app_id}")
    logger.info(f"Collector: {collector_uri}")
    
    # Create solver and attempt to solve
    solver = PXSolver(
        app_id=app_id,
        ft=ft,
        collector_uri=collector_uri,
        host=host,
        sid=sid,
        vid=vid,
        cts=cts,
        proxy=proxy
    )
    
    token = solver.solve()
    
    logger.info("="*70)
    if token:
        logger.info(f"✅ SUCCESS: {token}")
        return token
    else:
        logger.error("❌ FAILED: Could not obtain token")
        return None


if __name__ == "__main__":
    token = main()
    if token:
        print(f"\nToken: {token}")
    else:
        print("\nFailed to solve PX challenge")