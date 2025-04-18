# SeekSentinel: Automated Job Scraper & Filter

## Overview

SeekSentinel is a Python script designed to automate job searches on Seek.com.au. It uses specified criteria (keywords, location, salary) and filters results based on job description content (e.g., excluding roles requiring security clearances) and the presence of a "Quick Apply" option. Matching jobs are saved to a text file.

The script leverages Playwright for browser automation but optimizes the search process by constructing specific URLs with initial filters, enhancing speed and reliability compared to manual navigation.

## Quick Start

1.  **Prerequisites:** Python 3 installed.
2.  **Install Dependencies:** Open your terminal and run:
    ```bash
    pip install playwright && playwright install
    ```
3.  **Configure:** Edit the configuration variables (e.g., `SEARCH_KEYWORDS_LIST`, `LOCATION_NAME`, `SALARY_MIN`, `EXCLUSION_KEYWORDS`) near the top of `seek_scraper.py`.
4.  **Run:** Navigate to the script's directory in your terminal and execute:
    ```bash
    python seek_scraper.py
    ```
5.  **Results:** Find matching jobs listed in `seek_matching_jobs.txt` (or your configured output file).

## Features

*   **Multi-Keyword Search:** Iterates through a list of specified job keywords.
*   **URL-Based Filtering:** Applies location, salary, and distance filters directly via the search URL.
*   **Pagination:** Navigates through multiple pages of search results (configurable limit).
*   **Job Detail Analysis:** Scans the content of individual job posting pages.
*   **Content Filtering:**
    *   Requires "Quick Apply" button.
    *   Excludes jobs mentioning specific keywords (e.g., "security clearance", "nv1").
*   **Configurable:** Easily adjust search parameters and filters within the script.
*   **Text Output:** Saves relevant job details (Title, URL, Search Keyword) to a file.

## Configuration

Key settings are located at the top of `seek_scraper.py`:

*   **`SEARCH_KEYWORDS_LIST`**: List of job titles/keywords to search sequentially.
*   **`LOCATION_NAME`**: Target location (e.g., "Weston ACT 2611").
*   **`RADIUS_KM`**: Search radius around the location.
*   **`SALARY_MIN`**, **`SALARY_MAX`**: Desired annual salary range.
*   **`EXCLUSION_KEYWORDS`**: List of keys (defined in `KEYWORDS_TO_CHECK`) that will cause a job to be excluded if found in the description. Modify this list to customize content filtering.
*   **`OUTPUT_FILE`**: Name for the results file.
*   **`MAX_PAGES_TO_SCRAPE`**: Maximum number of result pages to process per keyword.

## Workflow

1.  Launches a web browser instance.
2.  Iterates through each `keyword` in `SEARCH_KEYWORDS_LIST`.
3.  Constructs a Seek search URL incorporating the keyword, location, salary, and radius filters.
4.  Navigates to the constructed URL.
5.  Scrapes job links from the results page(s), handling pagination up to `MAX_PAGES_TO_SCRAPE`.
6.  For each collected job link:
    *   Navigates to the job details page.
    *   Extracts the job title and description.
    *   Checks for the presence of a "Quick Apply" button.
    *   Checks if the description contains any terms listed in `EXCLUSION_KEYWORDS`.
7.  If a job has "Quick Apply" and *does not* contain exclusion keywords, it's considered a match.
8.  Saves all matched jobs (from all keyword searches) to the `OUTPUT_FILE`.
9.  Closes the browser.

## Output Example (`seek_matching_jobs.txt`)

```text
Keyword Searched: Analyst
Title: Data Analyst - Marketing
URL: https://www.seek.com.au/job/12345678
Quick Apply: True
--------------------
Keyword Searched: Business
Title: Business Process Improvement Lead
URL: https://www.seek.com.au/job/87654321
Quick Apply: True
--------------------
```

## Troubleshooting

*   **`ModuleNotFoundError: No module named 'playwright'`**: Run `pip install playwright`.
*   **`Executable doesn't exist...` error**: Run `playwright install`.
*   **`TimeoutError` or Failure Finding Elements**: Seek.com.au's website structure may have changed. The script's selectors (e.g., for job titles, buttons) likely need updating. This requires inspecting the website's HTML.
*   **Zero Results Found**:
    *   Verify that search filters (`LOCATION_NAME`, `SALARY_MIN`/`MAX`, `RADIUS_KM`) are not overly restrictive.
    *   Ensure `SEARCH_KEYWORDS_LIST` contains relevant terms.
    *   Check if `EXCLUSION_KEYWORDS` are too broad.

## Notes & Disclaimers

*   **Website Changes:** Web scraping scripts are sensitive to website updates. Seek.com.au may change its layout or URL structure, potentially breaking the script.
*   **Terms of Service:** Automated scraping may violate Seek's Terms of Service. Use this script responsibly.
*   **CAPTCHAs:** The script cannot solve CAPTCHAs. If encountered, execution will likely fail.