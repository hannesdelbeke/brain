https://www.amazon.co.uk/sendtokindle

usb micro

Remove ads on kindle untll next sync / update:
```batch
REM set /p letter= "Enter your Kindle device drive letter and press ENTER 'ex: e' "
set /p letter=E
set path=%letter%:\system\.assets
rd %path% /S /Q
type nul > %path%
attrib -r -s -h /S /D %path%

if exist %path%\* (
	msg * Ha ocurrido un error, los anuncios de tu Kindle NO se han podido eliminar.
	cls
	echo Ha ocurrido un error, los anuncios de tu Kindle NO se han podido eliminar.
) else (
	msg * Los anuncios de tu Kindle se han eliminado correctamente.
	cls
	echo Los anuncios de tu Kindle se han eliminado correctamente.
)
pause
```

[[Amazon]]