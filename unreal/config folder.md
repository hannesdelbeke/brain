What's the difference between `unrealProject/saved/config` &  `unrealProject/config`

## Project/Config
- Project/Config is project-level settings, 
- Config folder refers to Project/Config. 
- should be in version control

## Project/Saved/Config
- `Saved/Config` is usually things like user-preferences & keybinds.
- (configs in) your saved folder refers to `Project/Saved/Config`
- Configs in Saved are usually auto-generated from preferences and customized things in the editor.  You can manually edit them while the editor is closed, but most settings are accessible in the editor
- usually `Project/Saved/Config` folder should not be in version control, so it only contains local settings.