import json

import js
import rdflib

from jinja2 import Template
from pyodide.ffi import create_proxy
from pyodide.http import pyfetch

from helpers import NAMESPACES, sinopia_graph
from sinopia_api import environments


async def _get_group_graph(group: str, api_url: str, limit: int = 2_500) -> list:
    urls = []
    start = 0
    if not api_url.endswith("/"):
        api_url = f"{api_url}/"
    initial_url = f"{api_url}resource?limit={limit}&group={group}&start={start}"
    initial_result = await pyfetch(initial_url)
    group_payload = await initial_result.json()
    for row in group_payload["data"]:
        sinopia_graph.parse(data=json.dumps(row["data"]), format="json-ld")
    js.console.log(f"Total size of graph {len(sinopia_graph)} triples")
    return


async def build_graph() -> rdflib.Graph:
    groups_selected = js.document.getElementById("env-groups")
    sinopia_env_radio = js.document.getElementsByName("sinopia_env")
    sinopia_api_url = None
    for elem in sinopia_env_radio:
        if elem.checked:
            sinopia_api_url = environments.get(elem.value)

    for option in groups_selected.selectedOptions:
        await _get_group_graph(option.value, sinopia_api_url)

    js.console.log(f"Sinopia graph size {len(sinopia_graph)}")
    _summarize_graph(sinopia_graph)


bf_summary_template = Template(
    """<table class="table">
  <thead>
     <tr>
        <th>Description</th>
        <th>Value</th>
     </tr>
  </thead>
  <tbody>
     <tr>
        <td>Total Triples</td>
        <td>{{ graph|length }}</td>
     </tr>
     <tr>
        <td>Subjects</td>
        <td>{{ counts.subjCount }}</td>
     </tr>
     <tr>
        <td>Predicates</td>
        <td>{{ counts.predCount }}</td>
     </tr>
     <tr>
        <td>Objects</td>
        <td>{{ counts.objCount }}</td>
     </tr>
  </tbody>
</table>
<div class="mb-3">
  <div class="dropdown">
    <button class="btn btn-secondary dropdown-toggle" 
            type="button" 
            data-bs-toggle="dropdown"
            id="rdf-download-file"
            aria-expanded="false">
      Download Graph
    </button>
    <ul class="dropdown-menu" aria-labelledby="rdf-download-file">
        <li><a class="dropdown-item" href="#">Turtle (.ttl)</a></li>
        <li><a class="dropdown-item" href="#">XML (.rdf)</a></li>
        <li><a class="dropdown-item" href="#">JSON-LD (.json)</a></li>
         <li><a class="dropdown-item" href="#">N3 (.nt)</a></li>
    </ul>
  </div>
</div>
"""
)


def _summarize_graph(graph: rdflib.Graph):
    summary_div = js.document.getElementById("summarize-work-instance-item")
    query_result = graph.query(
        """SELECT (count(DISTINCT ?s) as ?subjCount) (count(DISTINCT ?p) as ?predCount) (count(DISTINCT ?o) as ?objCount) 
    WHERE { ?s ?p ?o . }"""
    )
    summary_div.innerHTML = bf_summary_template.render(
        graph=graph, counts=query_result.bindings[0]
    )


bf_template = Template(
    """<div class="col">
{% for bf_entity in entities %}
  {% set id = bf_entity[1].split("/")[-1] %}
  <div class="mb-3">
    <label for="{{ id }}" class="col-form-label">BIBFRAME {{ bf_entity[0] }} URL</label> 
    <input type="text" id="{{ id }}" class="form-control bf-entity" value="{{ bf_entity[1] }}">
  </div>
{% endfor %}
  <button type="button" id="build-graph-btn" class="btn btn-primary">Build RDF Graph</button>
</div>"""
)


def bibframe(element_id: str, urls: list):
    form_element = js.document.getElementById(element_id)
    form_element.classList.add("col")
    entities = zip(("Work", "Instance", "Item"), urls)
    form_element.innerHTML = bf_template.render(entities=entities)
    button = js.document.getElementById("build-graph-btn")
    button.addEventListener("click", create_proxy(_build_graph))


sparql_template = Template(
    """<div class="mb-3">
    <label for="bf-sparql-queries" class="form-label">SPARQL Query</label>
    <textarea class="form-control" id="bf-sparql-queries" rows="10">
    {% for ns in namespaces %}PREFIX {{ ns[0] }}: <{{ ns[1] }}>\n{% endfor %}
    </textarea>
  </div>
  <div class="mb-3">
    <button class="btn btn-primary" py-click="asyncio.ensure_future(run_query())">Run query</button>
  </div>
</div>"""
)


def bibframe_sparql(element_id: str):
    wrapper_div = js.document.getElementById(element_id)
    all_namespaces = NAMESPACES + [("rdf", rdflib.RDF), ("rdfs", rdflib.RDFS)]
    js.console.log(f"All namespaces {all_namespaces}")
    wrapper_div.innerHTML = sparql_template.render(namespaces=all_namespaces)
