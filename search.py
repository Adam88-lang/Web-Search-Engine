from settings import *
import requests
from requests.exceptions import RequestException
import pandas as pd
from storage import DBStorage
from datetime import datetime
from urllib.parse import quote_plus
from concurrent.futures import ThreadPoolExecutor

# Set up a cache to store search results
search_cache = {}

# Function to query search API with specified parameters and return results as a DataFrame
def search_api(query, pages=int(RESULT_COUNT/10)):
    # Check if results are already in cache
    if query in search_cache:
        return search_cache[query]

    results = []
    # Loop through the specified number of pages
    for i in range(0, pages):
        start = i*10+1
        # Format the search URL with the provided API key, search ID, query, and start index
        url = SEARCH_URL.format(
            key=SEARCH_KEY,
            cx=SEARCH_ID,
            query=quote_plus(query),
            start=start
        )
        response = requests.get(url)
        data = response.json()
        results += data["items"]
    res_df = pd.DataFrame.from_dict(results)
    res_df["rank"] = list(range(1, res_df.shape[0] + 1))
    res_df = res_df[["link", "rank", "snippet", "title"]]
    # Add results to cache
    search_cache[query] = res_df
    return res_df

# Function to scrape HTML content from a list of URLs and return the results
def scrape_page(link):
    try:
        data = requests.get(link, timeout=5)
        return data.text
    except RequestException:
        return ""

# Main search function to retrieve search results, scrape pages, and store results in a database
def search(query):
    columns = ["query", "rank", "link", "title", "snippet", "html", "created"]
    storage = DBStorage()

    # Check if query results already exist in the database
    stored_results = storage.query_results(query)
    if stored_results.shape[0] > 0:
        stored_results["created"] = pd.to_datetime(stored_results["created"])
        return stored_results[columns]

    # If query results not found in the database, use the API to fetch results
    print("No results in database.  Using the API.")
    results = search_api(query)
    with ThreadPoolExecutor(max_workers=10) as executor:
        html = list(executor.map(scrape_page, results["link"]))
    results["html"] = html
    results = results[results["html"].str.len() > 0].copy()
    results["query"] = query
    results["created"] = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
    results = results[columns]
    # Insert the search results into the database
    results.apply(lambda x: storage.insert_row(x), axis=1)
    print(f"Inserted {results.shape[0]} records.")
    return results
