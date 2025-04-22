import yaml
import json
import asyncio
import aiohttp
import logging
from collections import defaultdict

#Constants FUTURE: Change to enums
STAT_TOTAL = "TOTAL"
STAT_UP = "UP"
STAT_DOWN = "DOWN"
STAT_TIMEOUT = "TIMEOUT"
CHECK_CYCLE_INTERVAL = 15 # in seconds
REQUEST_TIMEOUT = 0.5 # in seconds

# Logging setup
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Function to load configuration from the YAML file
def load_config(file_path):
    try:
        with open(file_path, 'r') as file:
            return yaml.safe_load(file)
    except FileNotFoundError :
        logger.error("File not found. Check if the file exists. Exiting Program.")
        sys.exit(1)

#Check Endpoint Health / Asyncio Task Function
async def check_health(session, endpoint):
    url = endpoint['url']
    method = endpoint.get('method', "GET")
    headers = endpoint.get('headers')
    body = json.loads(endpoint.get('body', 'null'))
    domain = endpoint["url"].split("//")[-1].split("/")[0].split(":")[0]
    timeout = aiohttp.ClientTimeout(
        total=REQUEST_TIMEOUT,
        connect=None,
        sock_connect=None,
        sock_read=None
    )
    try:
        async with session.request(url=url, method=method, headers= headers, json=body, timeout=timeout) as response:
            if 200 <= response.status < 300:
                return domain, STAT_UP
            else:
                return domain, STAT_DOWN
    except asyncio.TimeoutError:
        logger.warning(f"Timeout on {url}")
        return domain, STAT_TIMEOUT
    except aiohttp.ClientError as e:
        logger.warning(f"Client error on {url}: {e}")
        return domain, STAT_DOWN
    except Exception as e:
        logger.warning(f"Unexpected error on {url}: {e}")
        return domain, STAT_DOWN

#Monitoring Logic / Async Main Calling Function
async def monitor_endpoints(file_path):
    config = load_config(file_path)
    domain_stats = defaultdict(lambda : {STAT_TOTAL: 0, STAT_UP: 0, STAT_DOWN: 0, STAT_TIMEOUT: 0})
    while True:
        try:
            async with aiohttp.ClientSession() as session:
                tasks = [check_health(session, endpoint) for endpoint in config]
                results = await asyncio.gather(*tasks)
                log_availability(domain_stats, results)
            await asyncio.sleep(CHECK_CYCLE_INTERVAL)
        except aiohttp.ClientError as e:
            logger.error(f"Session-related error: {e}")
        except Exception as e:
            logger.error(f"Unexpected error in monitoring loop: {e}")

#Log Availability Stats
def log_availability(domain_stats, results):
    for domain, status in results:
        domain_stats[domain][STAT_TOTAL] += 1
        domain_stats[domain][status] += 1
    for domain, stats in domain_stats.items():
        try:
            availability = round(100 * stats[STAT_UP] / stats[STAT_TOTAL]) if stats[STAT_TOTAL] else 0
            logger.info(f"{domain} has {availability}% availability percentage")
        except ZeroDivisionError:
            logger.warning(f"{domain} has no data")
        # stats.update({key: 0 for key in stats}) #Leaving for clarification on cumulative stats
    print("---")

if __name__ == "__main__":
    import sys
    if len(sys.argv) != 2:
        logger.error("Usage: python monitor-threading.py <config_file_path>")
        sys.exit(1)

    config_file = sys.argv[1]

    try:
        asyncio.run(monitor_endpoints(config_file))
    except KeyboardInterrupt:
        logger.info("\nMonitoring stopped by user.")