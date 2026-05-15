from __future__ import annotations

import json
import os
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from flask import Flask, flash, redirect, render_template, request, send_from_directory, url_for
from PIL import Image, UnidentifiedImageError
from werkzeug.utils import secure_filename


BASE_DIR = Path(__file__).resolve().parent
UPLOAD_FOLDER = BASE_DIR / "uploads"
DATA_FOLDER = BASE_DIR / "data"
ASSETS_FILE = DATA_FOLDER / "assets.json"
AUDIT_FILE = DATA_FOLDER / "audit_log.json"

ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "webp"}
MAX_UPLOAD_MB = 8

app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get("ASSETLENS_SECRET_KEY", "assetlens-local-demo-secret")
app.config["UPLOAD_FOLDER"] = str(UPLOAD_FOLDER)
app.config["MAX_CONTENT_LENGTH"] = MAX_UPLOAD_MB * 1024 * 1024

UPLOAD_FOLDER.mkdir(exist_ok=True)
DATA_FOLDER.mkdir(exist_ok=True)


def utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")


def read_json(path: Path, fallback: Any) -> Any:
    if not path.exists():
        return fallback

    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return fallback


def write_json(path: Path, payload: Any) -> None:
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def get_assets() -> list[dict[str, Any]]:
    return read_json(ASSETS_FILE, [])


def save_assets(assets: list[dict[str, Any]]) -> None:
    write_json(ASSETS_FILE, assets)


def get_audit_log() -> list[dict[str, Any]]:
    return read_json(AUDIT_FILE, [])


def save_audit_log(logs: list[dict[str, Any]]) -> None:
    write_json(AUDIT_FILE, logs)


def add_audit_event(asset_id: str, action: str, details: str, actor: str = "System") -> None:
    logs = get_audit_log()
    logs.insert(
        0,
        {
            "event_id": str(uuid.uuid4()),
            "asset_id": asset_id,
            "action": action,
            "details": details,
            "actor": actor,
            "timestamp": utc_now(),
        },
    )
    save_audit_log(logs[:250])


def allowed_file(filename: str) -> bool:
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def validate_image(file_path: Path) -> tuple[int, int]:
    try:
        with Image.open(file_path) as img:
            img.verify()

        with Image.open(file_path) as img:
            width, height = img.size

        return width, height
    except UnidentifiedImageError as exc:
        raise ValueError("Uploaded file is not a valid image.") from exc


def calculate_metadata_score(asset: dict[str, Any]) -> int:
    required_fields = [
        "campaign_name",
        "department",
        "asset_type",
        "usage_rights",
        "publish_channel",
        "owner",
        "description",
    ]

    completed = sum(1 for field in required_fields if asset.get(field))
    score = round((completed / len(required_fields)) * 100)

    if asset.get("usage_rights") == "Confirmed":
        score += 5

    return min(score, 100)


def calculate_risk(asset: dict[str, Any]) -> tuple[int, list[str]]:
    risk = 0
    reasons: list[str] = []

    if not asset.get("campaign_name"):
        risk += 12
        reasons.append("Missing campaign name.")

    if not asset.get("owner"):
        risk += 10
        reasons.append("Missing asset owner.")

    if not asset.get("description"):
        risk += 8
        reasons.append("Missing visual description.")

    if asset.get("usage_rights") in {"Unknown", "Not Provided", ""}:
        risk += 32
        reasons.append("Usage rights are not confirmed.")

    if asset.get("usage_rights") == "Expires Soon":
        risk += 22
        reasons.append("Usage rights may expire soon.")

    if asset.get("publish_channel") == "Paid Ads" and asset.get("usage_rights") != "Confirmed":
        risk += 20
        reasons.append("Paid advertising requires confirmed usage rights.")

    if asset.get("file_size_mb", 0) > 5:
        risk += 7
        reasons.append("Large image file may need optimization.")

    if asset.get("width", 0) < 900 or asset.get("height", 0) < 600:
        risk += 8
        reasons.append("Image resolution may be too small for campaign use.")

    if asset.get("department") in {"Healthcare", "Education", "Legal"}:
        risk += 8
        reasons.append("Department requires stronger governance review.")

    if asset.get("urgency") == "Critical":
        risk += 5
        reasons.append("Critical urgency increases operational review risk.")

    return min(risk, 100), reasons


