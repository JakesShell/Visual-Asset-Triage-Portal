import os
import uuid
from pathlib import Path
from flask import Flask, render_template, request
from werkzeug.utils import secure_filename

app = Flask(__name__)

UPLOAD_FOLDER = Path("static/uploads")
UPLOAD_FOLDER.mkdir(parents=True, exist_ok=True)

ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif", "webp", "bmp"}


def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def infer_asset_category(filename, workflow):
    lowered = filename.lower()

    keyword_groups = {
        "Marketing Creative": ["banner", "campaign", "social", "ad", "promo", "brand"],
        "Product Asset": ["product", "sku", "catalog", "item", "listing"],
        "Document Snapshot": ["invoice", "receipt", "report", "chart", "slide", "doc"],
        "People / Profile": ["team", "staff", "profile", "headshot", "person"]
    }

    for category, keywords in keyword_groups.items():
        if any(keyword in lowered for keyword in keywords):
            return category

    workflow_defaults = {
        "Marketing Operations": "Marketing Creative",
        "Ecommerce Content": "Product Asset",
        "Documentation Review": "Document Snapshot",
        "Internal Knowledge Base": "General Visual Asset"
    }

    return workflow_defaults.get(workflow, "General Visual Asset")


def build_review_notes(category, workflow):
    note_map = {
        "Marketing Creative": "Review branding consistency, headline visibility, and campaign-readiness before publishing.",
        "Product Asset": "Review image clarity, product framing, and catalog-readiness before listing approval.",
        "Document Snapshot": "Review readability, formatting clarity, and whether the asset belongs in structured reporting.",
        "People / Profile": "Review professionalism, framing, and internal-directory suitability.",
        "General Visual Asset": "Review whether the asset should be tagged, archived, or routed for follow-up classification."
    }

    base_note = note_map.get(category, "Review the asset and confirm the correct business use case.")
    return f"{base_note} Workflow context: {workflow}."


@app.route("/", methods=["GET", "POST"])
def index():
    result = None
    error = None

    if request.method == "POST":
        workflow = request.form.get("workflow", "Internal Knowledge Base")
        file = request.files.get("file")

        if not file or file.filename == "":
            error = "Please choose an image file to upload."
            return render_template("index.html", result=result, error=error)

        if not allowed_file(file.filename):
            error = "Unsupported file type. Upload PNG, JPG, JPEG, GIF, WEBP, or BMP."
            return render_template("index.html", result=result, error=error)

        original_name = secure_filename(file.filename)
        extension = original_name.rsplit(".", 1)[1].lower()
        saved_name = f"{uuid.uuid4().hex}.{extension}"
        save_path = UPLOAD_FOLDER / saved_name
        file.save(save_path)

        file_size_kb = round(save_path.stat().st_size / 1024, 2)
        asset_category = infer_asset_category(original_name, workflow)
        review_notes = build_review_notes(asset_category, workflow)

        result = {
            "original_name": original_name,
            "workflow": workflow,
            "asset_category": asset_category,
            "file_extension": extension.upper(),
            "file_size_kb": file_size_kb,
            "review_notes": review_notes,
            "image_path": f"uploads/{saved_name}"
        }

    return render_template("index.html", result=result, error=error)


if __name__ == "__main__":
    app.run(debug=True)
