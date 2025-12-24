Write a devdocs MCP server in Python.
Use poetry to manage dependencies.
Use fastmcp to run MCP server in stdio or Streaming HTTP mode.
It should extract docs from ghcr.io/freecodecamp/devdocs docker image path /devdocs/public/docs.
Write a script to do this.
Place it into the docs folder in this repo.
Add the docs and `__pycache__` folder to .gitignore.
The MCP server provides a tool to search for docs in the docs folder.
It provides another tool to read one specific doc in Markdown format.
You can convert HTML to Markdown if feasible.
If the specific docs path does not exists, use fuzzy matching.
Provide a CLI to start the server.
Also provide a CLI to search/view devdocs directly.
Write tests.
Setup GitHub Actions.
Create git commits using convential commit message.