def risk_level(score: int) -> str:
    if score >= 70:
        return "High"
    if score >= 40:
        return "Medium"
    return "Low"


def route_workflow(asset: dict[str, Any]) -> str:
    if asset.get("usage_rights") != "Confirmed":
        return "Compliance Review"

    if asset.get("department") in {"Brand", "Marketing"}:
        return "Brand Approval"

    if asset.get("department") == "E-commerce":
        return "Product Content Review"

    if asset.get("department") in {"Healthcare", "Education", "Legal"}:
        return "Governance Review"

    if asset.get("publish_channel") == "Client Portal":
        return "Client Approval"

    return "Marketing Operations"


def recommended_action(asset: dict[str, Any], score: int) -> str:
    if score >= 70:
        return "Hold asset. Escalate to compliance before release."

    if score >= 40:
        return "Request metadata updates before approval."

    if asset.get("usage_rights") == "Confirmed":
        return "Ready for reviewer approval."

    return "Confirm usage rights before publishing."


def priority(asset: dict[str, Any], risk_score: int) -> str:
    if asset.get("urgency") == "Critical" or risk_score >= 70:
        return "P1"
    if asset.get("urgency") == "High" or risk_score >= 40:
        return "P2"
    return "P3"


def enrich_asset(asset: dict[str, Any]) -> dict[str, Any]:
    metadata_score = calculate_metadata_score(asset)
    governance_risk_score, risk_reasons = calculate_risk(asset)

    asset["metadata_score"] = metadata_score
    asset["governance_risk_score"] = governance_risk_score
    asset["risk_level"] = risk_level(governance_risk_score)
    asset["risk_reasons"] = risk_reasons
    asset["workflow_route"] = route_workflow(asset)
    asset["recommended_action"] = recommended_action(asset, governance_risk_score)
    asset["priority"] = priority(asset, governance_risk_score)

    return asset


def find_asset(asset_id: str) -> dict[str, Any] | None:
    return next((asset for asset in get_assets() if asset["asset_id"] == asset_id), None)


def dashboard_metrics(assets: list[dict[str, Any]]) -> dict[str, Any]:
    total = len(assets)
    high_risk = sum(1 for asset in assets if asset["risk_level"] == "High")
    pending = sum(1 for asset in assets if asset["review_status"] in {"Pending Review", "Needs Metadata", "Compliance Review"})
    approved = sum(1 for asset in assets if asset["review_status"] == "Approved")
    avg_metadata = round(sum(asset["metadata_score"] for asset in assets) / total) if total else 0

    return {
        "total": total,
        "high_risk": high_risk,
        "pending": pending,
        "approved": approved,
        "avg_metadata": avg_metadata,
    }


@app.route("/")
def index():
    assets = [enrich_asset(asset) for asset in get_assets()]
    assets = sorted(assets, key=lambda item: (item["review_status"] == "Approved", item["governance_risk_score"]), reverse=True)
    metrics = dashboard_metrics(assets)
    logs = get_audit_log()[:8]

    return render_template("index.html", assets=assets, metrics=metrics, logs=logs)


