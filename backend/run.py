from dotenv import load_dotenv
load_dotenv()

from app import create_app
from app.seed import seed_all

app = create_app()


@app.cli.command('seed')
def seed_command():
    """Seed the database with demo data."""
    with app.app_context():
        seed_all()


if __name__ == '__main__':
    with app.app_context():
        seed_all()
    app.run(debug=True, port=5000)
