from flask import Flask, render_template, request, redirect, url_for, send_file, flash
from io import BytesIO
from middleware.blob_service import get_client, get_active_provider, set_active_provider
from dotenv import load_dotenv
import os

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "demo")

@app.route("/")
def index():
    client = get_client()
    files = client.list()
    return render_template("index.html", files=files, active=get_active_provider())

@app.post("/switch")
def switch():
    provider = request.form.get("provider")
    set_active_provider(provider)
    flash(f"Switched to {provider.upper()} successfully!", "success")
    return redirect(url_for("index"))

@app.post("/upload")
def upload():
    f = request.files.get("file")
    if not f or f.filename == "":
        flash("Choose a file first.", "error")
        return redirect(url_for("index"))
    client = get_client()
    client.upload(f.stream, f.filename)
    flash(f"Uploaded {f.filename}!", "success")
    return redirect(url_for("index"))

@app.get("/download/<key>")
def download(key):
    data = get_client().download(key)
    return send_file(BytesIO(data), as_attachment=True, download_name=key)

@app.post("/delete/<key>")
def delete(key):
    get_client().delete(key)
    flash(f"Deleted {key}", "success")
    return redirect(url_for("index"))

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
