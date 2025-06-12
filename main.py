__version__ = "1.0.0"
import asyncio
import sys
import js


from pyodide.ffi import create_proxy

import helpers

import rdflib

BIBFRAME = rdflib.Namespace("http://id.loc.gov/ontologies/bibframe/")
SINOPIA = rdflib.Namespace("http://sinopia.io/vocabulary/")

from helpers import bluecore_login
from sinopia_api import show_groups
from load_rdf import bibframe_sparql as bf_sparql_widget, build_graph, download_graph
from query_rdf import download_query_results, run_query


bf_sparql_widget("bf-sparql-query")

helpers.set_versions(__version__)

splash_modal_close_btn = js.document.getElementById("splashModalCloseBtn")
splash_modal_close_btn.click()
