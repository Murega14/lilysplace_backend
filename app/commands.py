import click

from app.models import User, db


def register_commands(app):
    @app.cli.command("create-superuser")
    @click.option('--username', prompt=True)
    def create_superuser(username):
        with app.app_context():
            password = click.prompt("Password", hide_input=True, confirmation_prompt=True)
            
            admin = User(username=username, role='manager')
            admin.hash_password(password)
            db.session.add(admin)
            db.session.commit()
            click.echo(f"superuser {username} has been created")