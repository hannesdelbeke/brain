[site](https://www.digitalcitizen.life/where-find-most-windows-10s-native-icons/) listing various DLLs containing default icons. 

apps can't have a custom icon.
	("Apps" use the [Universal Windows Platform](https://en.wikipedia.org/wiki/Universal_Windows_Platform) (UWP)
but shortcuts to apps can.



## TODO grey notepad icon
## challenge - incomplete

install [resource hacker](http://www.angusj.com/resourcehacker/#download)
open `C:\Windows\notepad.exe`
select icon folder

![[notepad_blackwhite.ico]]

before we can save
- take ownership of the file.
	- R-Click on Program Files -> Properties -> Security Tab
	- Click Advanced -> Owner (change)
	- click `advanced` under field `enter the object name to select` 
	- click find now
	- select administrator
- close and re open properties
- now set permissions
great [source](https://answers.microsoft.com/en-us/windows/forum/all/give-permissions-to-files-and-folders-in-windows/78ee562c-a21f-4a32-8691-73aac1415373)

- now save notepad in resource hacker
it works when saving notepad exe to desktop but cant yet paste it back.

## issue 1
- need permissions. rather not mess with whole windows folder
## isue 2
we set icon when saved on desktop, but not thumbnail


---

#darkmode
however a shortcut to notepad results in 2 notepad icons once launched, since notepad is an app.


> Have you tried to bypass the shell32.dll and instead modify the **imageres.dll** file which ought to contain the various icons you are wanting?
> [source](https://www.windows10forums.com/threads/modifying-shell32-dll.20570/) 


> First you need "Resource Hacker" to edit you Shell32.dll file icons. In order to save the changes you need to save the file as the same name but in a different directory. Then you need to run "Se7en File replacer.exe" Get you edited file from the directory you saved it into and then select Windows\System32 and it will copy it into that directory.
> [source](https://superuser.com/questions/152816/how-to-edit-shell32-dll-how-to-add-custom-pictures-icons-into-shell32-dll)

- is this true?don't edit default windows dll's, windows will revert and could break OS? 


- can we edit registry instead?
  look into [this](https://stackoverflow.com/questions/16829736/windows-changing-the-name-icon-of-an-application-associated-with-a-file-type) & default filetype / default app, more [here](https://www.howtogeek.com/12383/change-a-file-types-icon-in-windows-7/) 


- good [resource](https://www.makeuseof.com/tag/customize-icon-windows/) with some icon modify tips 

[[Windows]]