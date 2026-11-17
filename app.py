import os
from datetime import datetime
from pathlib import Path

import mysql.connector
from mysql.connector import Error
from flask import Flask, render_template, request, redirect, url_for, flash, abort
from dotenv import load_dotenv
from werkzeug.utils import secure_filename

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")
UPLOAD_DIR = BASE_DIR / "static" / "uploads"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "change-this-development-secret")
app.config["MAX_CONTENT_LENGTH"] = 5 * 1024 * 1024  # 5 MB upload limit
app.config["UPLOAD_FOLDER"] = str(UPLOAD_DIR)

ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "webp", "gif"}

def db_connection():
    """Open a fresh MySQL connection for this request."""
    return mysql.connector.connect(
        host=os.getenv("DB_HOST"),
        port=int(os.getenv("DB_PORT")),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD", ""),
        database=os.getenv("DB_NAME"),
    )

def query_db(sql, params=(), fetch=True, commit=True):
    conn = db_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute(sql, params)
        result = cursor.fetchall() if fetch else cursor.lastrowid
        if commit:
            conn.commit()
        return result
    finally:
        cursor.close()
        conn.close()

def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS

def save_poster(file):
    if not file or not file.filename:
        return None
    if not allowed_file(file.filename):
        raise ValueError("Poster must be PNG, JPG, JPEG, WEBP or GIF.")
    safe_name = secure_filename(file.filename)
    ext = safe_name.rsplit(".", 1)[1].lower()
    # Timestamp prefix avoids collisions and unsafe user-controlled paths.
    filename = f"{datetime.utcnow().strftime('%Y%m%d%H%M%S%f')}.{ext}"
    file.save(UPLOAD_DIR / filename)
    return url_for("static", filename=f"uploads/{filename}")

def get_anime(anime_id):
    rows = query_db("SELECT * FROM anime WHERE id = %s", (anime_id,), fetch=True)
    if not rows:
        abort(404)
    return rows[0]

def form_values():
    title = request.form.get("title", "").strip()
    if not title:
        raise ValueError("Anime title is required.")
    total = max(0, int(request.form.get("total_episodes") or 0))
    watched = max(0, int(request.form.get("watched_episodes") or 0))
    if total and watched > total:
        raise ValueError("Watched episodes cannot exceed total episodes.")
    rating = float(request.form.get("rating") or 0)
    if rating < 0 or rating > 10:
        raise ValueError("Rating must be between 0 and 10.")
    status = request.form.get("status", "Plan to Watch")
    valid_statuses = {"Watching", "Completed", "Plan to Watch", "On Hold", "Dropped"}
    if status not in valid_statuses:
        raise ValueError("Choose a valid watch status.")
    if total and watched == total and watched > 0:
        status = "Completed"
    return {
        "title": title,
        "genre": request.form.get("genre", "").strip(),
        "total_episodes": total,
        "watched_episodes": watched,
        "status": status,
        "rating": rating,
        "notes": request.form.get("notes", "").strip(),
        "image_url": request.form.get("image_url", "").strip(),
        "is_favorite": 1 if request.form.get("is_favorite") == "on" else 0,
    }

@app.route("/")
def index():
    search = request.args.get("q", "").strip()
    status = request.args.get("status", "").strip()
    sort = request.args.get("sort", "recent")
    allowed_sorts = {
        "recent": "created_at DESC",
        "title": "title ASC",
        "rating": "rating DESC, title ASC",
        "progress": "watched_episodes DESC",
    }
    where, params = [], []
    if search:
        where.append("(title LIKE %s OR genre LIKE %s)")
        params.extend([f"%{search}%", f"%{search}%"])
    if status in {"Watching", "Completed", "Plan to Watch", "On Hold", "Dropped"}:
        where.append("status = %s")
        params.append(status)
    sql = "SELECT * FROM anime"
    if where:
        sql += " WHERE " + " AND ".join(where)
    sql += " ORDER BY " + allowed_sorts.get(sort, allowed_sorts["recent"])
    anime = query_db(sql, tuple(params), fetch=True)

    stats_rows = query_db("""
        SELECT COUNT(*) AS total,
               SUM(status = 'Watching') AS watching,
               SUM(status = 'Completed') AS completed,
               SUM(status = 'Plan to Watch') AS planned,
               COALESCE(AVG(NULLIF(rating, 0)), 0) AS avg_rating,
               COALESCE(SUM(watched_episodes), 0) AS episodes
        FROM anime
    """, fetch=True)
    stats = stats_rows[0]
    return render_template("index.html", anime=anime, stats=stats,
                           search=search, selected_status=status, selected_sort=sort)

