https://github.com/hannesdelbeke/plugget-unreal
bring [[plugget]] to [[Unreal]]

# dev notes
- [ ] slow on Unreal startup.
- [ ] pip freezes Unreal
`LogPython: Successfully installed PySide2-5.15.2.1 detect-app-0.0.2 plugget-0.0.12 plugget-qt-0.0.1 shiboken2-5.15.2.1`
- [ ] if we do keep the upgrade, document that this freezes the app.

- [x] [[good install instructions]]
- [x] auto pip installs plugget & dependencies

install seems to silent fail 
clone seems to fail
where is it installed in unreal?

uninstall plugget
install plugget from local dev

## development
installing plugget_qt as editable.
1. pip uninstall plugget_qt
2. clone plugget_qt locally 
3. editable install plugget_qt
AFAIK if version changes need to reinstall?

other option: edit PATH
this let's you swap without uninstalling

