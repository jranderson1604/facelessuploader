"""Flask web dashboard for controlling the faceless uploader."""

import json
import logging
import threading
from pathlib import Path

from flask import Flask, render_template, request, jsonify, redirect, url_for

log = logging.getLogger(__name__)


def create_app() -> Flask:
    app = Flask(
        __name__,
        template_folder=str(Path(__file__).parent / "templates"),
        static_folder=str(Path(__file__).parent / "static"),
    )

    from faceless.config import WEB_SECRET_KEY
    app.secret_key = WEB_SECRET_KEY

    @app.route("/")
    def index():
        from faceless.pipeline import get_history
        history = get_history()
        return render_template("index.html", history=history[-20:])

    @app.route("/generate", methods=["POST"])
    def generate():
        url = request.form.get("url", "").strip()
        platforms = request.form.getlist("platforms") or None
        no_upload = request.form.get("no_upload") == "on"

        if not url:
            return jsonify({"error": "URL is required"}), 400

        def _run():
            from faceless.pipeline import process_url
            process_url(url, platforms=platforms, upload=not no_upload)

        thread = threading.Thread(target=_run, daemon=True)
        thread.start()

        return jsonify({"status": "started", "message": f"Processing {url} in background"})

    @app.route("/auto", methods=["POST"])
    def auto_generate():
        count = int(request.form.get("count", 1))
        platforms = request.form.getlist("platforms") or None

        def _run():
            from faceless.pipeline import process_auto
            process_auto(count=count, platforms=platforms)

        thread = threading.Thread(target=_run, daemon=True)
        thread.start()

        return jsonify({"status": "started", "message": f"Auto-generating {count} videos"})

    @app.route("/history")
    def history_api():
        from faceless.pipeline import get_history
        return jsonify(get_history())

    @app.route("/status")
    def status():
        from faceless.pipeline import get_history
        from faceless.config import UPLOADS_PER_DAY, OUTPUT_DIR
        history = get_history()
        videos = list(OUTPUT_DIR.glob("*.mp4"))
        return jsonify({
            "total_uploads": len(history),
            "videos_on_disk": len(videos),
            "target_per_day": UPLOADS_PER_DAY,
        })

    return app
