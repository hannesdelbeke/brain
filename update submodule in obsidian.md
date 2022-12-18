#public #git #submodule #obsidian

the git plugin doesn't support pulling updates on submodules
instead of updating the git plugin code, we can use [execute code](https://github.com/twibiral/obsidian-execute-code) from notes plugin

if on windows, do this first: [[bash on windows]]

## run this to update submodules in obsidian directory
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

push submodule updates
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