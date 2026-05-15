# AssetLens Visual Governance And Workflow Triage Portal

AssetLens is a premium internal SaaS-style visual asset governance portal. It helps teams upload, inspect, risk-score, route, approve, and audit visual assets before they are used publicly.

This project upgrades the original Visual Asset Triage Portal into a stronger real-world business system for marketing operations, brand teams, e-commerce teams, compliance reviewers, agencies, and client approval workflows.

## Product Direction

AssetLens is designed as a lightweight visual governance platform, not a basic image upload tool.

It focuses on the operational problem companies face when visual assets move through messy folders, email threads, unclear permissions, and untracked approval decisions.

The system helps teams answer:

- Is this asset approved?
- Who owns it?
- Can we legally use it?
- Does it have enough metadata?
- Which workflow should review it?
- What risk does it carry before publication?
- Who approved or rejected it?

## Core Features

- Secure image upload intake for PNG, JPG, JPEG, and WEBP files
- File size protection through Flask upload limits
- Filename sanitization using Werkzeug secure filename handling
- Image validation using Pillow
- Metadata quality scoring
- Governance risk scoring
- Workflow routing recommendations
- Review queue with asset cards
- Approval, rejection, metadata request, compliance review, and client approval statuses
- Asset detail review page
- Audit trail for upload and decision history
- Demo data loader for quick portfolio walkthroughs
- Enterprise-style dashboard UI

## Business Use Case

AssetLens could be used by marketing teams, brand teams, creative operations teams, agencies, e-commerce teams, healthcare campaign teams, education marketing departments, franchise businesses, and client approval teams.

## Revenue Model Concept

| Plan | Monthly Price | Setup Fee |
|---|---:|---:|
| Starter | $299/month | $500 |
| Growth | $999/month | $2,500 |
| Business | $2,500/month | $7,500 |
| Enterprise | $7,500/month | $20,000 |

The strongest path to $100,000/month is a combination of Growth, Business, and Enterprise customers using AssetLens for controlled approval workflows, client portals, brand compliance, usage rights tracking, and operational reporting.

## Security Model

This portfolio version includes:

- Allowed image extensions only
- File size limit
- Safe stored filenames
- Server-generated file identifiers
- Image validation before asset registration
- Review statuses to prevent unapproved release
- Audit logging for governance decisions

Future production hardening should include user authentication, role-based access control, CSRF protection, private object storage, malware scanning, signed download URLs, SSO, tenant isolation, database-backed persistence, and full compliance reporting.

## Tech Stack

- Python
- Flask
- Pillow
- HTML
- CSS
- JSON-based local data storage for portfolio/demo use

## Run Locally

PowerShell commands:

    cd C:\github-audit\Visual-Asset-Triage-Portal
    python -m venv .venv
    .\.venv\Scripts\python.exe -m pip install --upgrade pip
    .\.venv\Scripts\python.exe -m pip install -r requirements.txt
    .\.venv\Scripts\python.exe app.py

Then open this in your browser:

    http://127.0.0.1:5000

To load demo records, click Load Demo Data or open:

    http://127.0.0.1:5000/seed

## Portfolio Value

This project demonstrates product thinking, B2B SaaS positioning, secure upload handling, workflow design, operational dashboards, governance logic, risk scoring, metadata validation, audit logging, UI/UX polish, and real-world business relevance.

## Planned Enhancements

- User accounts and team workspaces
- Role-based permissions
- Client approval portals
- Cloud object storage
- Database persistence
- AI-assisted image tagging
- Usage rights expiration tracking
- Brand rule templates
- Exportable audit reports
- Admin billing dashboard
- API integration layer