@app.route("/upload", methods=["POST"])
def upload_asset():
    uploaded_file = request.files.get("asset_file")

    if not uploaded_file or uploaded_file.filename == "":
        flash("Please choose an image to upload.", "error")
        return redirect(url_for("index"))

    if not allowed_file(uploaded_file.filename):
        flash("Only PNG, JPG, JPEG, and WEBP files are allowed.", "error")
        return redirect(url_for("index"))

    original_name = secure_filename(uploaded_file.filename)
    extension = original_name.rsplit(".", 1)[1].lower()
    stored_name = f"{uuid.uuid4()}.{extension}"
    file_path = UPLOAD_FOLDER / stored_name

    uploaded_file.save(file_path)

    try:
        width, height = validate_image(file_path)
    except ValueError as exc:
        file_path.unlink(missing_ok=True)
        flash(str(exc), "error")
        return redirect(url_for("index"))

    file_size_mb = round(file_path.stat().st_size / (1024 * 1024), 2)

    asset = {
        "asset_id": str(uuid.uuid4()),
        "original_file_name": original_name,
        "stored_file_name": stored_name,
        "file_type": extension.upper(),
        "file_size_mb": file_size_mb,
        "width": width,
        "height": height,
        "campaign_name": request.form.get("campaign_name", "").strip(),
        "department": request.form.get("department", "").strip(),
        "asset_type": request.form.get("asset_type", "").strip(),
        "usage_rights": request.form.get("usage_rights", "Unknown").strip(),
        "publish_channel": request.form.get("publish_channel", "").strip(),
        "owner": request.form.get("owner", "").strip(),
        "urgency": request.form.get("urgency", "Normal").strip(),
        "description": request.form.get("description", "").strip(),
        "review_status": "Pending Review",
        "review_notes": "Awaiting first reviewer decision.",
        "created_at": utc_now(),
        "updated_at": utc_now(),
    }

    asset = enrich_asset(asset)

    if asset["risk_level"] == "High":
        asset["review_status"] = "Compliance Review"
    elif asset["metadata_score"] < 70:
        asset["review_status"] = "Needs Metadata"

    assets = get_assets()
    assets.insert(0, asset)
    save_assets(assets)

    add_audit_event(asset["asset_id"], "Asset Uploaded", f"{asset['original_file_name']} routed to {asset['workflow_route']}.")

    flash("Asset uploaded and triaged successfully.", "success")
    return redirect(url_for("index"))


@app.route("/asset/<asset_id>")
def asset_detail(asset_id: str):
    asset = find_asset(asset_id)

    if asset is None:
        flash("Asset not found.", "error")
        return redirect(url_for("index"))

    asset = enrich_asset(asset)
    logs = [log for log in get_audit_log() if log["asset_id"] == asset_id]

    return render_template("asset_detail.html", asset=asset, logs=logs)


@app.route("/decision/<asset_id>", methods=["POST"])
def decision(asset_id: str):
    assets = get_assets()
    asset = next((item for item in assets if item["asset_id"] == asset_id), None)

    if asset is None:
        flash("Asset not found.", "error")
        return redirect(url_for("index"))

    decision_value = request.form.get("decision", "Pending Review")
    reviewer = request.form.get("reviewer", "AssetLens Reviewer").strip() or "AssetLens Reviewer"
    notes = request.form.get("review_notes", "").strip()

    allowed_decisions = {"Approved", "Approved With Exception", "Rejected", "Needs Metadata", "Compliance Review", "Client Approval"}

    if decision_value not in allowed_decisions:
        flash("Invalid review decision.", "error")
        return redirect(url_for("asset_detail", asset_id=asset_id))

    evaluated_asset = enrich_asset(asset.copy())
    unsafe_for_normal_approval = (
        evaluated_asset["risk_level"] == "High"
        or evaluated_asset["governance_risk_score"] >= 70
        or evaluated_asset.get("usage_rights") in {"Unknown", "Not Provided", "Expires Soon", ""}
    )

    if decision_value == "Approved" and unsafe_for_normal_approval:
        flash(
            "Normal approval is blocked for this asset. Confirm usage rights, reduce risk, or use Approved With Exception with reviewer notes.",
            "error",
        )
        return redirect(url_for("asset_detail", asset_id=asset_id))

    if decision_value == "Approved With Exception" and len(notes) < 12:
        flash("Approved With Exception requires clear reviewer notes explaining the override.", "error")
        return redirect(url_for("asset_detail", asset_id=asset_id))

    asset["review_status"] = decision_value
    asset["review_notes"] = notes or f"Decision updated to {decision_value}."
    asset["updated_at"] = utc_now()

    save_assets(assets)
    add_audit_event(asset_id, f"Decision: {decision_value}", asset["review_notes"], reviewer)

    flash("Review decision saved.", "success")
    return redirect(url_for("asset_detail", asset_id=asset_id))


