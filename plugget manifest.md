

## notes

- [ ] can i use toml and pip isntead of a custom config template(our manifest)?
      can i load extra data from toml, just like bl_info?
> [!NOTE]- pip install # subdirectory (Fragment Identifier)
> can we reuse pip install?
> 
> ⚠️ note this is pip, not git
> [[Python pip|pip]] supports install from subdir, see [examples](https://pip.pypa.io/en/stable/cli/pip_install/?highlight=subdirectory#examples)
> but this requires a setup file or wheel. not just a directory of files (e.g. blender addons or unity packages are just folders)
> 
> ```python
> py -m pip install -e "git+https://git.repo/some_repo.git#egg=subdir&subdirectory=subdir_path"
>
> # alternative
> py -m pip install SomePackage[PDF]
> py -m pip install "SomePackage[PDF] @ git+https://git.repo/SomePackage@main#subdirectory=subdir_path"
> py -m pip install .[PDF]  # project in current directory
> py -m pip install SomePackage[PDF]==3.0
> py -m pip install SomePackage[PDF,EPUB]  # multiple extras
> ```
