Vendoring means copying the source code of another project into your project
It's in contrast to using dependencies, adding another project's name to your package.

Pro
- all dependencies are contained within 1 project, you can easily give the project to someone and it will work as expected

Con
- Maintaining vendored code can be time consuming. if someone fixes a bug in a dependency, you have to naually update this now. And everyone who is using your code must also manually update.