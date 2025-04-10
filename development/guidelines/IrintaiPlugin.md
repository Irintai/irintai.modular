# IrintaiPlugin Specification (Optional Implementation)

## Purpose
This document outlines the future standardization of the `IrintaiPlugin` interface. It is **not currently required**, but is intended to serve as a future-proofing measure for the IrintAI Assistant plugin ecosystem.

The goal of introducing a shared `IrintaiPlugin` interface is to:
- Provide a universal standard for plugin lifecycle methods
- Simplify validation and interaction between plugins and the core system
- Support better developer tooling, reflection, and documentation
- Maintain decentralization by offering, not enforcing, the structure

This specification is written to ensure that **if the original developer is no longer able to lead development**, others can continue the work with clarity, care, and respect for the original vision.

---

## Philosophy
Irintai is built to empower the user.
The plugin system is designed to:
- Be readable and editable by anyone
- Require no hidden inheritance or central codebase modifications
- Offer full functionality within the plugin folder itself

The `IrintaiPlugin` interface will follow this ethos: it must never be required. It is a convenience, not a constraint.

---

## Proposed Interface: `IrintaiPlugin`

```python
class IrintaiPlugin:
    name: str = "UnnamedPlugin"
    friendly_name: str = "Unnamed Plugin"
    version: str = "0.1"
    description: str = "No description provided."
    tags: list[str] = []

    def __init__(self):
        self.log = print  # This may be overwritten by the plugin loader

    def activate(self):
        pass

    def deactivate(self):
        pass

    def get_interface(self) -> dict:
        return {}
```

### Optional Methods
```python
    def configure(self, config: dict):
        pass

    def export_state(self) -> dict:
        return {}

    def import_state(self, state: dict):
        pass
```

---

## Future Loader Logic (Optional Support)
The `plugin_manager.py` may be extended to:
- Detect if a plugin class inherits from `IrintaiPlugin`
- Use reflection to auto-document its metadata
- Provide default error handling and validation routines

However, any such logic **must fallback gracefully** to plugins that do not inherit the base class.

---

## Location
If implemented, the `IrintaiPlugin` base class will reside in:
```
utils/irintai_plugin.py
```

This file must:
- Be visible
- Be documented with examples
- Never contain side effects or hidden behavior

---

## Development Conditions
The introduction of this interface should only occur **after**:
- At least 5 plugins have been built using the existing architecture
- At least one external developer has successfully contributed a plugin
- The core system has stabilized and reached a public-facing stage

---

## Final Statement
This specification ensures that **if the original developer is unable to continue**, future contributors will have:
- A clear path forward
- A documented standard
- A preserved ethos of accessibility, self-containment, and transparency

The `IrintaiPlugin` is not here to control. It is here to assist.
Just like Irintai itself.

