# Visual Asset Triage Portal

## Overview

Visual Asset Triage Portal is a Flask-based internal review tool for uploading images, assigning workflow context, and generating a lightweight categorization summary for business teams.

This project is positioned as a recruiter-ready Python web application and internal-tool prototype. It upgrades a rough image-classification concept into a more practical workflow for marketing, e-commerce, documentation, and internal content review.

## Real-World Business Use Case

This project maps to practical workflows used by:

- Marketing Operations Teams
- Ecommerce Content Teams
- Internal Documentation Review
- Brand Asset Review Workflows
- Small Internal Operations Tools

A team may need to answer questions such as:

- What workflow should this asset belong to?
- Is this image likely to be a marketing creative, product asset, document snapshot, or general visual asset?
- What file type and basic intake details should be reviewed before approval?
- How can lightweight image review be handled through a simple internal portal?

This portal is useful for intake review, lightweight asset triage, and prototype demonstration of a practical business-facing Flask app.

## Key Features

- Image Upload Workflow
- Workflow Context Selection
- Suggested Asset Categorization
- File Type And File Size Summary
- Preview Panel For Uploaded Assets
- Lightweight Review Notes
- Simple Internal Tool Positioning

## Tech Stack

- Python
- Flask
- HTML
- CSS

## Repository Contents

- `app.py`
- `templates/index.html`
- `static/styles.css`
- `requirements.txt`
- `README.md`

## How To Run

### 1. Create And Activate A Virtual Environment

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
