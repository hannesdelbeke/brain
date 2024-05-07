---
source: https://around-the-corner.typepad.com/adn/2013/04/distributing-plug-insfiles-on-maya-and-3ds-max.html
---
# Distributing plug-ins/files on Maya
(and 3ds Max)

You probably remember this article where I described in details how to work with Maya Modules and integrate your files and plug-ins in Maya. This time, I am going to explain what changes were made in Maya to support the Autodesk Exchange Store.

To submit an application / content package on Autodesk Exchange Store, you need to follow few but important rules. The application should be self-contained and easy to install for example. Self-contained means that all files should go in one single directory structure and outside the host application directory structure. In the past, I know, many people were copying their files directly into '`c:\Program Files\Autodesk\MayaNNNN`' or '`/Applications/Autodesk/MayaNNNN`', but for Exchange this is not allowed and unacceptable.

The other thing with the legacy Maya Module approach was that you needed to have a text file posted under the user profile at a specific place, meaning the installer had to determine which Maya version you wanted to use in case you had many on your computer. Many people were instead having a readme to explain people to copy files here and here, to make changes in their Maya.env or userPrefs.mel file, etc... and that was true as well for the Maya Bonus Tools ;)

The last but not least limitation was about initializing the application in Maya. Like the Maya Bonus Tools, you could provide a userSetup.mel to initialize your menu, shelve, plug-ins, ... but in remember that Maya load one and only one userSetup.mel file (and only the first one found :(

The Exchange approach is that you now put your application in one common place, and describe your application. Any Autodesk software watch that folder and if the application says 'I am for Maya 2014', Maya 2014 will load the application. If it says 'I am for Maya 2014, AutoCAD 2014 and 3ds Max 2014 & 2015', these 4 app/version will load the application but not the others.

## Describe your application
Let's take a quick look to my favorite little Maya Math node sample in Python. The XML description file looks like this:
```xml
<?xml version="1.0" encoding="utf-8"?>
<ApplicationPackage SchemaVersion="1.0"
	ProductType="Application"
	AutodeskProduct="Maya"
	Name="MathNode"
	Description="Autodesk Maya MathNode"
	AppVersion="1.0.0"
	Author="Autodesk"
	AppNameSpace="com.autodesk.exchange.maya.mathnode"
	HelpFile="./Contents/docs/index.html"
	OnlineDocumentation="http://www.autodesk.com/maya"
	ProductCode="*"
	UpgradeCode="{52c87085-07d5-4cfa-b76e-e348553c30ac}" >
	
	<CompanyDetails Name="Autodesk"
		Phone=" "
		Url="http://www.autodesk.com"
		Email="labs.plugins@autodesk.com" />

	<!-- Prevent to load in older version than Maya 2008 -->
	<RuntimeRequirements SupportPath="./Contents/docs" OS="win64|macOS|linux" Platform="Maya" SeriesMin="2008"  />

	<Components>
		<RuntimeRequirements SupportPath="./Contents/docs" OS="win64|macOS|linux" Platform="Maya" SeriesMin="2008" />
		<MayaEnv expr="MAYA_SCRIPT_PATH+:=shelves" />
		<ComponentEntry ModuleName="./Contents/plug-ins/asdkMathNode.py" AutoLoad="True" />
		<ComponentEntry ModuleName="./Contents/scripts/AEasdkMathNodeTemplate.mel" />
		<ComponentEntry ModuleName="./Contents/scripts/MathNode_load.mel" />
		<ComponentEntry ModuleName="./Contents/icons/MathNode.png" />
		<ComponentEntry ModuleName="./Contents/shelves/MathNode_shelf.mel" />
	</Components>
	
</ApplicationPackage>
```

The `ApplicationPackage` and the first `RuntimeRequirements` tags are the ones all Autodesk Application are watching to determine if the package if something they should eventually consider loading. The OS, Platform, can contain multiple values.

Each following 'Components' tag will describe an entire application like here, or components. In short, I could have had something like:

```xml
	<Components>
		<RuntimeRequirements SupportPath="./Contents/docs" OS="win64" Platform="3dsMax" SeriesMin="2013" SeriesMax="2014" />
		<ComponentEntry ModuleName="./Contents/plug-ins/asdkMathNode-x64.dlu" AutoLoad="True" />
	</Components>
	<Components>
		<RuntimeRequirements SupportPath="./Contents/docs" OS="win32" Platform="3dsMax" SeriesMin="2013" SeriesMax="2013" />
		<ComponentEntry ModuleName="./Contents/plug-ins/asdkMathNode-x86.dlu" AutoLoad="True" />
	</Components>

	<Components>
		<RuntimeRequirements SupportPath="./Contents/docs" OS="win64|macOS|linux" Platform="Maya" SeriesMin="2008" />
		<ComponentEntry ModuleName="./Contents/plug-ins/asdkMathNode.py" AutoLoad="True" />
	</Components>

	<Components>
		<RuntimeRequirements SupportPath="./Contents/docs" OS="win64|macOS|linux" Platform="Maya|3dsMax" />
		<ComponentEntry ModuleName="./Contents/docs/ReadMeFirst.txt" />
	</Components>
```

Which tells there is an application for:

3ds Max 2013 - 32-bits
3ds Max 2013 & 2014 - x64
Maya 2008 and beyond on Windows x64 / Max OSX, Linux
and a readme for

all OS,
3ds Max and Maya (all releases)
Nothing really new for Maya, but no more user profile text file to tell where to find a module on disk. For 3ds Max this is a completely new way for plug-ins to work with 3ds Max and would recommend using that approach instead of copying into the 3ds Max directory structure.

Autoload
One new thing for Maya is that Maya will now call a `<moduleName>_load.mel/.py` file as soon as a module is detected. Is that _load script, it is your chance to initialize menus, shelves, or anything you want. Note this _load script is source'd right before the userSetup.mel script which gives you a chance to setup your application environment and let the user to change it if he needs to.

But, Maya will also load modules at runtime. That means you would not need to restart Maya if you decide to install an Exchange compliant application (this can be turned off if you unload the 'autoLoader' plug-in in the Plug-in Manager).

Installer
Because the files are self-contained, and we got an XML file which describe the application, it is very easy to create installers for the 3 platforms in few minutes. The MSI, PKG, and Shell script installers for Maya are entirely automated and takes only 5 minutes once you got your application working. There is no additional work to do - you give the path where to find the files, and the AppPacker tool reads the XML file and directory structure to produce all the installers. The ADN team will create these installers for you and will help you to make changes in your application for a better Exchange Store integration.

You are unsure where to start - go here and/or Autodesk Developer Center 

You got plug-ins for year without installer and interested to have one without knowing where to start? I got the scripts and tools on GitHub and willing to share them with individuals. If interested, drop me a line with your GitHub account name. In future, I'll make them in public repository, but at this time, I am still testing couple of more complex scenario.

[[maya plugin]]
