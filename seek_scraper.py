import asyncio
import re # Import regex module for more flexible text searching
import urllib.parse # For URL encoding/construction
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeoutError

# --- Configuration ---
# Keywords to search for sequentially
SEARCH_KEYWORDS_LIST = ["Admin", "Business", "Analyst"]

# Location details
LOCATION_NAME = "Weston ACT 2611" # Used for slug generation
RADIUS_KM = "50"
SALARY_MIN = "80000"
SALARY_MAX = "120000"
OUTPUT_FILE = "seek_matching_jobs.txt"
MAX_PAGES_TO_SCRAPE = 10 # Limit the number of pages per keyword search

# Keywords to check for inside job descriptions (case-insensitive) - Terms to EXCLUDE
KEYWORDS_TO_CHECK = {
    "security_clearance": r"security clearance",
    "nv1": r"\bnv1\b",
    "baseline": r"\bbaseline\b",
    "citizenship": r"citizen(?:ship)?",
    "federal_government": r"federal government"
}

# List of keyword keys from above that should CAUSE EXCLUSION if found
EXCLUSION_KEYWORDS = [
    "security_clearance",
    "nv1",
    "baseline",
    "citizenship",
    "federal_government"
]

# --- End Configuration ---

def format_seek_slug(text):
    """Formats text into a Seek URL slug (e.g., 'Weston ACT 2611' -> 'Weston-ACT-2611')."""
    slug = text.strip().replace(' ', '-')
    # Remove characters not typically allowed in URL paths (allow letters, numbers, hyphen)
    slug = re.sub(r'[^\w\-]+', '', slug)
    # Remove leading/trailing hyphens that might result from sanitization
    slug = slug.strip('-')
    return slug

def construct_seek_url(keyword, location, salary_min, salary_max, radius):
    """Constructs the Seek search URL with filters."""
    base_url = "https://www.seek.com.au"
    keyword_slug = format_seek_slug(keyword)
    location_slug = format_seek_slug(location)

    # Construct path component
    # Example: /Admin-jobs/in-Weston-ACT-2611
    # Handle case where keyword might be empty (though not in our list)
    if keyword_slug:
        path = f"/{keyword_slug}-jobs/in-{location_slug}"
    else:
        path = f"/jobs/in-{location_slug}" # Path if no keyword

    # Construct query parameters
    params = {
        "salaryrange": f"{salary_min}-{salary_max}",
        "distance": str(radius),
        "salarytype": "annual" # Often needed, assume annual unless specified otherwise
        # Add any other static parameters discovered from manual search URL if needed
    }
    # Encode parameters into a query string (e.g., ?salaryrange=...&distance=...)
    query_string = urllib.parse.urlencode(params)

    return f"{base_url}{path}?{query_string}"

