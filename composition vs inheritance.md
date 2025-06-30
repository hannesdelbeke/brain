## inheritance
[[inheritance]]

```python
class Image():
	def __init__(file_path):
		self.file_path = file_path
		self.pixels = []
		self.height = 0
		self.width = 0
		self.load()  # loads the image from the path on instance creation
	def load()
		raise NotImplemented
	def save()
		raise NotImplemented
```

```python
class JPGImage(Image):
	def load()
		self.pixels, self.height, self.width = jpg.load(self.file_path)
	def save()
		jpg.save(self.pixels, self.file_path)
```

```python
class BMPImage(Image):
	def load()
		self.pixels, self.height, self.width = bmp.load(self.file_path)
	def save()
		bmp.save(self.pixels, self.file_path)
```

if we [[refactor]] this we run into issues.
e.g. we want to add support for a dynamically generated image, not made from a file. 
it would not make sense to have a `load` and `save` method, so instead we either 
- make the `load` & `save` methods throw an error. we now have 2 methods that you shouldn't use. Confusing!
- Or we refactor the `Image` class with a in-between `FileImage` class
```python
class Image():
	def __init__():
		self.pixels = []
		self.height = 0
		self.width = 0
		
class FileImage(Image):
	def __init__():
		self.file_path = "C:/path/to/file"
	def load()
		raise NotImplemented
	def save()
		raise NotImplemented

```python
class DrawImage(Image):
	def flip():
		self.pixels = self.pixels.reverse()
	def draw_line():
		# edit self.pixels to draw a line
		...
```
but then we also need to modify our other image classes that inherit currently from `Image`

```python
class JPGImage(FileImage):
	...
class BMPImage(FileImage):
	...
```
this is a lot of refactoring, showing that inheritance can make it hard to change code.

## composition
instead of inheriting, and accessing through `self`, we store a `Image` variable.
more like [[functional programming]]
```python
class JPGImage():
	def __init__(file_path):
		self.file_path = file_path
	def load(img: Image)
		img.pixels, img.height, img.width = jpg.load(self.file_path)
	def save(img: Image)
		jpg.save(img.pixels, img.file_path)
```
This contains all file related stuff to `JPGImage`, and keeps all image related logic in `Image` without tightly coupling it to each other.
So instead of having to choose a class to inherit `Image` or `JPGImage`, we can choose classes to use `Image` + `JPGImage` + `DrawImage`
mix n match example:

```python
class DrawImage():
	def __init__(image: Image):
		self.image = image
	def flip():
		self.image.pixels = self.image.pixels.reverse()
	def draw_line():
		# edit self.image.pixels to draw a line
		...
```
## Example

```python
# composition example
img = Image()  # create new img
jpg = JPGImage(file_path="C:/file.jpg")  # load jpg
draw = DrawImage(image=img)
draw.flip()  # this edits the img we passed on creation (mutation)
bmp = BMPImage(file_path="C:/file.bmp")
bmp.save(img=img)
```
with inheritance it looks cleaner at first, but harder to modify your code.
and we now need to create a new method to convert jpg to bmp!
```python
# inheritance example
jpg = JPGImage(file_path="C:/file.jpg")  # load jpg
jpg.flip()
# TODO create method to convert jpg to bmp
bmp.save()
```

inheritance looks cleaner because it comes with [[abstraction]], hiding some things. It creates a [[contract (software)|contract]] telling the user what to expect. E.g. every `image` child class has `save` & `load`.
and the user doesn't has to care about what type of image we have, they can just load & save the image.
An [[interface|interface]] allows us to do this while using [[composition]].

```python
class ImageFile()
	def load()
		raise NotImplemented
	def save()
		raise NotImplemented
# you can also use ABC, abstractmethod
```

> [!warning] 
> (unsure if this makes sense in Python), in Java they use `structure` instead of `class`

Instead of tightly coupling to the class, we only define the shared methods. this results in a much more lightweight reuse of code.
This can then be inherited by our classes again, to show we have shared functionality.
```python
class JPGImage(ImageFile):
	...
class BMPImage(ImageFile):
	...
```

interfaces only define the important parts of the contract, and are easily added on top of existing classes. e.g. i can inherit multiple interfaces.

now instead of asking to pass a whole thing, we can pass the interface for what we want to use it for. This is [[dependency injection]]

based on [video](https://www.youtube.com/watch?v=hxGOiiR9ZKg)
