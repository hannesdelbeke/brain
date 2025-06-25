If you package your [[Maya tool]] in a [[Maya module]] (e.g. using the [[Maya module template]]),
[[vendoring]] your dependencies in the scripts folder results in duplicated Python modules between your tools. And your dependencies will get outdated.

A cleaner solution is to package your tool in a [[Maya plugin]] using the [[Maya plugin template]]. It's more [[modular]], can be enabled/disabled per user in Maya unlike Maya modules. And dependencies can be pip installed, so you can keep them up to date, and avoid duplication.
There also are fewer files and folders usually compared to a Maya module setup.

- [x] easily install dependencies from requirements in the [[Maya plugin template]]
	- [x] [[plugget]] handles this
	- [x] the mel installer installs dependencies
