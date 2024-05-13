## question

how does used by work in [[GitHub]] for Python packages?
e.g. https://github.com/yjg30737/pyqt-frameless-window
I understand it reads from requirements.txt
```
pyqt-frameless-window==0.0.61
```
but how does it know where the repo lives? 
anyone could make a repo with the same name after all.

## answer

the [GitHub docs](https://docs.github.com/en/code-security/supply-chain-security/understanding-your-software-supply-chain/exploring-the-dependencies-of-a-repository#changing-the-used-by-package)  explain how:
-   The dependency graph is enabled for the repository
-   Your repository contains a package that is published on a [supported package ecosystem](https://docs.github.com/en/github/visualizing-repository-data-with-graphs/about-the-dependency-graph#supported-package-ecosystems).
-   **Within the ecosystem, your package has a link to a _public_ repository where the source is stored.**