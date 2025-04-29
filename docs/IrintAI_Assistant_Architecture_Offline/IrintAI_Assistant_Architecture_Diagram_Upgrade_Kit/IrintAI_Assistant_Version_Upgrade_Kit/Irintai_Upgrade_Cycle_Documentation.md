
# IrintAI Assistant Upgrade Cycle Documentation

## When to Update Each File
| File | When to Update | How to Update |
|:-----|:---------------|:--------------|
| `VERSION.txt` | Every time you create a new version (v2.0, v3.0, etc.) | - Copy from `VERSION_TEMPLATE.txt`<br>- Update version number and date<br>- List key changes<br>- Add any migration notes |
| `CHANGELOG.md` | Every time you make **meaningful changes** | - Add a new section at the top:<br>  `## [vX.X] - YYYY-MM-DD`<br>- Use **Added**, **Changed**, **Fixed**, **Removed** sections |
| `irintai_architecture_diagram_full_offline.html` | When the diagram itself changes | - Edit or replace the diagram content<br>- Retain HTML structure |
| `launch_irintai_viewer.bat` | Only if file names change | - Update the `.html` filename inside if needed |
| `launch_irintai_viewer_smart.bat` | Only if error handling or filenames change | - Ensure it points to correct `.html` file |
| `README.txt` | When major features or instructions change | - Add updated setup steps if needed |
| `README_UPGRADE.txt` | Only if the upgrade process itself changes | - Update if you modify the upgrade batch script logic |
| `upgrade_irintai.bat` | Only if new upgrade needs emerge | - Update deletion targets or copy behavior if structure changes |

## Practical Upgrade Workflow (Step-by-Step)
**Whenever you plan a new release:**

1. Edit your new diagram or features.
2. Copy `VERSION_TEMPLATE.txt` → Create a fresh `VERSION.txt`.
3. Open `CHANGELOG_TEMPLATE.md` → Add a new version block at the top.
4. Update `README.txt` if there are major user-facing changes.
5. Test your `launch` batch files (especially if file names change).
6. Zip everything cleanly for deployment:
    - New HTML
    - Updated BATs
    - Updated README / VERSION
    - New `update_files/` for Upgrade Kit
7. (Optional) Update `README_UPGRADE.txt` if major upgrade methods change.
8. Distribute the **Upgrade Kit ZIP** to your team.
9. Instruct teammates: “Double-click `upgrade_irintai.bat` — Done.”

## Example Versioning Pattern
| Version | Changes | Notes |
|:--------|:--------|:------|
| v1.0 | Initial release | Manual offline viewing, basic batch launcher |
| v2.0 | New diagram nodes added, smart launcher improved | Upgrade kit provided |
| v3.0 | Major semantic layer overhaul | Requires minor README updates |

## BONUS: Pro Tips for Long-Term Success
- Always **increment** version numbers logically:
  - Major (v1 → v2) = Big diagram or system changes.
  - Minor (v2.1 → v2.2) = Small fixes or instructions.
- Always **timestamp** your `VERSION.txt` clearly.
- Keep your **CHANGELOG.md** public if you ever open the project up (e.g., GitHub, team drive).

## Summary of Deliverables Completed
| Task | Status |
|:-----|:-------|
| Offline deployment kit | Done |
| Upgrade automation kit | Done |
| README and Upgrade documentation | Done |
| VERSION.txt template | Done |
| CHANGELOG.md template | Done |
| Full Upgrade Cycle Documentation | Done |
