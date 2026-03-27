from flask import Flask
from flask_cors import CORS
from routes.news_routes import news_bp
from routes.job_routes import jobs_bp
from routes.saved_routes import saved_bp
from models.db import init_db

app = Flask(__name__)
CORS(app)
init_db()

app.register_blueprint(news_bp, url_prefix="/api/news")
app.register_blueprint(jobs_bp, url_prefix="/api/jobs")
app.register_blueprint(saved_bp, url_prefix="/api/saved")

@app.route("/")
def home():
    return {"message": "Tech Hub API running"}

if __name__ == "__main__":
    app.run(debug=True)