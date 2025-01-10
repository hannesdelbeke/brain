# object oriented programming (OOP) Example
Imagine a game where you have a player and an enemy. 
Each has attributes like position and health, and they can move.

```python
# OOP Example
class Character:
    def __init__(self, name, x, y, health):
	    # in ECS this data is the "component"
        self.name = name
        self.x = x  # Position X
        self.y = y  # Position Y
        self.health = health

    def move(self, dx, dy):  # in ECS this method is the "system"
        self.x += dx
        self.y += dy

    def take_damage(self, damage):  # in ECS this method is the "system"
        self.health -= damage
        if self.health <= 0:
            print(f"{self.name} has been defeated!")

# Create objects for player and enemy
# in ECS these are the "entities"
player = Character("Player", 0, 0, 100)
enemy = Character("Enemy", 5, 5, 50)

# Move the player and apply damage
player.move(1, 1)
enemy.take_damage(20)

print(f"Player Position: ({player.x}, {player.y})")
print(f"Enemy Health: {enemy.health}")
```
# Entity-Component-System (ECS) Example
Now, let's represent the same game in ECS. 
We'll separate data (components) from behavior (systems).
``` python
# ECS Example

# Components: Data only
class Position:
    def __init__(self, x, y):
        self.x = x
        self.y = y

class Health:
    def __init__(self, current):
        self.current = current

# Systems: Logic that operates on components
def move_system(entity, dx, dy):
    if Position in entity:
        entity[Position].x += dx
        entity[Position].y += dy

def damage_system(entity, damage):
    if Health in entity:
        entity[Health].current -= damage
        if entity[Health].current <= 0:
            print(f"Entity has been defeated!")

# Create entities as dictionaries of components
player = {Position: Position(0, 0), Health: Health(100)}
enemy = {Position: Position(5, 5), Health: Health(50)}

# Apply systems
move_system(player, 1, 1)  # Move player
damage_system(enemy, 20)   # Damage enemy

# Output results
print(f"Player Position: ({player[Position].x}, {player[Position].y})")
print(f"Enemy Health: {enemy[Health].current}")
```

## Comparison
### OOP:
- Behavior is tied to objects (Character has methods like move and take_damage).
- Adding new behaviors might require modifying or subclassing the Character class.
### ECS:
- Behavior (systems) is decoupled from data (components).
- Adding new behaviors involves creating new systems rather than modifying existing entities or components.
- ECS can be more scalable, especially for games with many entities and shared behaviors.

[[object oriented programming]]
[[entity component system]]