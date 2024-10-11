`__new__` runs before `__init__` and is responsible for returning a new instance of the class.

can be used to edit strings on init

**Problem**: 
Standard tuples in [[Python]] are [[immutable]] and written in C, making them faster than any custom Python code. Lowercasing elements in the __init__ method isn’t possible because the object is already created.

**Solution**: 
Use the __new__ method to intercept and modify the arguments before the tuple is created.

**Implementation**:
- Define a class `LowerCaseTuple` that inherits from tuple.
- Override the __new__ method to lowercase all elements of the input iterable.
- Create an instance of `LowerCaseTuple` with uppercase strings to see the result.

```Python
class LowerCaseTuple(tuple):
    def __new__(cls, iterable):
        lower_iterable = (l.lower() for l in iterable)
        return super().__new__(cls, lower_iterable)

def lower_case_example():
    print(LowerCaseTuple(['HELLO', 'MEDIUM']))

def main():
    lower_case_example()

if __name__ == '__main__':
    main()
```

Running this code will output a tuple with lowercase elements:` ('hello', 'medium')`

source https://medium.com/@zackbunch/when-to-use-new-in-python-58632249b9cc

