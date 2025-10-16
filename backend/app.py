from flask import Flask, jsonify, request, send_from_directory
import os, logging
from logging.handlers import RotatingFileHandler
import mysql.connector

app = Flask(__name__, static_folder="static", static_url_path="/static")

# 日志配置（写入 /var/log/myapp/error.log）
log_dir = "/var/log/myapp"
os.makedirs(log_dir, exist_ok=True)
handler = RotatingFileHandler(os.path.join(log_dir, "error.log"), maxBytes=5*1024*1024, backupCount=3, encoding="utf-8")
handler.setLevel(logging.ERROR)
formatter = logging.Formatter('%(asctime)s %(levelname)s %(name)s: %(message)s')
handler.setFormatter(formatter)
app.logger.addHandler(handler)
# CI/CD trigger test

@app.route("/health")
def health():
    return jsonify({"status":"ok"})

@app.route("/api/users")
def users():
    try:
        conn = mysql.connector.connect(
            host=os.getenv("MYSQL_HOST","mysql"),
            user=os.getenv("MYSQL_USER","root"),
            password=os.getenv("MYSQL_PASSWORD","example"),
            database=os.getenv("MYSQL_DATABASE","mydb")
        )
        cur = conn.cursor(dictionary=True)
        cur.execute("SELECT id, name FROM users LIMIT 100")
        rows = cur.fetchall()
        cur.close()
        conn.close()
        return jsonify({"users": rows})
    except Exception as e:
        app.logger.error("DB error: %s", e, exc_info=True)
        return jsonify({"error":"db error"}), 500

@app.route("/api/do_something", methods=["POST"])
def do_something():
    data = request.json or {}
    try:
        if data.get("cause_error"):
            raise ValueError("Simulated error")
        return jsonify({"result":"ok","data":data})
    except Exception as e:
        app.logger.error("Error in /api/do_something: %s", e, exc_info=True)
        return jsonify({"error":"internal"}), 500

# 静态前端
@app.route("/", defaults={"path":""})
@app.route("/<path:path>")
def front(path):
    if path and os.path.exists(os.path.join(app.static_folder, path)):
        return send_from_directory(app.static_folder, path)
    return send_from_directory(app.static_folder, "index.html")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)
