# How to use this script

## Install Required Packages
- ```pip install -r requirements.txt```
- There are some non-standard libraries that are needed for this script to work, so do not skip this step.

## Running the program
- ```python monitor.py <path-to-file>```
- Endpoint YAML file has to be passed as a command-line argument. The script will exit if the file is not found.
- The format for the config file can be found in sample.yaml.
- More examples/tests can be found under yaml-examples.

## Function Documentation
### load_config(file_path)
- Loads and parses the YAML configuration file.
- Args: file_path – path to the config file
- Returns: list of endpoint dictionaries

### check_health(session, endpoint)
- Asynchronously pings a single endpoint to check its status.
- Args:
  - session: shared aiohttp client session 
  - endpoint: dictionary with endpoint data 
- Returns: (domain, status) where status is one of "UP", "DOWN", or "TIMEOUT"

### monitor_endpoints(file_path)
- Main loop that:
  - Loads config 
  - Creates an aiohttp session 
  - Dispatches tasks for each endpoint 
  - Logs availability stats every 15 seconds

### log_availability(domain_stats, results)
- Aggregates and logs availability stats by domain.
- Resets stats after each 15-second interval.

## Issues with starter code
- No exception handling on file handling logic
- No default values assigned for optional fields in YAML file. Bound to raise errors.
- By design, the code logic is synchronous and would not scale since each request is being waited on for response. If mere 30 requests were to timeout, it would cross the 15 seconds cycle window.
- No timeout for request added as required.
- body variable in yaml is a json string which is being passed as directly as a json string to request() function, and it raises an error.
- 

## Changes to starter code
### Load config function
- Added exception handling for file errors.

### Check Health function
- Refactored code to add parallelism to network operations using asyncio library.
- Requests are made asynchronously instead of the earlier request-and-wait structure.
- Added default values for methods, headers and body variables.
- Added timeout of 500ms for request as required.
- Handled exception for timeout and other client session errors.
- Handled domain-name splitting logic here instead of Monitor function since it gave easier control over task scheduling. Added extra splitting function to remove port numbers from domain names.

### Monitor Endpoints function
- Added extra log stat TIMEOUT for diagnostics if required.
- Implemented asyncio task loop here.
- Requests are made asynchronously and the results are gathered when all tasks end. Since our requirements are specific, I assumed it is safe to not timeout tasks cumulatively.
- Moved the availability printing logic to a new function.