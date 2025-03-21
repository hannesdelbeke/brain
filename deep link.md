similar to [[app URI]]

## Key Differences:

| Feature               | Deep Link (`myapp://`)          | App URI (`https://myapp.com/...`) |
|-----------------------|--------------------------------|----------------------------------|
| **Opens in App**      | ✅ Yes, if app supports it     | ✅ Yes, if app is installed     |
| **Fallback to Web**   | ❌ No (fails if app is missing) | ✅ Yes (opens in browser)      |
| **Works on Desktop?** | ✅ Yes (if app supports it)    | ✅ Yes (via browser)           |
| **Needs Server Setup?** | ❌ No                         | ✅ Yes                         |
| **iOS & Android Support** | ✅ Yes (if app handles it)  | ✅ Yes (Universal Links/App Links) |
