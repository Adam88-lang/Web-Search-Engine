# Import necessary libraries
from flask import Flask, request, jsonify
from search import search
from filter import Filter
from storage import DBStorage
import html
import requests
import urllib.parse
from functools import lru_cache

# Initialize Flask
app = Flask(__name__)

# CSS styles and JavaScript for the web page
styles = """
<style>
    body {
        background: #F2F2F2;
        font-family:  sans-serif;
    }
    .site, .snippet, .rel-button {
    .site, .snippet {
        width: 50%;
        background-color: white;
        padding: 20px;
@@ -22,6 +22,16 @@
        transition: transform 0.3s ease-in-out;
    }
   a:link {
        color: yellow;
        background-color: transparent;
        text-decoration: none;
    }
    a:visited {
        color: white;
        background-color: transparent;
        text-decoration: none;
    }
    .site:hover, .snippet:hover, .rel-button:hover {
        transform: translateY(-10px);
    }
@@ -30,17 +40,25 @@
        font-size: .8rem;
        color: green;
    }

        .ellipse1 {
        /* Ellipse 1 - orange*/
        position: absolute;
        top: calc(350px - 497px);
        left: calc(350px - 497px);
        width: 447px;
        height: 418px;
        background: #D17837;
        border-radius: 50%;
    }
    .ellipse2 {
        /* Ellipse 2 */
        position: absolute;
        top: 5%;
        left: 70%;
        width: 385px;
        height: 340px;
        background: #FAFAFA;
        border-radius: 50%;
        box-shadow: 0px 4px 4px rgba(0, 0, 0, 0.25);
    }
    .ellipse3 {
        /* Ellipse 3 */
        position: absolute;
        top: 60%;
        left: 80%;
        width: 396.95px;
        height: 382.15px;
        background: #FAFAFA;
        border-radius: 50%;
        box-shadow: inset 0px 4px 4px rgba(0, 0, 0, 0.25);
        transform: rotate(0.02deg);
    }


    .large-rectangle {
        position: absolute;
        display: flex;
        flex-direction: row;
        top: 10%;
        left: 10%;
        width: 80%;
        background: #FFFFFF;
        z-index: 0;
    }
    .large-rectangle-initial {
        position: absolute;
        top: 10%;
        left: 10%;
        width: 80%;
        height: 600px;
        background: #FFFFFF;
        z-index: 0;

    }
    .search-bar-initial {
        flex: 50%;
        padding-top: 10%;
        text-align: center;
        z-index: 1;
        top: 0;
    }

   .search-bar-area {
        flex: 50%;
        padding-top: 20px;
        text-align: center;
        z-index: 1;
        top: 0;
        display: flex;
        flex-direction: column;
    }


    .search-bar img {
        position: relative;
        text-align: center;
    } 

    .results-below-search-bar {
        /* Results below Search Bar */
        position: relative;
        left: 10%;
        width: 80%;
        text-align: left;
    }

    .results-area { 
        flex: 50%;
        padding-top: 20px;
        text-align: center;
        z-index: 1;
        top: 0;
        display: flex;
        flex-direction: column;
        row-gap: 10px;
    }

    .related-rectangles {
        /* Related Rectangle */
        font-size: 14px;
        position: relative;
        left: 10%;
        width: 80%;
        background: #F2F2F2;
        text-align: left;
    }
    .snippet {
        font-size: .9rem;
        color: gray;
        margin-bottom: 30px;
    }
.rel-button {
    cursor: pointer;
    background-color: transparent; /* Changed from lightgray to transparent */
    color: blue;
    padding: 1px;
    border: none; /* Added this line to remove the border */
    margin: 0px 0 0px 20px;
    transition: transform 0.3s ease-in-out;
    cursor: pointer;
}

    .rounded-search {
        border-radius: 25px;
        border: 4px solid lightgrey;
        background: white;
        padding: 20px;
        width: 400px;
        height: 44px;
    }
    .link-text {
    font-size: 0.8rem; 
    }



    input[type="text"] {
        padding: 10px;
@@ -65,6 +83,21 @@
        cursor: pointer;
    }
</style>
<script>



function submitSearch(query) {
    const searchForm = document.getElementById('search-form');
    searchForm.elements.namedItem('query').value = query;
    searchForm.submit();
}
const relevant = function(query, link){
    fetch("/relevant", {
        method: 'POST',
        headers: {
          'Accept': 'application/json',
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
           "query": query,
           "link": link
          })
        });
}
</script>
"""

