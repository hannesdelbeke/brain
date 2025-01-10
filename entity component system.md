---
aliases:
  - ECS
  - Entity-Component-System
  - Entity-Component System
---

[[OOP vs ECS]]

For implementing ECS, in Python ChatGPT recommends 
### dictionaries for entities
Using a dict allows you to dynamically add, remove, or query components for each entity during runtime

example: make a enemy immortal by removing their health
```python
entity = {}
entity[Position] = Position(10, 20)  # Add a Position component
del entity[Health]  # Remove the Health component
```

- dataclasses for components.



> [!warning] 
> Don't confuse entity component system {ECS} with [[Amazon Elastic Container Service]] (Amazon ECS)


- [ECS FAQ](https://github.com/SanderMertens/ecs-faq)

see unity DOTS
## WIP notes
ecs is used for simulation
not for gfx

complex to implement
mostly gains if you use same stuff

