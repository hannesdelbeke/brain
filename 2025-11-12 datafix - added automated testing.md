Project: [[datafix dev]]

used [[Github Copilot|Copilot]] in [[visual studio code|vs code]] to add automated testing on [[pull request|PR]]
- [[Python - Black]]
- [[pytest]]

## Black
It's been a while since I used Black, but want to get back into the habit.
I used to use Black in commit hooks and with [[GitHub actions]] all the time, by copy-pasting the project files defining the workflow between projects.

When I hadn't setup Black for a while, I felt [[mental resistance]] to do it again, despite the setup being straightforward, and having experienced the benefits. [[AI improves accessibility|Copilot solves that]], making it [[intuitive]] and simple to set up. 

## Tests
I've always wanted to develop a more test driven approach, and with [[datafix]] it feels like I did a decent job. I abstracted the logic in its own repo. And since it's [[pure Python]] with no dependencies, it's easy to write tests for it, and quick to run. 

The aim is to protect the core logic, ensuring some funny Maya or Blender change won't unknowingly break the module. And separating each area of concern makes it easier to think about the [[software architecture|architecture]].

[[code review]]