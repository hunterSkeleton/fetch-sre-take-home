# How to use this script

## 0. Pre-requisites

- python3 / pip3
    - You need python3 to run the program since the code and libraries used are developed in python3 environment.

## 1. Install Required Packages

> There are some non-standard libraries that are needed for this script to work, so do not skip this step.

- `pip3 install -r requirements.txt`

## 2. Running the program

- `python3 monitor.py <path-to-file>`
- Endpoint YAML file has to be passed as a command-line argument. The `path_to_file` can be relative or direct.
- The script will exit if the file is not found.
- The format for the config file can be found
  in [sample.yaml](https://github.com/hunterSkeleton/fetch-sre-take-home/blob/main/sample.yaml).
- More examples/tests can be found
  under [yaml-examples](https://github.com/hunterSkeleton/fetch-sre-take-home/tree/main/yaml-examples).

--------

## Function Documentation:

- ### load_config(file_path)
    - Loads and parses the YAML configuration file.
    - Args:
        - file_path: path to the config file
    - Returns:
        - list of endpoint dictionaries

- ### check_health(session, endpoint)
    - Asynchronously pings a single endpoint to check its status.
    - Args:
        - session: shared aiohttp client session object
        - endpoint: dictionary with endpoint data
    - Returns:
      - (domain, status): where status is one of `UP`, `DOWN`, or `TIMEOUT`

- ### monitor_endpoints(file_path)
    - Main loop that:
        - Loads config
        - Creates an aiohttp session
        - Dispatches tasks for each endpoint
        - Logs availability stats every 15 seconds
    - Args:
        - file_path: path to the config file

- ### log_availability(results, cumulative)
    - Aggregates and logs availability stats by domain.
    - Resets stats after each 15-second interval.
    - Args:
      - results: results from the current check cycle
      - cumulative: optional argument to determine the type of log to be printed
    - The current availability percentages are calculated by taking into consideration the previous states of endpoints.
      But this gives wrong availability percentages if some endpoints fail between check cycles. Consider there are 15
      endpoints of a certain domain, and during first check cycle all 15 are UP. Suppose, before the next check cycle, 5
      endpoints become unavailable.
    - ### Current Cumulative Availability
      | TOTAL | UP | Availability (%) |
          |-------|----|------------------|
      | 15    | 15 | 100              |
      | 30    | 20 | 66               |
    - This can be used for availability stats over longer periods.
    - Instead, if we do not consider previous states of our endpoints, we get current availability of our endpoints by
      calculating availability for only the current check cycle.
    - ### Cycle-Only Availability
      | TOTAL | UP | Availability (%) |
          |-------|----|------------------|
      | 15    | 15 | 100              |
      | 15    | 5  | 33               |
    - This can be used for making alerts and live dashboards.
    - Considering the requirements we also need to determine availability accurately during each cycle, which can be
      achieved by calculating availability of only the current check cycle results.

--------

## Issues with starter code:

- No exception handling on file handling logic.
- No default values assigned for optional fields in YAML file. Bound to raise errors.
- By design, the code logic is synchronous, and would not scale since each request is being waited on for response. If the number of requests timing out increased above 30, it would cross the 15 seconds cycle window.
- No timeout for request added as required.
- The `body` variable in yaml is a json string which is being passed directly as a json string to `request` function,
  which would raise an error.

## Changes to starter code:

- ### Load config function
    - Added exception handling for file errors.

- ### Check Health function
    - Refactored code to add parallelism to network operations using asyncio library.
    - Requests are made asynchronously instead of the earlier request-and-wait structure.
    - Added default values for optional variables `methods`, `headers`, and `body` using `endpoints.get()`. Used json library to convert dictionary string to
      json object and handled empty `body` string using `null`.
    - Added timeout of 500ms for request as required.
    - Handled exception for timeout and other client session errors.
    - Handled domain name parsing logic in this function instead of `monitor_endpoint` function since it gave easier control over task
      scheduling. Added extra split on URL to remove port numbers.

- ### Monitor Endpoints function
    - Added extra log stat `TIMEOUT` for extra endpoint debugging or diagnostics.
    - Implemented `asyncio` task loop here.
    - Requests are made asynchronously and the results are gathered when all tasks end. Since all tasks run parallely, it is safe to assume that they will not cross the 15s time limit.
    - Measured time taken for the check cycle to complete to calculate sleep time before next cycle starts.
    - Moved the availability percentage printing logic to a new function.

## Testing:
- Tested code against URLs with port numbers.
- Tested code against both HTTP and HTTPS URLs.
- Tested code against different HTTP request methods (e.g. POST, PUT, DELETE, PATCH, ...).
- Tested code against 150 endpoints that timeout.

## Future Considerations:

- Availability statistic variables can be handled with enums for more modularity.
- Logging can be improved with other network/connection/resource errors.
- Logs can be exported to a file.
- URL parsing can be done using a library like urlparse or regex for safety and readability.