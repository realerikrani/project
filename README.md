# project

Add private and public key based project management API endpoints to your flask app.

See the docs folder in the GitHub repository for specific info about endpoints.

Set the location where the SQLite database `PROJECT_DATABASE_PATH` would be created.

```bash
export PROJECT_DATABASE_PATH=/path/to/your/db.sqlite
```

... and call the `register_project` function to set up the endpoints
and general API error handling.

```py
from flask import Flask

from realerikrani.project import register_project

if __name__ == "__main__":
    app = register_project(Flask("your_app_name"))
    app.run(port=8080, debug=True)
```