async def check_job_page(page, job_url):
    """Navigates to a job page and checks for keywords and Quick Apply."""
    # This function remains largely the same as before
    print(f"  Checking job: {job_url}")
    try:
        await page.goto(job_url, wait_until="domcontentloaded", timeout=45000)
        await page.wait_for_timeout(2000)

        job_title = "Unknown Title"
        try:
            title_element = page.locator('h1[data-automation="job-detail-title"], h1').first
            await title_element.wait_for(timeout=10000)
            job_title = await title_element.text_content()
            job_title = job_title.strip() if job_title else "Unknown Title"
            print(f"    Job Title: {job_title}")
        except PlaywrightTimeoutError:
            print("    Error: Could not find job title element in time.")
        except Exception as e:
            print(f"    Error extracting job title: {e}")

        description_text = ""
        try:
            desc_container = page.locator('[data-automation="jobAdDetails"]')
            await desc_container.wait_for(timeout=15000)
            if await desc_container.count() > 0:
                description_text = await desc_container.first.inner_text()
            else:
                description_text = await page.locator('body').inner_text()
                print("    Warning: Could not find specific description container, using body text.")
            description_text_lower = description_text.lower()
        except PlaywrightTimeoutError:
            print("    Error: Timed out waiting for job description container.")
            return None
        except Exception as e:
            print(f"    Error extracting description text: {e}")
            return None

        keyword_found = {}
        print("    Checking for keywords to exclude...")
        for key, pattern in KEYWORDS_TO_CHECK.items():
            if re.search(pattern, description_text_lower):
                keyword_found[key] = True
                if key in EXCLUSION_KEYWORDS:
                    print(f"    Exclusion keyword found: '{pattern}'")
            else:
                keyword_found[key] = False

        is_quick_apply = False
        print("    Checking for Quick Apply button...")
        try:
            apply_button = page.locator('a[data-automation="job-detail-apply"]')
            await apply_button.wait_for(state="visible", timeout=10000)
            if await apply_button.count() > 0:
                 button_text = await apply_button.first.text_content()
                 button_text = button_text.strip().lower() if button_text else ""
                 print(f"    Apply button text: '{button_text}'")
                 if "quick apply" in button_text:
                     is_quick_apply = True
                     print("    Quick Apply detected.")
                 else:
                     print("    Apply button found, but not 'Quick Apply'.")
            else:
                print("    Warning: Could not find the apply button using primary selector.")
        except PlaywrightTimeoutError:
            print("    Error: Timed out waiting for apply button or button not visible.")
        except Exception as e:
            print(f"    Error checking apply button: {e}")

        return {
            "url": job_url,
            "title": job_title,
            "keywords_found": keyword_found,
            "is_quick_apply": is_quick_apply
        }
    except PlaywrightTimeoutError:
        print(f"  Error: Timed out loading or processing job page {job_url}")
        return None
    except Exception as e:
        print(f"  Error processing job page {job_url}: {e}")
        return None

