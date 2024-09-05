[source](https://wiki.c2.com/?RegistryPattern)
A registry is a global association from keys to objects, allowing the objects to be reached from anywhere. It involves two methods: 
- one that takes a key and an object and add objects to the registry 
- and one that takes a key and returns the object for the key. 
It's similar to the [MultitonPattern](https://wiki.c2.com/?MultitonPattern), but doesn't restrict instances to only those in the registry.

note that e.g. in python you can register a class or class instance object directly. you don't need a string key, because under the hood there is a key (the pointer)
I see some implementations limit themself to string names, which won't work with duplicate key names.