@app.route("/anime/new", methods=["GET", "POST"])
def add_anime():
    if request.method == "POST":
        try:
            data = form_values()
            uploaded = save_poster(request.files.get("poster"))
            if uploaded:
                data["image_url"] = uploaded
            query_db("""
                INSERT INTO anime
                (title, genre, total_episodes, watched_episodes, status, rating,
                 notes, image_url, is_favorite)
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)
            """, tuple(data.values()), commit=True)
            flash("Anime added to your collection!", "success")
            return redirect(url_for("index"))
        except ValueError as exc:
            flash(str(exc), "error")
        except Error:
            app.logger.exception("MySQL insert failed")
            flash("Could not save anime. Check your MySQL connection and table setup.", "error")
    return render_template("form.html", item=None, page_title="Add anime")

@app.route("/anime/<int:anime_id>/edit", methods=["GET", "POST"])
def edit_anime(anime_id):
    item = get_anime(anime_id)
    if request.method == "POST":
        try:
            data = form_values()
            uploaded = save_poster(request.files.get("poster"))
            if uploaded:
                data["image_url"] = uploaded
            query_db("""
                UPDATE anime SET title=%s, genre=%s, total_episodes=%s,
                watched_episodes=%s, status=%s, rating=%s, notes=%s,
                image_url=%s, is_favorite=%s WHERE id=%s
            """, tuple(data.values()) + (anime_id,), commit=True)
            flash("Anime details updated.", "success")
            return redirect(url_for("index"))
        except ValueError as exc:
            flash(str(exc), "error")
        except Error:
            app.logger.exception("MySQL update failed")
            flash("Could not update anime. Check your database connection.", "error")
    return render_template("form.html", item=item, page_title="Edit anime")

@app.post("/anime/<int:anime_id>/delete")
def delete_anime(anime_id):
    query_db("DELETE FROM anime WHERE id = %s", (anime_id,), commit=True)
    flash("Anime removed from your collection.", "success")
    return redirect(url_for("index"))

@app.post("/anime/<int:anime_id>/favorite")
def toggle_favorite(anime_id):
    query_db("UPDATE anime SET is_favorite = NOT is_favorite WHERE id = %s",
             (anime_id,), commit=True)
    return redirect(request.referrer or url_for("index"))

@app.post("/anime/<int:anime_id>/progress")
def update_progress(anime_id):
    action = request.form.get("action")
    item = get_anime(anime_id)
    watched = item["watched_episodes"]
    if action == "plus":
        watched += 1
    elif action == "minus":
        watched = max(0, watched - 1)
    if item["total_episodes"]:
        watched = min(watched, item["total_episodes"])
    status = "Completed" if item["total_episodes"] and watched == item["total_episodes"] else item["status"]
    if status == "Completed" and watched < item["total_episodes"]:
        status = "Watching"
    query_db("UPDATE anime SET watched_episodes=%s, status=%s WHERE id=%s",
             (watched, status, anime_id), commit=True)
    return redirect(request.referrer or url_for("index"))

@app.errorhandler(413)
def too_large(_error):
    flash("Poster is too large. Maximum upload size is 5 MB.", "error")
    return redirect(request.referrer or url_for("add_anime"))

@app.route("/health")
def health():
    try:
        query_db("SELECT 1", fetch=True)
        return {"status": "ok", "database": "connected"}
    except Error:
        return {"status": "error", "database": "unavailable"}, 503

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", "5000")), debug=os.getenv("FLASK_DEBUG") == "1")
