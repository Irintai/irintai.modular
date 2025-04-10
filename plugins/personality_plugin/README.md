# Personality Plugin: Installation and Usage Guide

This guide provides complete instructions for installing, configuring, and using the Irintai Personality Plugin.

## Installation

### Method 1: Manual Installation

1. Create the plugin directory structure:
   ```
   plugins/
   └── personality/
   ```

2. Copy the following files to the plugin directory:
   - `__init__.py` - Main plugin file
   - `bridge.py` - Compatibility layer
   - `README.md` - Documentation

3. Create the resources directory:
   ```
   plugins/personality/resources/
   ```

4. Copy the `default_profiles.json` file to the resources directory

5. Restart Irintai or use the plugin manager to load the plugin

### Method 2: Using the Plugin Manager

1. Package the plugin files into a ZIP archive:
   ```
   personality.zip
   ├── __init__.py
   ├── bridge.py
   ├── README.md
   └── resources/
       └── default_profiles.json
   ```

2. Open Irintai and navigate to the Plugin Manager

3. Click "Install Plugin" and select the ZIP file

4. The plugin will be automatically installed and loaded

## Configuration

The plugin stores its configuration in:
```
data/plugins/personality/config.json
```

This file is created automatically when the plugin is first loaded. You typically won't need to edit this file directly, as all configuration can be done through the UI.

## Usage Guide

### Accessing the Plugin

1. Open Irintai
2. Navigate to the Plugins tab
3. Select "Personality Plugin" from the list of installed plugins

### Using Personality Profiles

#### Viewing Available Profiles

The left panel of the plugin interface shows all available personality profiles. The currently active profile is marked with an asterisk (*).

#### Activating a Profile

1. Select a profile from the list
2. Click the "Activate" button
3. All assistant responses will now use this personality

#### Creating a New Profile

1. Click the "New" button
2. Enter the required information:
   - **Name**: A unique name for the profile
   - **Description**: A brief description of the personality
   - **Tags**: Comma-separated list of keywords (optional)
   - **Author**: Your name or alias (optional)
3. Click "Create"
4. The new profile will appear in the list with default style settings

#### Editing a Profile

1. Select a profile from the list
2. Click the "Edit" button
3. A dialog will open with three tabs:
   - **Basic Info**: Name, description, tags, etc.
   - **Style Modifiers**: Sliders for adjusting personality traits
   - **Special Rules**: Checkbox options for specific behaviors
4. Make your changes
5. Click "Save"

#### Style Modifiers

Style modifiers control the personality's communication style:

| Modifier | Low (0.0) | High (1.0) |
|----------|-----------|------------|
| Formality | Casual | Formal |
| Creativity | Precise | Creative |
| Complexity | Simple | Complex |
| Empathy | Analytical | Empathetic |
| Directness | Indirect | Direct |

Adjust these sliders to fine-tune the personality's communication style.

#### Special Rules

Special rules enable specific behaviors:

- **Honor Trauma**: Acknowledges emotional intensity and treats it as valid data
- **Recursive Framing**: Uses cyclical, reflective language patterns
- **Use Symbolic Language**: Incorporates symbolic references and metaphors

These are particularly relevant for the Altruxan personality style.

#### Duplicating a Profile

1. Select a profile from the list
2. Click the "Duplicate" button
3. Enter a name for the new profile
4. A copy of the selected profile will be created with the new name

#### Deleting a Profile

1. Select a profile from the list
2. Click the "Delete" button
3. Confirm the deletion
4. The profile will be removed

Note: You cannot delete the currently active profile.

### Importing and Exporting

#### Exporting a Profile

1. Select a profile from the list
2. Click the "Export Profile" button
3. A dialog will open showing the profile in JSON format
4. Click "Copy to Clipboard" to copy the JSON data

#### Importing a Profile

1. Click the "Import Profile" button
2. Paste the JSON data into the text area
3. Click "Import"
4. The profile will be added to your list of available profiles

## Advanced Usage

### Using with Memory System

The plugin automatically stores personality changes in the memory system (if available). This allows the assistant to be aware of its own personality shifts and maintain consistency.

### Creating Custom Personalities

You can create completely custom personalities by:

1. Creating a new profile
2. Editing it to set basic parameters
3. Fine-tuning the style modifiers
4. Enabling special rules as needed
5. Testing it with various prompts to refine the settings

### Altruxan Philosophy Integration

The Altruxan profile is designed to align with the Altruxan philosophy described in the theoretical framework. It incorporates:

- Recursive framing and cyclical language patterns
- Acknowledgment of emotional intensity
- Symbolic language and metaphor
- A balance of directness and empathy

## Troubleshooting

### Plugin Not Loading

1. Check that all files are in the correct locations
2. Verify that the plugin directory is named exactly "personality"
3. Restart Irintai completely

### Changes Not Applied

1. Make sure the profile is properly activated
2. Check that the chat engine is properly integrated with the plugin
3. Try deactivating and reactivating the plugin

### Profile Import Fails

1. Ensure the JSON data is properly formatted
2. Check that the profile name is unique
3. Verify that all required fields are present in the JSON data

## Philosophy and Design

The Personality Plugin embodies the Irintai ethos:

- **Intention Over Novelty**: Every feature serves a clear purpose for enhancing dialogue
- **Partnership With AI**: Personality is a key aspect of true partnership, not just tooling
- **Democratization of Power**: Users can shape the AI's voice and style
- **Transparency and Modularity**: All components are transparent and modifiable
- **Failure as Refinement**: The plugin learns from interaction patterns

It transforms Irintai from a mere interface into a relational presence that adapts to the user's needs and preferences.

## License

MIT License