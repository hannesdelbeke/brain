Change the capitalization of a file that's already commit to the the repository can be tricky.

[[Perforce]] won't let you do this by default it it runs on a Windows server. (see [article](https://portal.perforce.com/s/article/3448))

[[Git]] is easier to do. (see [post](https://stackoverflow.com/questions/10523849/how-do-you-change-the-capitalization-of-filenames-in-git))
either of these 2:
```
git config --global core.ignorecase false
git mv --force myfile MyFile
```