chat GPT
```python
import sys
from PySide2.QtWidgets import QApplication, QMainWindow, QLabel, QLineEdit, QVBoxLayout, QWidget


class Person:
    def __init__(self, name='', age=0):
        self._name = name
        self._age = age

    def get_name(self):
        return self._name

    def set_name(self, name):
        self._name = name

    def get_age(self):
        return self._age

    def set_age(self, age):
        self._age = age


class PersonPresenter:
    def __init__(self, model, view):
        self.model = model
        self.view = view

        self.view.name_input.textChanged.connect(self.update_name)
        self.view.age_input.textChanged.connect(self.update_age)

    def update_name(self, name):
        self.model.set_name(name)

    def update_age(self, age):
        self.model.set_age(age)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.name_label = QLabel("Name:")
        self.name_input = QLineEdit()

        self.age_label = QLabel("Age:")
        self.age_input = QLineEdit()

        layout = QVBoxLayout()
        layout.addWidget(self.name_label)
        layout.addWidget(self.name_input)
        layout.addWidget(self.age_label)
        layout.addWidget(self.age_input)

        widget = QWidget()
        widget.setLayout(layout)
        self.setCentralWidget(widget)


if __name__ == '__main__':
    app = QApplication(sys.argv)

    person_model = Person()
    main_window = MainWindow()
    person_presenter = PersonPresenter(person_model, main_window)

    main_window.show()

    sys.exit(app.exec_())

```

In this example, we have a `Person` class that represents the Model. It encapsulates the data and provides getter and setter methods for accessing and modifying the properties.

The `MainWindow` class represents the View. It creates the UI elements and sets up the layout.

The `PersonPresenter` class acts as the Presenter, which acts as a mediator between the Model and the View. It handles the user interactions from the View and updates the Model accordingly.

The Presenter listens to the `textChanged` signals from the name and age input fields and updates the Model using the corresponding setter methods.

This example follows the MVP pattern by separating the concerns into distinct components. The Presenter facilitates the communication between the Model and the View, allowing for separation of logic and making the code more modular and testable.

Note that in this example, we have not included any additional logic for displaying or utilizing the data from the Model. The focus is on the separation of responsibilities according to the MVP pattern.

[[programming patterns]]