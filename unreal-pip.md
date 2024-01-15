
> [!warning]
> i think this module might be archivable, since [[pip Qt Unreal plugin]] now exposes pip-qt in [[Unreal]], and all pip related code is in [[py-pip]], a dependency of pip-qt.

https://github.com/hannesdelbeke/unreal-pip

## compared to py-pip
unreal-pip is a single file, so easy to vendor. (just like py-pip atm)
i do think it'll be less reliable than [[py-pip]], since it has had less usage.
py-pip is generic, and its settings aren't configured for Unreal. Plugget contains those settings in its unreal install action.

[[Python pip|pip]]
[[Unreal]]
[[my code projects]]