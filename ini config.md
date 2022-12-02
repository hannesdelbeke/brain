in Python you can make an ini config with [configparser](https://docs.python.org/3/library/configparser.html)

```python
import configparser
from pathlib import Path

def read_config():
    config = configparser.ConfigParser()
    if config_path.exists():
        config.read(config_path)
    return config

def write_config(config: Path):
    config_path.parent.mkdir(parents=True, exist_ok=True)
    with open(config_path, "w") as f:
        config.write(f)
```

unlike `json`, `ini` can have comments.
the python package `toml` file uses the same structure. TODO link build note

found it bit of a pain to use. `json` is easier to use in Python

good [discussion](https://www.reddit.com/r/Python/comments/89c9b5/what_config_file_format_do_you_prefer/) on formats