import json
import rdflib

from datetime import datetime, timedelta, UTC
from urllib.parse import urlencode

from js import alert, console, document, File, FormData, sessionStorage
from pyodide.http import AbortError, pyfetch
from state import BLUECORE_ENV, BF_GRAPH

def _expires_at(seconds: int) -> str:
    now = datetime.now(UTC)
    expires = now + timedelta(seconds=seconds)
    return expires.isoformat()


def _add_search_item(item: dict):
    alert = document.createElement("div")
    for class_ in ["alert", "alert-info", "alert-dismissible", "fade", "show"]:
        alert.classList.add(class_)
    uri = item.get('uri')
    graph = rdflib.Graph()
    graph.parse(data=item.get('data'), format='json-ld')
    alert.innerHTML = f"""<strong class="text-primary">Blue Core Resource</strong>
    <small>{item.get('type').title()}</small>
    <p>
      <a href="{uri}">{uri}</a>
    </p>
    <textarea class="d-none" id="{uri}-rdf">{graph.serialize(format='json-ld')}</textarea>
    <button type="button" class="btn btn-success"
            data-uri="{item.get('uri')}" py-click="load_uri">Load</button>
    <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
    """
    return alert


async def _get_keycloak_token():
    global BLUECORE_ENV

    username = document.getElementById("user-name")
    user_element = document.getElementById("keycloak_username")
    keycloak_username = user_element.value
    user_password = document.getElementById("keycloak_password")
    keycloak_password = user_password.value
    form_bytes = bytes(f"client_id=bluecore_api&username={keycloak_username}&password={keycloak_password}&grant_type=password",
                       encoding='utf-8')
    try:
        token_request = await pyfetch(
            f"{BLUECORE_ENV}/keycloak/realms/bluecore/protocol/openid-connect/token",
            method = "POST",
            headers={
                'Content-Type': 'application/x-www-form-urlencoded'
            },
            body=form_bytes
        )
        if token_request.ok:
            token_result = await token_request.json()
            username.innerHTML = keycloak_username
            return token_result
        else:
            error_text = await token_request.text()
            alert(f"Error retrieving token {error_text}")
    except AbortError as e:
        alert(f"Error! {e}")
        return
    
    

async def bluecore_login(event):
    close_btn = document.getElementById("loginModalhModalCloseBtn")
    tokens = await _get_keycloak_token()
    if not tokens:
        close_btn.click()
        return
    sessionStorage.setItem("keycloak_access_token", tokens.get("access_token"))
    sessionStorage.setItem("keycloak_access_expires", _expires_at(tokens.get("expires_in")))
    sessionStorage.setItem("keycloak_refresh_token", tokens.get("refresh_token"))
    sessionStorage.setItem("keycloak_refresh_expires", _expires_at(tokens.get('refresh_expires_in')))
    close_btn.click()


async def save_bluecore(event):
    global BLUECORE_ENV
    global BF_GRAPH

    if BLUECORE_ENV is None:
        alert(f"Cannot save!\nBluecore Environment not set")
        return
    if len(BF_GRAPH) < 0:
        alert(f"Cannot save empty graph")
        return
    access_token = sessionStorage.getItem("keycloak_access_token")
    form_data = FormData.new()
    
    bf_upload_file = File.new([BF_GRAPH.serialize(format='json-ld')],
                              "upload",
                              { "type": "text/plain"})
    form_data.append('file', bf_upload_file)
    bench_heading = document.getElementById("bench-heading")
    bench_bc_result = document.getElementById("bc-results")
    bench_bc_result.innerHTML = ""
    batch_result = await pyfetch(
        f"{BLUECORE_ENV}/api/batches/upload/",
        method="POST",
        headers={
            "Authorization": f"Bearer {access_token}"
        },
        body=form_data
    )
    if batch_result.ok:
        bench_heading.innerHTML = "Saving Graph to Blue Core API"
        batch_message = await batch_result.json()
        workflow_uri = f"{BLUECORE_ENV}/workflows/dags/resource_loader/runs/{batch_message.get('workflow_id')}"
        bench_bc_result.innerHTML = f"""Workflow at <a href="{workflow_uri}" target="_blank">{workflow_uri}</a>"""
    else:
        bench_heading.innerHTML = """<span class="text-danger">ERROR!!</span>"""
        bench_bc_result.innerHTML = await batch_result.text


async def search_bluecore(event):
    """
    Searches Blue Core using API
    """
    global BLUECORE_ENV

    query_elem = document.getElementById("ai-search-resources")
    bench_heading = document.getElementById("bench-heading")
    bench_bc_results = document.getElementById("bc-results")
    bench_bc_results.innerHTML = ""
    search_url = f"{BLUECORE_ENV}/api/search?" + urlencode({ "q": query_elem.value })
    search_result = await pyfetch(search_url)
    if search_result.ok:
        search_result_json = await search_result.json()
        if int(search_result_json.get('total')) < 1:
            bench_heading.innerHTML = """<h3>No results from Blue Core</h3>"""
        else:
            bench_heading.innerHTML = f"""<h3>{search_result_json.get('total')} results from Blue Core</h3>"""

        div_query = document.createElement("div")
        div_query.innerHTML = f"""<strong>Query:</strong><p>{query_elem.value}</p>"""
        bench_bc_results.append(div_query)
        for item in search_result_json.get("items", []):
            alert = _add_search_item(item)
            bench_bc_results.append(alert)


async def set_environment(this):
    global BLUECORE_ENV
    console.log(this)
    BLUECORE_ENV = this.target.getAttribute("data-env")
    bluecore_env_label = document.getElementById("bluecore-env-label")
    bluecore_env_label.innerHTML = f"for {BLUECORE_ENV}"
    sessionStorage.removeItem("keycloak_access_token")
    sessionStorage.removeItem("keycloak_access_expires")
    sessionStorage.removeItem("keycloak_refresh_token")
    sessionStorage.removeItem("keycloak_refresh_expires")