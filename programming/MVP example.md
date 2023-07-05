# MVP example

written by me, another example by chatGPT [[MVP python example]]

## model
Pure functionality. A function you can run through console. No UI dependencies.
```python
# model.py
def do_math(a, b):
	return a + b
```

## view
the view doesn't do anything, it only shows the UI.
It's hooked up to a placeholder function that does nothing.
```python
# view.py
import sys
from PySide2.QtWidgets import QApplication, QMainWindow, QLabel, QWidget, QVBoxLayout, QLineEdit, QPushButton


class View(QMainWindow): 
	def __init__(self): 
		super(MainWindow, self).__init__()

        # Create the main widget and layout
        self.widget = QWidget()
        self.layout = QVBoxLayout(self.widget)

        # Create the input text cells
        self.input1 = QLineEdit()
        self.input2 = QLineEdit()

        # Create the button
        self.button = QPushButton("+")

        # Create the label to display the result
        self.result_label = QLabel()
        
        # Connect the button's clicked signal to the addition function
        self.button.clicked.connect(self.callback_button_clicked)


        # Add the input cells, button, and result label to the layout
        self.layout.addWidget(self.input1)
        self.layout.addWidget(self.input2)
        self.layout.addWidget(self.button)
        self.layout.addWidget(self.result_label)

        # Set the main widget and window properties
        self.setCentralWidget(self.widget)
        self.setWindowTitle("Addition Window")
        
	def callback_button_clicked():
		pass


def show():
	# Create the application and window
	app = QApplication(sys.argv)
	window = MainWindow()
	window.show()
	# Start the event loop
	sys.exit(app.exec_())
```

## presenter

You can inherit to create a presenter, however then the presenter has to know how the view works. If the variable `self.input1` is renamed to `self.input_a`, the presenter needs updating or will break.
However it's pretty straightforward otherwise.
```python
# presenter.py
from view import View
from model import do_math

class Presenter(View):
	def callback_button_clicked():
		a = self.input1.getText()
		b = self.input2.getText()
		result = do_math(a, b)
		self.result_label.setText(result)
```

## More separation
Another approach is to hookup predefined methods in the view.
Let's extend the view with
```python
def get_input_a():
	return self.input1
	
def get_input_b():
	return self.input2
```
Now we can rename the attrs without breaking the presenter. And agree on an interface that's exposed to the presenter.
TBH, if you rename `def get_input_a` it will also break, so IMO not much advantage is gained.
From personal experience, I've not noticed much advantage either.

The main advantage is that if you work with a `.ui` file, you can rename stuff in there without affecting the presenter, but still have to update the view.
Otherwise you have to update the presenter instead of the view, or possibly both.
So it's more changing the responsibility instead of avoiding the issue.

## hookup with functions
Another way is to instead of inheritance, use a function to hookup.
The callback should take no arguments, and return nothing. So it can simply be called by the view without worrying about input.
```python
# presenter.py
from view import View
from model import do_math

def do_math_hookup(view):
	a = self.input1.getText()
	b = self.input2.getText()
	result = do_math(a, b)
	self.result_label.setText(result)
	
def hookup_view():
	"""returns a presenter"""
	view = View()
	view.callback_button_clicked = lambda a=view : do_math_hookup(a)
	return view
```
> It might be worth to add `*args` to your callback method to avoid crashing with qt passing extra arguments like a `is_checked` bool for checkboxes.

[[programming patterns]]