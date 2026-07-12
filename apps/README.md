# Mobile App Fixtures

Put local mobile app builds here when you want native examples to run.

The bundled native examples auto-download their TheApp sample build when it is missing.
You can also download both fixtures manually:

```bash
python scripts/download_sample_apps.py --all
```

You can still add your own `.apk`, `.app`, `.app.zip`, or `.ipa` here and run with:

```bash
python framework.py run --profile android_the_app --app apps/YourAndroidApp.apk -m android
python framework.py run --profile ios_the_app --app apps/YourIosApp.app.zip -m ios
```
