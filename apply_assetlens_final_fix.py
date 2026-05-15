from pathlib import Path

app_path = Path("app.py")
template_path = Path("templates/asset_detail.html")
css_path = Path("static/styles.css")
readme_path = Path("README.md")

app_text = app_path.read_text(encoding="utf-8")
template_text = template_path.read_text(encoding="utf-8")
css_text = css_path.read_text(encoding="utf-8")
readme_text = readme_path.read_text(encoding="utf-8")

old_decisions = 'allowed_decisions = {"Approved", "Rejected", "Needs Metadata", "Compliance Review", "Client Approval"}'
new_decisions = 'allowed_decisions = {"Approved", "Approved With Exception", "Rejected", "Needs Metadata", "Compliance Review", "Client Approval"}'
app_text = app_text.replace(old_decisions, new_decisions)

old_block = '''    if decision_value not in allowed_decisions:
        flash("Invalid review decision.", "error")
        return redirect(url_for("asset_detail", asset_id=asset_id))

    asset["review_status"] = decision_value
    asset["review_notes"] = notes or f"Decision updated to {decision_value}."
    asset["updated_at"] = utc_now()
'''

new_block = '''    if decision_value not in allowed_decisions:
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
'''

app_text = app_text.replace(old_block, new_block)

old_option = '''                        <option>Approved</option>
                        <option>Needs Metadata</option>'''

new_option = '''                        <option>Approved</option>
                        <option>Approved With Exception</option>
                        <option>Needs Metadata</option>'''

template_text = template_text.replace(old_option, new_option)

old_verdict = '''            <div class="verdict-card">
                <span class="badge risk-{{ asset.risk_level|lower }}">{{ asset.risk_level }} Risk</span>
                <h3>{{ asset.recommended_action }}</h3>
                <p>Workflow Route: <strong>{{ asset.workflow_route }}</strong></p>
            </div>'''

new_verdict = '''            <div class="verdict-card">
                <span class="badge risk-{{ asset.risk_level|lower }}">{{ asset.risk_level }} Risk</span>
                <h3>{{ asset.recommended_action }}</h3>
                <p>Workflow Route: <strong>{{ asset.workflow_route }}</strong></p>
            </div>

            {% if asset.risk_level == "High" or asset.usage_rights in ["Unknown", "Not Provided", "Expires Soon", ""] %}
                <div class="governance-alert">
                    <strong>Approval Control Active</strong>
                    <p>Normal approval is blocked until usage rights are confirmed or an executive-approved exception is documented.</p>
                </div>
            {% endif %}'''

template_text = template_text.replace(old_verdict, new_verdict)

if ".governance-alert" not in css_text:
    css_text += '''

.governance-alert {
    margin-top: 16px;
    padding: 16px;
    border-radius: 18px;
    color: var(--red);
    background: var(--red-soft);
    border: 1px solid rgba(184, 71, 71, 0.18);
}

.governance-alert strong {
    display: block;
    margin-bottom: 6px;
}

.governance-alert p {
    margin: 0;
    color: var(--red);
    line-height: 1.55;
}
'''

if "Approved With Exception" not in readme_text:
    readme_text = readme_text.replace(
        "- Approval, rejection, metadata request, compliance review, and client approval statuses",
        "- Approval, Approved With Exception, rejection, metadata request, compliance review, and client approval statuses"
    )

    readme_text = readme_text.replace(
        "- Review statuses to prevent unapproved release",
        "- Review statuses to prevent unapproved release\n- Approval blocking for high-risk assets or assets with unknown usage rights\n- Approved With Exception workflow requiring reviewer notes"
    )

app_path.write_text(app_text, encoding="utf-8")
template_path.write_text(template_text, encoding="utf-8")
css_path.write_text(css_text, encoding="utf-8")
readme_path.write_text(readme_text, encoding="utf-8")

print("AssetLens final governance fix applied.")
