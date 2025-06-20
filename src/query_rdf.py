import json

import js

import pandas as pd

import helpers
from state import RESULTS_DF, SINOPIA_GRAPH


from jinja2 import Template

query_results_template = Template(
    """
<h2>Query Results {{count}} Rows</h2>
 <div>
  <div class="dropdown">
    <button class="btn btn-secondary dropdown-toggle" 
            type="button" 
            data-bs-toggle="dropdown"
            id="rdf-download-file"
            aria-expanded="false">
      Download Results
    </button>
    <ul class="dropdown-menu" aria-labelledby="rdf-download-file">
        <li><a py-click="download_query_results" data-serialization='csv' class="dropdown-item" href="#">CSV (.csv)</a></li>
        <li><a class="dropdown-item" py-click="download_query_results" data-serialization='json' href="#">JSON (.json)</a></li>
    </ul>
  </div>
</div>
<table class="table">          
  <thead>
    <tr>
   {% for var in vars %}
     <th>{{ var }}</th>
   {% endfor %} 
    </tr>                       
  </thead>
  <tbody>
    {% for result in results %}
     <tr>
      {% for var in vars %}
      <td>{{ result[var] }}</td>
      {% endfor %}                     
     </tr> 
    {% endfor %}                        
  </tbody>
</table>             
"""
)


async def download_query_results(event):
    serialization = event.target.getAttribute("data-serialization")
    js.console.log(f"Download query results {serialization} {len(RESULTS_DF)}")
    mime_type, content = None, None
    match serialization:
        case "csv":
            mime_type = "text/csv"
            contents = RESULTS_DF.to_csv(index=False)

        case "json":
            mime_type = "application/json"
            contents = json.dumps(RESULTS_DF.to_dict(orient="records"))

        case _:
            js.alert(f"Unknown serialization {serialization}")
            return
    blob = js.Blob.new([contents], {"type": mime_type})
    anchor = js.document.createElement("a")
    anchor.href = js.URL.createObjectURL(blob)
    anchor.download = f"query-results.{serialization}"
    js.document.body.appendChild(anchor)
    anchor.click()
    js.document.body.removeChild(anchor)


async def run_query(*args):
    global RESULTS_DF
    global SINOPIA_GRAPH

    query_element = js.document.getElementById("bf-sparql-queries")
    sparql_query = query_element.value
    output_element = js.document.getElementById("bf-sparql-results")
    output_element.content = ""
    try:
        query = SINOPIA_GRAPH.query(sparql_query)
        RESULTS_DF = pd.DataFrame(query.bindings)
        output_element.innerHTML = query_results_template.render(
            count=f"{len(query.bindings):,}", vars=query.vars, results=query.bindings
        )
    except Exception as e:
        output_element.content = f"""<h2>Query Error</h2><p>{e}</p>"""
