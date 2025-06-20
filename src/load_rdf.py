import json

import js
import rdflib

from jinja2 import Template
from pyodide.ffi import create_proxy
from pyodide.http import pyfetch

from state import NAMESPACES, SINOPIA_GRAPH
from sinopia_api import environments


def skolemize_resource(resource_url: str, raw_rdf: str) -> str:
    resource_graph = rdflib.Graph()
    resource_graph.parse(data=json.dumps(raw_rdf), format="json-ld")
    skolemize_graph = resource_graph.skolemize(basepath=f"{resource_url.strip()}#")
    return skolemize_graph.serialize(format="turtle")


async def _get_all_graph(api_url: str, limit: int = 250) -> None:
    next_url = f"{api_url}resource?limit={limit}"
    loading_resources = True
    while loading_resources:
        result = await pyfetch(next_url)
        payload = await result.json()
        for i, row in enumerate(payload["data"]):
            if not "data" in row:
                js.console.log(f"No data for {i}")
                continue
            if not "uri" in row:
                js.console.log("No URI for resource {i}")
                continue
            try:
                turtle_rdf = skolemize_resource(row["uri"], row["data"])
                SINOPIA_GRAPH.parse(data=turtle_rdf, format="turtle")
            except Exception as e:
                js.console.log(f"Failed to parse {row['uri']} {e}")
        next_url = payload["links"].get("next")
        if next_url is None:
            loading_resources = False
    return SINOPIA_GRAPH


async def _get_group_graph(group: str, api_url: str, limit: int = 2_500) -> None:
    start = 0
    if not api_url.endswith("/"):
        api_url = f"{api_url}/"
    initial_url = f"{api_url}resource?limit={limit}&group={group}&start={start}"
    initial_result = await pyfetch(initial_url)
    group_payload = await initial_result.json()
    for i, row in enumerate(group_payload["data"]):
        if not "data" in row:
            js.console.log(f"No RDF found for {row.get('uri', 'bad url')}")
            continue
        if not "uri" in row:
            js.console.log(f"No URI for {i}")
            continue
        try:
            turtle_rdf = skolemize_resource(row["uri"], row["data"])
            SINOPIA_GRAPH.parse(data=turtle_rdf, format="turtle")
        except Exception as e:
            js.console.log(f"Cannot load {row['uri']} Error:\n{e}")
            continue
    return SINOPIA_GRAPH


async def build_graph(*args) -> rdflib.Graph:
    global SINOPIA_GRAPH

    groups_selected = js.document.getElementById("env-groups")
    individual_resources = js.document.getElementById("resource-urls")
    sinopia_env_radio = js.document.getElementsByName("sinopia_env")
    loading_spinner = js.document.getElementById("graph-loading-status")
    loading_spinner.classList.remove("d-none")

    sinopia_api_url = None

    for elem in sinopia_env_radio:
        if elem.checked:
            sinopia_api_url = environments.get(elem.value)
    for option in groups_selected.selectedOptions:
        if option.value == "all":
            SINOPIA_GRAPH = await _get_all_graph(sinopia_api_url)
            break
        SINOPIA_GRAPH = await _get_group_graph(option.value, sinopia_api_url)

    if len(individual_resources.value) > 0:
        resources = individual_resources.value.split(",")
        for resource_url in resources:
            resource_result = await pyfetch(resource_url)
            resource_payload = await resource_result.json()
            turtle_rdf = skolemize_resource(
                resource_url.strip(), resource_payload["data"]
            )
            SINOPIA_GRAPH.parse(data=turtle_rdf, format="turtle")
    loading_spinner.classList.add("d-none")
    _summarize_graph(SINOPIA_GRAPH)
    return SINOPIA_GRAPH


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
        <li><a py-click="download_graph" data-serialization="ttl" class="dropdown-item" href="#">Turtle (.ttl)</a></li>
        <li><a class="dropdown-item" py-click="download_graph" data-serialization="xml" href="#">XML (.rdf)</a></li>
        <li><a class="dropdown-item" py-click="download_graph" data-serialization="json-ld" href="#">JSON-LD (.json)</a></li>
         <li><a class="dropdown-item" py-click="download_graph" data-serialization="nt" href="#">N3 (.nt)</a></li>
    </ul>
  </div>
</div>
"""
)


async def download_graph(event):
    anchor = event.target
    serialization = anchor.getAttribute("data-serialization")

    if len(SINOPIA_GRAPH) < 1:
        js.alert("Empty graph cannot be download")
        return
    for prefix, uri in NAMESPACES:
        SINOPIA_GRAPH.namespace_manager.bind(prefix, uri)
    mime_type, contents = None, None
    match serialization:
        case "json-ld":
            mime_type = "application/json"
            contents = SINOPIA_GRAPH.serialize(format="json-ld")

        case "nt":
            mime_type = "application/n-triples"
            contents = SINOPIA_GRAPH.serialize(format="nt")

        case "ttl":
            mime_type = "application/x-turtle"
            contents = SINOPIA_GRAPH.serialize(format="turtle")

        case "xml":
            mime_type = "application/rdf+xml"
            contents = SINOPIA_GRAPH.serialize(format="pretty-xml")

        case _:
            js.alert(f"Unknown RDF serialization {serialization}")
            return
    blob = js.Blob.new([contents], {"type": mime_type})
    anchor = js.document.createElement("a")
    anchor.href = js.URL.createObjectURL(blob)
    anchor.download = f"sinopia-graph.{serialization}"
    js.document.body.appendChild(anchor)
    anchor.click()
    js.document.body.removeChild(anchor)


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
    <button class="btn btn-primary" py-click="run_query">Run query</button>
  </div>
</div>"""
)


def bibframe_sparql(element_id: str):
    wrapper_div = js.document.getElementById(element_id)
    all_namespaces = NAMESPACES + [("rdf", rdflib.RDF), ("rdfs", rdflib.RDFS)]
    wrapper_div.innerHTML = sparql_template.render(namespaces=all_namespaces)
