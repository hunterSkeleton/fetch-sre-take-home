import asyncio
import json
import logging
import time
from collections import defaultdict

import aiohttp
import yaml

# Constants
# TODO: Change to enums
STAT_TOTAL = "TOTAL"
STAT_UP = "UP"
STAT_DOWN = "DOWN"
STAT_TIMEOUT = "TIMEOUT"
CHECK_CYCLE_INTERVAL = 15  # in seconds
REQUEST_TIMEOUT = 0.5  # in seconds

# Logger config that will log INFO, WARN and ERROR level logs. DEBUG logs can be added, but are not used in this code.
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


def load_config(file_path):
    """
    Function to load configuration from the YAML file
    :param file_path:
    :return: Returns list of dictionary objects of endpoints
    """
    try:
        with open(file_path, 'r') as file:
            return yaml.safe_load(file)
    except FileNotFoundError:
        logger.error("File not found. Check if the file exists. Exiting Program.")
        sys.exit(1)


async def check_health(session, endpoint):
    """
    Check Endpoint Health / Asyncio Task Function
    :param session: shared aiohttp client session object
    :param endpoint: dictionary with endpoint data
    :return: (domain, status) where status is one of "UP", "DOWN", or "TIMEOUT"
    """
    url = endpoint['url']
    method = endpoint.get('method', "GET")
    headers = endpoint.get('headers')
    body = json.loads(endpoint.get('body', 'null'))
    # TODO: Use REGEX or urlparse library to safely extract domain and readability
    domain = endpoint["url"].split("//")[-1].split("/")[0].split(":")[0]
    # This demonstrates the flexibility to set timeouts for various stages of connection
    timeout = aiohttp.ClientTimeout(
        total=REQUEST_TIMEOUT,
        connect=None,
        sock_connect=None,
        sock_read=None
    )
    try:
        async with session.request(url=url, method=method, headers=headers, json=body, timeout=timeout) as response:
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


async def monitor_endpoints(file_path):
    """
    Monitoring Logic / Async Main Calling Function
    :param file_path: direct or relative path to the yaml config file
    """
    config = load_config(file_path)
    domain_stats = defaultdict(lambda: {STAT_TOTAL: 0, STAT_UP: 0, STAT_DOWN: 0, STAT_TIMEOUT: 0})
    while True:
        try:
            async with aiohttp.ClientSession() as session:
                tasks = [check_health(session, endpoint) for endpoint in
                         config]  # Creating tasks based on endpoints from config
                start_time = time.time()
                results = await asyncio.gather(*tasks)
                end_time = time.time()
                # Log Check-Cycle Results then log Cumulative Cycle Results
                log_availability(results)
                log_availability(results, domain_stats)
            # Calculating time taken for completion of tasks to ensure they are executed every 15 seconds exactly
            await asyncio.sleep(CHECK_CYCLE_INTERVAL - (end_time - start_time))
        except aiohttp.ClientError as e:
            logger.error(f"Session-related error: {e}")
        except Exception as e:
            logger.error(f"Unexpected error in monitoring loop: {e}")


def log_availability(results, cumulative=None):
    """
    Log Availability stats to console. This function logs both cumulative and check-cycle availabilities
    :param results: results from the current check cycle
    :param cumulative: Optional parameter to print cumulative stats instead of only check-cycle stats
    """
    # TODO: Add logs to a file
    domain_stats = cumulative if cumulative else defaultdict(
        lambda: {STAT_TOTAL: 0, STAT_UP: 0, STAT_DOWN: 0, STAT_TIMEOUT: 0})
    logstr = "cumulative" if cumulative is not None else "check cycle"
    for domain, status in results:
        domain_stats[domain][STAT_TOTAL] += 1
        domain_stats[domain][status] += 1

    for domain, stats in domain_stats.items():
        availability = round(100 * stats[STAT_UP] / stats[STAT_TOTAL]) if stats[STAT_TOTAL] else 0
        logger.info(f"{domain} had {availability}% {logstr} availability percentage")


if __name__ == "__main__":
    import sys

    if len(sys.argv) != 2:
        logger.error("Usage: python3 monitor.py <config_file_path>")
        sys.exit(1)

    config_file = sys.argv[1]

    try:
        asyncio.run(monitor_endpoints(config_file))
    except KeyboardInterrupt:
        logger.info("\nMonitoring stopped by user.")
