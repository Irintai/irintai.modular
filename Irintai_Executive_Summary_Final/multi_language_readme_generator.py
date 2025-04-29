
import os

translations = {
    'Spanish': 'Este proyecto proporciona un visor sin conexión para la arquitectura Irintai.',
    'French': "Ce projet fournit un visualiseur hors ligne pour l'architecture Irintai.",
    'German': 'Dieses Projekt bietet einen Offline-Viewer für die Irintai-Architektur.',
    'Portuguese': 'Este projeto fornece um visualizador offline para a arquitetura Irintai.',
    'Italian': "Questo progetto fornisce un visualizzatore offline per l'architettura Irintai.",
}

base_readme = """
# IrintAI Assistant Offline Viewer

This project provides an offline viewer for the IrintAI Assistant architecture.

## Usage
- Double-click the batch file to launch the viewer.

## Requirements
- A modern web browser.
"""

output_dir = "generated_readmes"
os.makedirs(output_dir, exist_ok=True)

# Save English README
with open(os.path.join(output_dir, "README_EN.txt"), "w", encoding="utf-8") as f:
    f.write(base_readme.strip())

# Generate translated versions
for language, translation in translations.items():
    translated_readme = base_readme.replace(
        "This project provides an offline viewer for the IrintAI Assistant architecture.", translation
    )
    filename = f"README_{language.upper()[:2]}.txt"
    with open(os.path.join(output_dir, filename), "w", encoding="utf-8") as f:
        f.write(translated_readme.strip())

print(f"Generated {len(translations) + 1} README files in '{output_dir}' folder.")
