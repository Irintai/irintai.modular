
@echo off
setlocal

if not exist "mermaid.min.js" (
    echo ------------------------------------------------------
    echo ERROR: Missing 'mermaid.min.js'!
    echo Please download it from:
    echo https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.min.js
    echo and place it in the same folder as this file.
    echo ------------------------------------------------------
    pause
    exit /b
)

start irintai_architecture_diagram_full_offline.html
exit
