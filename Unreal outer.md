An object’s “Outer” is the object which “owns” it. For instance, a Component is owned by its Actor or parent component, and Actors are owned by their Levels. Whenever you construct an object of a class derived from `UObject`, you provide it with an Outer. 
(`CreateDefaultSubobject` implicitly provides the current object as the Outer.)
[source](https://forums.unrealengine.com/t/how-can-i-understand-the-data-member-outer-in-the-uobjectbase-class/330196)

AFAIK if you destroy an actor that's an outer of a component, the component will be garbage collected