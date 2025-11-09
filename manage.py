from flask.cli import FlaskGroup

from src import app

# Flask 3.x expects a create_app callback; passing the app object directly no longer works
cli = FlaskGroup(create_app=lambda: app)


if __name__ == "__main__":
    cli()
