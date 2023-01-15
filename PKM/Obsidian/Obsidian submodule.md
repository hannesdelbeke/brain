#public #git #submodule #obsidian

# update submodules in vault
~~The [git plugin](https://github.com/denolehov/obsidian-git) doesn't support submodules.~~ It now does on PC! 
but not on Android (due to limitations of the git library it uses.)


> [!TIP] Tip
> We can use the [execute code](https://github.com/twibiral/obsidian-execute-code) plugin to update all submodules from within Obsidian

## Update on Windows
If on windows, first add support for [[bash on windows]]
Then restart Obsidian, you now can run bash code with [execute code](https://github.com/twibiral/obsidian-execute-code)

### pull submodule
```shell
VAULT=@vault_path

# replace C:/ with /C/ in the path
WORDTOREMOVE=":"
VAULT="/${VAULT//$WORDTOREMOVE/}"

# browse to folder
cd "${VAULT//$WORDTOREMOVE/}"

# update sumbodules
git submodule update --remote

echo Done!
```

### push submodule
```shell
VAULT=@vault_path

# replace C:/ with /C/ in the path
WORDTOREMOVE=":"
VAULT="/${VAULT//$WORDTOREMOVE/}"

# browse to submodule folder
SUBMODULE="${VAULT}/public-brain" # name of submodule dir: public brain 
cd "${SUBMODULE}"  

# push changes to submodule
git add .
git commit -m "update submodule"
git push

# now update main repo
cd "${VAULT}"
git add "${SUBMODULE}"
git commit -m "updated my submodule"
git push

echo Done!
```