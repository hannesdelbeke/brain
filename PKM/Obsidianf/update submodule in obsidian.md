#public #git #submodule #obsidian

~~The [git plugin](https://github.com/denolehov/obsidian-git) doesn't support submodules.~~ It now does on PC!

Instead we can use [execute code](https://github.com/twibiral/obsidian-execute-code) plugin to easily update submodules from in Obsidian (PC only)

If on windows, first add support for [[bash on windows]]

## pull submodule
```shell
RAWVAULT=(@vault)

# bug fix since the plugin has issues
WORDTOREMOVE="app://local/"
VAULT="${RAWVAULT//$WORDTOREMOVE/}"

# replace C:/ with /C/ in the path
WORDTOREMOVE=":"
VAULT="/${VAULT//$WORDTOREMOVE/}"

# browse to folder
cd "${VAULT//$WORDTOREMOVE/}"

# update sumbodules
git submodule update --remote

echo $VAULT  # this fixes it
```

## push submodule
```shell
RAWVAULT=(@vault)

# bug fix since the plugin has issues
WORDTOREMOVE="app://local/"
VAULT="${RAWVAULT//$WORDTOREMOVE/}"

# replace C:/ with /C/ in the path
WORDTOREMOVE=":"
VAULT="/${VAULT//$WORDTOREMOVE/}"
#VAULT_PATH="${VAULT//$WORDTOREMOVE/}" #bash friendly path
SUBMODULE="${VAULT}/public-brain"

# browse to submodule folder
cd "${SUBMODULE}"  # replace public brain with name of your submodule folder

# push changes to submodule
git add .
git commit -m "update submodule"
git push

# now update main repo
cd "${VAULT}"
git add "${SUBMODULE}"
git commit -m "updated my submodule"
git push

echo $VAULT  # this fixes it
```