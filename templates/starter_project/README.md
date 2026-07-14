# Starter Project Template

Copy this folder when starting a product-specific mobile automation suite from the framework.

Recommended first steps:

1. Replace the example package names and app paths in `config/capabilities.yaml`.
2. Move product locators into `screens/`.
3. Keep business journeys in `flows/`.
4. Keep tests readable and marker-driven.
5. Run helper tests and at least one device smoke test before opening a PR.

This folder is intentionally small. It shows the shape of a project without copying the framework
internals. Keep only product-specific capabilities, screens, flows, and tests here; shared mobile
helpers should stay in the framework.
