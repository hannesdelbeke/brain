
useful [[environment variable]]s for Windows

| Environment Variable  | Example Value                         |
| --------------------- | ------------------------------------- |
| `%ProgramFiles%`      | `C:\Program Files`                    |
| `%ProgramFiles(x86)%` | `C:\Program Files (x86)`              |
| `%AppData%`           | `C:\Users\<Username>\AppData\Roaming` |
| `%UserProfile%`       | `C:\Users\<Username>`                 |
| `%LocalAppData%`      | `C:\Users\<Username>\AppData\Local`   |
| `%SystemRoot%`        | `C:\Windows`                          |

```python
import os
program_files = os.environ['ProgramFiles']
```