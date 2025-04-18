# SeekSentinel: Automated Job Scraper & Filter

## Overview

SeekSentinel is a Python script designed to automate job searches on Seek.com.au. It uses specified criteria (keywords, location, salary) and filters results based on job description content (e.g., excluding roles requiring security clearances) and the presence of a "Quick Apply" option. Matching jobs, including title, employer, description, and URL, are saved to a timestamped text file.

The script leverages Playwright for browser automation but **optimises** the search process by constructing specific URLs with initial filters, enhancing speed and reliability compared to manual navigation.

## Quick Start

1.  **Prerequisites:** Python 3 installed.
2.  **Install Dependencies:** Open your terminal and run:
    ```bash
    pip install playwright && playwright install
    ```
3.  **Configure:** Edit the configuration variables (see "Configuration Parameters" below) near the top of `seek_scraper.py`.
4.  **Run:** Navigate to the script's directory in your terminal and execute:
    ```bash
    python seek_scraper.py
    ```
5.  **Results:** Find matching jobs listed in the generated `Seek_Matching_Jobs_YYYYMMDD_HHMMSS.txt` file.

## Features

*   **Multi-Keyword Search:** Iterates through a list of specified job keywords.
*   **URL-Based Filtering:** Applies location, salary, and distance filters directly via the search URL.
*   **Pagination:** Navigates through multiple pages of search results (configurable limit).
*   **Job Detail Extraction:** Scrapes key details from individual job posting pages:
    *   Job Title
    *   Employer Name
    *   Full Job Description
*   **Content Filtering:**
    *   Requires "Quick Apply" button.
    *   Excludes jobs mentioning specific keywords (e.g., "security clearance", "nv1").
*   **Configurable:** Easily adjust search parameters and filters within the script.
*   **Timestamped Text Output:** Saves relevant job details to a uniquely named file for each run.

## Configuration Parameters

All configuration settings are located in the `# --- Configuration ---` section near the top of the `seek_scraper.py` file.

*   **`SEARCH_KEYWORDS_LIST`**: A Python list of strings. Each string is a keyword or phrase (e.g., "Project Manager", "Admin") that the script will search for sequentially.
*   **`LOCATION_NAME`**: A string specifying the target location for the job search. **Important:** To ensure correct URL construction, go to Seek.com.au, perform a search with your desired postcode or suburb in the "Where" field, and copy the exact text Seek uses (e.g., "Weston ACT 2611", "Sydney NSW 2000"). Use this exact text for the `LOCATION_NAME` variable.
*   **`RADIUS_KM`**: A string representing the search radius in kilometers around the `LOCATION_NAME` (e.g., "50").
*   **`SALARY_MIN`**: A string representing the minimum desired annual salary (e.g., "80000").
*   **`SALARY_MAX`**: A string representing the maximum desired annual salary (e.g., "120000").
*   **`MAX_PAGES_TO_SCRAPE`**: An integer defining the maximum number of search result pages to scrape for *each* keyword in `SEARCH_KEYWORDS_LIST`.
*   **`MAX_DESCRIPTION_LENGTH`**: An integer specifying the maximum number of characters to save from the job description. Set to `0` or a negative number to save the full, untruncated description.
*   **`KEYWORDS_TO_CHECK`**: A Python dictionary where keys are identifiers (e.g., "security_clearance") and values are raw string regular expressions (e.g., `r"security clearance"`) used to search within job descriptions. You generally won't modify this directly unless adding new types of terms to check for.
*   **`EXCLUSION_KEYWORDS`**: A Python list of strings. Each string must match a *key* from the `KEYWORDS_TO_CHECK` dictionary. If a job description contains text matching the regex associated with any key listed here, the job will be *excluded* from the results. This is the primary way to customise content filtering.
*   **`OUTPUT_FILE`**: This variable is generated automatically using the current timestamp (`f"Seek_Matching_Jobs_{TIMESTAMP}.txt"`). You don't typically need to change the line defining `OUTPUT_FILE` itself, but be aware of how the filename is constructed.

## Workflow

1.  Launches a web browser instance.
2.  Generates a timestamped output filename based on the `OUTPUT_FILE` pattern.
3.  Iterates through each `keyword` in `SEARCH_KEYWORDS_LIST`.
4.  Constructs a Seek search URL incorporating the keyword, `LOCATION_NAME`, `SALARY_MIN`, `SALARY_MAX`, and `RADIUS_KM`.
5.  Navigates to the constructed URL.
6.  Scrapes job links from the results page(s), handling pagination up to `MAX_PAGES_TO_SCRAPE`.
7.  For each collected job link:
    *   Navigates to the job details page.
    *   Extracts the job title, employer name, and full description.
    *   Checks for the presence of a "Quick Apply" button.
    *   Checks if the description contains any terms associated with keys in `EXCLUSION_KEYWORDS`.
8.  If a job has "Quick Apply" and *does not* contain exclusion keywords, it's considered a match.
9.  Saves all matched jobs (including title, employer, URL, potentially truncated description based on `MAX_DESCRIPTION_LENGTH`, and the search keyword used) from all keyword searches to the timestamped `OUTPUT_FILE`.
10. Closes the browser.

## Output Example (`Seek_Matching_Jobs_YYYYMMDD_HHMMSS.txt`)

```text
Keyword Searched: Analyst
Title: Data Analyst - Marketing
Listed By: Example Corp
URL: https://www.seek.com.au/job/12345678
Quick Apply: True

Description:
[Full job description text appears here, potentially truncated if MAX_DESCRIPTION_LENGTH is set]...
------------------------------------------

Keyword Searched: Business
Title: Business Process Improvement Lead
Listed By: Another Company Pty Ltd
URL: https://www.seek.com.au/job/87654321
Quick Apply: True

Description:
[Full job description text appears here, potentially truncated if MAX_DESCRIPTION_LENGTH is set]...
------------------------------------------

```

## Troubleshooting

*   **`ModuleNotFoundError: No module named 'playwright'`**: Run `pip install playwright`.
*   **`Executable doesn't exist...` error**: Run `playwright install`.
*   **`TimeoutError` or Failure Finding Elements**: Seek.com.au's website structure may have changed. The script's selectors (e.g., for job titles, employer, description, buttons) likely need updating. This requires inspecting the website's HTML.
*   **Zero Results Found**:
    *   Verify that search filters (`LOCATION_NAME`, `SALARY_MIN`/`MAX`, `RADIUS_KM`) are not overly restrictive. Check that `LOCATION_NAME` uses the exact format from the Seek website.
    *   Ensure `SEARCH_KEYWORDS_LIST` contains relevant terms.
    *   Check if `EXCLUSION_KEYWORDS` are too broad or if the corresponding regex in `KEYWORDS_TO_CHECK` is incorrect.

## Notes & Disclaimers

*   **Website Changes:** Web scraping scripts are sensitive to website updates. Seek.com.au may change its layout or URL structure, potentially breaking the script.
*   **Terms of Service:** Automated scraping may violate Seek's Terms of Service. Use this script responsibly.
*   **CAPTCHAs:** The script cannot solve CAPTCHAs. If encountered, execution will likely fail.