@app.route("/uploads/<filename>")
def uploaded_file(filename: str):
    safe_name = secure_filename(filename)
    return send_from_directory(app.config["UPLOAD_FOLDER"], safe_name)


@app.route("/seed")
def seed_demo_data():
    demo_assets = [
        {
            "asset_id": "demo-001",
            "original_file_name": "spring-launch-hero.webp",
            "stored_file_name": "",
            "file_type": "WEBP",
            "file_size_mb": 2.4,
            "width": 1800,
            "height": 1200,
            "campaign_name": "Spring Launch",
            "department": "Marketing",
            "asset_type": "Hero Image",
            "usage_rights": "Confirmed",
            "publish_channel": "Website",
            "owner": "Marketing Operations",
            "urgency": "High",
            "description": "Main campaign hero image for the spring product launch.",
            "review_status": "Approved",
            "review_notes": "Approved for website and social launch usage.",
            "created_at": utc_now(),
            "updated_at": utc_now(),
        },
        {
            "asset_id": "demo-002",
            "original_file_name": "clinic-family-ad.jpg",
            "stored_file_name": "",
            "file_type": "JPG",
            "file_size_mb": 6.1,
            "width": 1200,
            "height": 800,
            "campaign_name": "Family Care Awareness",
            "department": "Healthcare",
            "asset_type": "Paid Ad",
            "usage_rights": "Unknown",
            "publish_channel": "Paid Ads",
            "owner": "Growth Team",
            "urgency": "Critical",
            "description": "Healthcare campaign visual awaiting rights verification.",
            "review_status": "Compliance Review",
            "review_notes": "Cannot publish until usage rights and patient-safe review are complete.",
            "created_at": utc_now(),
            "updated_at": utc_now(),
        },
        {
            "asset_id": "demo-003",
            "original_file_name": "product-card-lifestyle.png",
            "stored_file_name": "",
            "file_type": "PNG",
            "file_size_mb": 1.8,
            "width": 900,
            "height": 700,
            "campaign_name": "Q4 Product Refresh",
            "department": "E-commerce",
            "asset_type": "Product Image",
            "usage_rights": "Confirmed",
            "publish_channel": "Product Page",
            "owner": "E-commerce Content",
            "urgency": "Normal",
            "description": "Lifestyle product card image for catalog refresh.",
            "review_status": "Pending Review",
            "review_notes": "Waiting for product content review.",
            "created_at": utc_now(),
            "updated_at": utc_now(),
        },
    ]

    demo_assets = [enrich_asset(asset) for asset in demo_assets]
    save_assets(demo_assets)

    save_audit_log(
        [
            {
                "event_id": str(uuid.uuid4()),
                "asset_id": "demo-001",
                "action": "Decision: Approved",
                "details": "Approved for website and social launch usage.",
                "actor": "Brand Reviewer",
                "timestamp": utc_now(),
            },
            {
                "event_id": str(uuid.uuid4()),
                "asset_id": "demo-002",
                "action": "Decision: Compliance Review",
                "details": "Usage rights unknown for healthcare paid ad campaign.",
                "actor": "Compliance Reviewer",
                "timestamp": utc_now(),
            },
            {
                "event_id": str(uuid.uuid4()),
                "asset_id": "demo-003",
                "action": "Asset Uploaded",
                "details": "Product image routed to Product Content Review.",
                "actor": "System",
                "timestamp": utc_now(),
            },
        ]
    )

    flash("Demo AssetLens data loaded.", "success")
    return redirect(url_for("index"))


if __name__ == "__main__":
    app.run(debug=True)