async def main():
    """Main function to run the scraper."""
    browser = None # Initialize browser variable outside try block
    async with async_playwright() as p:
        try: # Outer try block for overall browser operations
            browser = await p.chromium.launch(headless=False)
            page = await browser.new_page()
            all_matching_jobs = [] # List to store matching jobs across all keywords

            for current_keyword in SEARCH_KEYWORDS_LIST:
                print(f"\n===== Starting search for keyword: '{current_keyword}' =====")
                try: # Inner try block for handling errors per keyword
                    # Construct the specific URL for this keyword search
                    target_url = construct_seek_url(
                        current_keyword, LOCATION_NAME, SALARY_MIN, SALARY_MAX, RADIUS_KM
                    )
                    print(f"Navigating to constructed URL: {target_url}")

                    # Go directly to the pre-filtered URL
                    await page.goto(target_url, wait_until="domcontentloaded", timeout=60000)
                    print("Search results page loaded.")
                    await page.wait_for_timeout(3000) # Wait for elements like pagination to settle

                    # --- Collect Job Links using Pagination ---
                    print("\nCollecting job links using pagination...")
                    job_links = set() # Reset links for each keyword
                    page_count = 0

                    while page_count < MAX_PAGES_TO_SCRAPE:
                        page_count += 1
                        print(f"--- Scraping page {page_count} for '{current_keyword}' ---")
                        await page.wait_for_timeout(2000)

                        links_on_page = await page.locator('article[data-automation="normalJob"] a[data-automation="jobTitle"]').all()
                        page_link_count = 0
                        if not links_on_page and page_count == 1:
                            print("Warning: No job links found on the first page. Filters might be too restrictive or URL incorrect.")
                        for link in links_on_page:
                            href = await link.get_attribute('href')
                            if href:
                                if href.startswith('/'):
                                    href = f"https://www.seek.com.au{href}"
                                if href not in job_links:
                                   job_links.add(href)
                                   page_link_count += 1

                        print(f"Found {page_link_count} new job links on this page. Total unique links for '{current_keyword}': {len(job_links)}")

                        next_button_selector = 'a[data-automation="page-next"], a:has-text("Next")'
                        next_button = page.locator(next_button_selector)
                        is_next_enabled = False
                        if await next_button.count() > 0:
                            if await next_button.is_enabled():
                                is_next_enabled = True

                        if is_next_enabled:
                            print("Found enabled 'Next' button. Clicking...")
                            try:
                                await next_button.click()
                                await page.wait_for_load_state("domcontentloaded", timeout=30000)
                                await page.wait_for_timeout(1000)
                            except PlaywrightTimeoutError:
                                print("Timeout waiting for next page to load after clicking 'Next'. Stopping pagination for this keyword.")
                                break
                            except Exception as next_click_err:
                                 print(f"Error clicking 'Next' button or waiting for next page: {next_click_err}. Stopping pagination for this keyword.")
                                 break
                        else:
                            print("Next button not found or not enabled. Reached the last page or max pages for this keyword.")
                            break # Exit pagination loop for this keyword

                    print(f"\nFinished collecting links for '{current_keyword}'. Found a total of {len(job_links)} unique links.")

                    # --- Process Collected Links for this keyword ---
                    keyword_matches = []
                    processed_count = 0
                    if not job_links:
                         print(f"No job links collected for '{current_keyword}' to process.")

                    for job_url in job_links:
                        processed_count += 1
                        print(f"\n--- Processing job {processed_count} / {len(job_links)} for '{current_keyword}' ---")
                        job_data = await check_job_page(page, job_url)

                        if job_data:
                            passes_filter = True
                            if not job_data["is_quick_apply"]:
                                passes_filter = False
                                print("    Filter fail: Not Quick Apply.")
                            if passes_filter:
                                for keyword_key in EXCLUSION_KEYWORDS:
                                    if job_data["keywords_found"].get(keyword_key, False):
                                        passes_filter = False
                                        print(f"    Filter fail: Exclusion keyword '{keyword_key}' mentioned.")
                                        break
                            if passes_filter:
                                print(f"  >>> MATCH FOUND (Keyword: {current_keyword}): {job_data['title']}")
                                job_data['search_keyword'] = current_keyword # Add keyword context
                                keyword_matches.append(job_data)

                    all_matching_jobs.extend(keyword_matches) # Add this keyword's matches to the overall list

                except Exception as keyword_error: # Catch errors specific to this keyword's processing
                     print(f"ERROR processing keyword '{current_keyword}': {keyword_error}")
                     print("Continuing to next keyword...")
                     # Optional: Add a longer wait or browser restart logic here if needed

            # --- Save ALL Results --- (Still inside the outer try)
            if all_matching_jobs:
                print(f"\nSaving {len(all_matching_jobs)} total matching jobs from all keyword searches to {OUTPUT_FILE}...")
                # Sort results perhaps? Optional. e.g., by keyword then title
                # all_matching_jobs.sort(key=lambda x: (x['search_keyword'], x['title']))
                with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
                    for job in all_matching_jobs:
                        f.write(f"Keyword Searched: {job['search_keyword']}\n")
                        f.write(f"Title: {job['title']}\n")
                        f.write(f"URL: {job['url']}\n")
                        # Optionally write keyword findings for context
                        # f.write(f"Keywords Found: {job['keywords_found']}\n")
                        f.write(f"Quick Apply: {job['is_quick_apply']}\n")
                        f.write("-" * 20 + "\n")
                print("Done saving.")
            else:
                print("\nNo jobs found matching criteria across all keywords.")

        except Exception as outer_error: # Optional: Catch errors outside the keyword loop
             print(f"\nAn unexpected error occurred during the main process: {outer_error}")
             # This could be browser launch errors, etc.

        finally: # Outer finally block, ensures browser closure
            if browser: # Check if browser was successfully launched before trying to close
                print("Closing browser...")
                await browser.close()
            else:
                print("Browser was not launched, no need to close.")


if __name__ == "__main__":
    asyncio.run(main())
