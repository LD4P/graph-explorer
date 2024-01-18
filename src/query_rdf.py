import js

import helpers

from jinja2 import Template

query_results_template = Template(
    """
<h2>Query Results</h2>
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


async def run_query():
    query_element = js.document.getElementById("bf-sparql-queries")
    sparql_query = query_element.value
    output_element = js.document.getElementById("bf-sparql-results")
    output_element.innerHTML = ""
    try:
        query = helpers.sinopia_graph.query(sparql_query)

        output_element.innerHTML = query_results_template.render(
            vars=query.vars, results=query.bindings
        )
    except Exception as e:
        output_element.innerHTML = f"""<h2>Query Error</h2><p>{e}</p>"""
