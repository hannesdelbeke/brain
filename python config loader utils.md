I often find myself writing the same helper functions

```python    
from pathlib import Path

def load_json(p):  
    import json  
    with open(p , "r") as f:  
        return json.load(f)  
  
def load_yaml(p):  
    import yaml
    with open(p , "r") as f:  
        return yaml.safe_load(f)  
  
def load_config(p:str) -> dict  
    p = Path(p)  
    if p.suffix == ".json":  
        return load_json(p)  
    elif p.suffix == ".yaml":  
        return load_yaml(p)  
    else:  
        return {}
```

[[Python]] #config [[json]] [[YAML]]

Almost identical with this Python module [config-manager](https://github.com/afxentios/config-manager/blob/master/config_manager/config_manager.py)