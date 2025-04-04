from flask import Flask, render_template
from app.routes.sessions_routes import sessions_routes

app = Flask(__name__)
app.register_blueprint(sessions_routes)

@app.route("/")
def index():
    return render_template("index.html")

if __name__ == "__main__":
    app.run(debug=True)
