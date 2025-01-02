import os

os.environ["PROJECT_DATABASE_PATH"] = "./projects.sqlite"

from flask import Flask

from realerikrani.project.app import register_project

if __name__ == "__main__":
    app = register_project(Flask("demo"))
    app.run(port=8080, debug=False)
