# project

This project is licensed under [Apache License 2.0](./LICENSE-Apache-2.0), see [NOTICE](./NOTICE).

## Direct dependencies

- [Flask](https://github.com/pallets/flask) - licensed under [BSD 3-Clause license](./LICENSE-BSD-3-Clause-flask)
- [pyjwt[crypto]](https://github.com/jpadilla/pyjwt) - licensed under [MIT License](./LICENSE-MIT-pyjwt)
- [realerikrani-sopenqlite](https://github.com/realerikrani/sopenqlite) - licensed under [Apache License 2.0](./LICENSE-Apache-2.0)
- [realerikrani-flaskapierr](https://github.com/realerikrani/flaskapierr) - licensed under [Apache License 2.0](./LICENSE-Apache-2.0)
- [realerikrani-base64token](https://github.com/realerikrani/base64token) - licensed under [Apache License 2.0](./LICENSE-Apache-2.0)

## What's it about

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