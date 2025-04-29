
# IrintAI Assistant Offline Viewer - Master Documentation

Welcome to the IrintAI Assistant Offline Viewer Project.  
This documentation outlines all available tools, scripts, and workflows for managing, upgrading, backing up, and deploying the IrintAI Assistant project.

---

## Core Components

| Component | Purpose |
|:----------|:--------|
| `irintai_architecture_diagram_full_offline.html` | Main offline viewer for the IrintAI Assistant Architecture |
| `launch_irintai_viewer.bat` | Basic one-click launcher |
| `launch_irintai_viewer_smart.bat` | Smart launcher with mermaid.js check |
| `README.txt` | User instructions for offline viewer |
| `VERSION.txt` | Version information for each release |
| `CHANGELOG.md` | Full historical record of changes |

---

## Automation Scripts

| Script | Purpose |
|:-------|:--------|
| `auto_packager_irintai.bat` | 🔧 Packages the latest files into a clean versioned ZIP for distribution |
| `auto_deploy_irintai_docs.bat` | 🚀 Automates GitHub Pages deployment (one-click upload of documentation website) |
| `backup_irintai_docs.bat` | 🛡️ Creates a timestamped backup ZIP of all current files |
| `multi_language_readme_generator.py` | 🌎 Generates README files in multiple languages for internationalization |

---

## Documentation Website

- `index.html` → Homepage linking all documentation
- `upgrade_cycle.html` → Step-by-step Upgrade Cycle Guide
- `version_log.html` → Version history and summaries
- `changelog.html` → Detailed changelog of all changes
- `about.html` → Project background and mission

These can be viewed locally or published online through GitHub Pages.

---

## GitHub Pages Deployment Guide

To publish your documentation:

1. Create a GitHub repository (e.g., `irintai-docs`).
2. Upload the documentation website files (`index.html`, `assets/`, etc.).
3. Use the `auto_deploy_irintai_docs.bat` script to push files automatically.
4. Go to your repository Settings > Pages > Enable GitHub Pages on the `main` branch.
5. Your documentation will be publicly available!

---

## Upgrade Workflow Overview

1. Update or improve your diagram and supporting files.
2. Create new `VERSION.txt` and update `CHANGELOG.md`.
3. Run `auto_packager_irintai.bat` to bundle a new ZIP release.
4. (Optional) Backup current files using `backup_irintai_docs.bat`.
5. (Optional) Update multi-language READMEs using `multi_language_readme_generator.py`.
6. Deploy documentation updates online using `auto_deploy_irintai_docs.bat`.

---

## Best Practices

- Always create a **backup** before making significant changes.
- Always increment version numbers logically.
- Maintain clear **VERSION.txt** and **CHANGELOG.md** records.
- Test locally before publishing online.

---

## Special Thanks

This entire infrastructure was constructed to support resilience, clarity, and growth of the Irintai vision.

-- The IrintAI Assistant Project Team
