## How to deploy to a GitHub environment
Which adds a big green `environment` button on the front page of your [[GitHub]] repo. Example [repo](https://github.com/plugget/plugget-qt)

1. Configure an environment named PyPI
2. Add the `PYPI_API_TOKEN` secret to your environment 
3. Add this to your release workflow config: (e.g. see this [workflow](https://github.com/plugget/plugget-qt/blob/main/.github/workflows/PyPI-publish.yml))
```
    environment:
      name: PyPI
      url: https://pypi.org/p/plugget-qt
```
⚠️ Believe the environment name is capital sensitive.