search_template = styles + """
<html>
  <head>
  </head>
  <body>
        <div class="ellipse1">   </div>
        <div class="ellipse2">   </div>
        <div class="ellipse3">   </div>
        <div class="large-rectangle-initial"> 
                <div class="search-bar-initial">
                <img src = "https://i.ibb.co/N9K2Pk1/SFCG.jpg" alt = "SearchFCG" height = "400" width = "480" />

                <form id="search-form" action="/" method="post">
                    <input class="rounded-search" type="text" name="query" placeholder="Enter Search Here">
                    <input type="submit" value="Search">
                </form>
                </div>

            <div class="results-area"> 
            </div>
        </div>


  </body>
</html>
"""

result_search_template1 = styles + """
<html>
  <head>
  </head>
  <body>
        <div class="ellipse1">   </div>
        <div class="ellipse2">   </div>
        <div class="ellipse3">   </div>
        """

result_search_template2 = """
        <div class="large-rectangle"> 
            <div class="search-bar-area"> 
                <div class="search-bar">
                    <img src = "https://i.ibb.co/N9K2Pk1/SFCG.jpg" alt = "SearchFCG" height = "300" 
                    width = "380" />
                    <form id="search-form" action="/" method="post">
                        <input class="rounded-search" type="text" name="query" placeholder="Enter Search Here">
                        <input type="submit" value="Search">
                    </form>
                </div>
                <div class="results-below-search-bar">

"""

end_search_template = """
                </div>
            </div>
        <div class="results-area"> 

"""
right_side_template = """

"""

relevant_result_template = """
<p class="site">Result {rank}: </p>
<p class="title"><a href="{link}">{title}</a></p>
<p class="snippet">{snippet}</p>
<p class="link"><a class="link-text" href="{link}">{link}</a></p>
<button class="rel-button" onclick="relevant('{query}', '{link}')">Mark as Relevant</button>
"""


related_result_template = """
<div class="related-rectangles">
    <h3>Related Keywords:</h3>
    <ul>
    {related}
    </ul>
</div>
"""

end_right_template = """
       </div>
  </body>
</html>

"""


# Show the search form
def show_search_form():
    return search_template


@lru_cache(maxsize=128)
def cached_search(query):
    return search(query)


# Perform the search and render the results
def run_search(query):
    results = cached_search(query)  # Use the cached version of search
    fi = Filter(results)
    filtered = fi.filter()
    print(f"Filtered results: {filtered}")  # Add this line to debug filtered results
    leftrendered = ""
    all_related_html = ""
    more_elipses_html = ""
    filtered["snippet"] = filtered["snippet"].apply(lambda x: html.escape(x))
    for index, row in filtered.iterrows():
        related = get_related_keywords(row["title"])
        related_html = ""
        for keyword in related:
            related_html += f'<li><a href="javascript:void(0)" onclick="submitSearch(\'{keyword}\')">{keyword}</a></li>'
        row["related"] = related_html
        leftrendered += relevant_result_template.format(**row)
        all_related_html += related_html
        if index > 0 and index % 5 == 0:
            elipsetop1 = 500 * index / 3
            elipsetop2 = elipsetop1 + 100
            elipsetop3 = elipsetop1 + 500
            more_elipses_html += f'<div class="ellipse1" style="top:{elipsetop1}px"></div>'
            more_elipses_html += f'<div class="ellipse2" style="top:{elipsetop2}px"></div>'
            more_elipses_html += f'<div class="ellipse3" style="top:{elipsetop3}px"></div>'

    right_side_template = f"""
    <div class="related-rectangles">
        <h3>Related Keywords:</h3>
        <ul>
        {all_related_html}
        </ul>
    </div>
    """

    full_template = result_search_template1 + more_elipses_html + result_search_template2 + leftrendered + end_search_template + right_side_template + end_right_template
    return full_template



# Main route to handle the search form and display results
@app.route("/", methods=['GET', 'POST'])
def search_form():
    if request.method == 'POST':
        query = request.form["query"]
        rendered = run_search(query)
        return rendered
    else:
        return show_search_form()


# Route to mark a result as relevant
@app.route("/relevant", methods=["POST"])
def mark_relevant():
    data = request.get_json()
    query = data["query"]
    link = data["link"]
    storage = DBStorage()
    storage.update_relevance(query, link, 10)
    return jsonify(success=True)


# Get related keywords for a query using the Google Custom Search API
import requests

import requests

def get_related_keywords(query):
    url = "https://en.wikipedia.org/w/api.php"
    params = {
        "action": "query",
        "format": "json",
        "list": "search",
        "srsearch": query,
        "srprop": "",
        "srinfo": "",
        "utf8": "",
    }
    response = requests.get(url, params=params)
    if response.status_code == 200:
        results = response.json()["query"]["search"]
        return [result["title"] for result in results]
    else:
        return []



    response = requests.get(url, params=params)
    if response.status_code == 200:
        results = response.json()["items"]
        return [result["title"] for result in results]
    else:
        return []
