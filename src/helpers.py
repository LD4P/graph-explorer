import js
import markdown

from js import document, console


async def bluecore_login(event):
    console.log(f"Starting Blue Core Login")
   
    

def set_versions(version):
    version_element = document.getElementById("version")
    footer_version = document.getElementById("footer-version")
    version_element.innerHTML = version
    footer_version.innerHTML = version


async def render_markdown(element_id):
    element = document.getElementById(element_id)
    if element is None:
        return
    raw_mkdwn = element.innerText
    element.innerHTML = markdown.markdown(raw_mkdwn)


def run_step_01(event):
    stage_urls = js.document.querySelector("#sinopia-stage-urls")
    output = js.document.querySelector("#step-01-output")
    raw_input = stage_urls.value
    try:
        exec(raw_input)
        js.console.log(globals())
        output.innerHTML = f"sinopia_urls has ${len(sinopia_stage_urls)}"
    except Exception as e:
        output.innerHTML = f"Error {e} loading {stage_urls.value}"
 
