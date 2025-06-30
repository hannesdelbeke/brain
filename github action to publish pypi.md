- copy the publish action
- set the `PYPI_API_TOKEN` token in `settings / secrets & variables / Actions`
	- either copy from pass-mngr or create a new one in py-pi
- package your project with a [[pyproject.toml]]
- create a github release

for first time, use a all py-pi access API key
then once uploaded, you can generate a project specific API key in [[Python Package Index|PyPI]] and update the API key in your [[GitHub repo]].