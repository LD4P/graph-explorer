import asyncio
import sys
import js
import pathlib
import tomllib


from pyodide.ffi import create_proxy
from pyodide.http import pyfetch

import helpers

import rdflib


FILE = pathlib.Path(".")

SINOPIA = rdflib.Namespace("http://sinopia.io/vocabulary/")

from bluecore_api import bluecore_login, save_bluecore, search_bluecore, set_environment
from sinopia_api import show_groups
from load_rdf import bibframe_sparql as bf_sparql_widget, build_graph, download_graph, load_cbd_file, load_uri
from marc import bf2marc, marc2bf
from query_rdf import download_query_results, run_query, run_summary_query

bf_sparql_widget("bf-sparql-query")

async def retrieve_version():
    pyproject_request = await pyfetch("pyproject.toml")
    pyproject = await pyproject_request.text()
    project = tomllib.loads(pyproject)
    version = project["project"]["version"]
    return version


version = await retrieve_version()

helpers.set_versions(version)

splash_modal_close_btn = js.document.getElementById("splashModalCloseBtn")
splash_modal_close_btn.click()
