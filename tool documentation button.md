# Tool UX: User
A great UX improvement, is to have a link to the docs from your tools.
This way users always know where the docs live.

> [!NOTE]- Sample tool without clear docs
> Have a look at this image.
> ![[documentation button-1676646116906.jpeg|200]]
> How does this tool work? What does it Do? Where to find the docs?

# Tool UX: Dev
As a dev, I want to easily add a documentation button or menu to my tool.

### Hardcode approach
The easiest method would be, just add a qt button to the top.

PRO
- no dependencies
CONs
- less consistent, harder to update tools in bulk

> [!NOTE]- sample hardcoded docs button
> At Mediatonic we had a docs button always in the same place
> ![[documentation button-1676646504645.jpeg|300]]

### Dependency approach
a [[qt_custom_window]] could do this.

> [!NOTE]- sample of a custom qt window
> ![[2022-12-31-1672479992574.jpeg]]

the dev who writes this tool can do
```python
import docsbar
wrapped_widget = docsbar.wrap(mywidget)
wrapped_widget.url = "www.docs.com"
```

add `docsbar` to the dependencies / requirements file
the `docsbar` dependency auto installs through pip on install.

[[tooldev]]