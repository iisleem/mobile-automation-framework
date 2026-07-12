# Security

Do not commit credentials, device farm tokens, app signing secrets, or production app builds.

Use environment variables in `config/capabilities.yaml`:

```yaml
appium:app: "${IOS_APP:-apps/TestApp.app.zip}"
```

Mask sensitive values before attaching logs or capabilities to reports.

## Reporting Security Issues

Open a private advisory or contact the repository owner directly for sensitive issues. Do not create
public issues that include credentials, tokens, private app links, production data, device farm
secrets, or screenshots with personal information.
