
Default Obsidian styling in the dark theme:
- <span style="background:#202020; color:#dcddde">This sentence is <font color="#7f6df2"><u>easy to read</u></font> without <font color="#99caf"><u>visual</u></font> interruption.</span>
A sentence with normal text formatting is easier to read:
- <span style="background:#202020; color:#dcddde">This sentence is easy to read without visual interruption.</span>
My custom styling tries to have the best of both worlds:
- <span style="background:#202020; color:#dcddde">This sentence is <font color="#AE8CFF">easy to read</font> without <font color="#ADD8E6">visual</font> interruption.</span>

## Problem: text color
I find that [[wikilink|wikilinks]] in text decrease the readability of my notes. Because links are colored dark purple, which clashes with the white color from normal text. A colored word in the middle of a sentence, interrupts the reading flow.
### Solution
in Obsidian settings, you can change accent color which changes note link color.
## Problem: underline
Links are underlined to distinguish them from text. This underline also disrupts reading flow a bit. I think just a color difference would do the trick for me. I already know purple is a local link, and blue is a [[URL]].
- [forum post](https://forum.obsidian.md/t/how-to-remove-underline-in-links/59705)
- [reddit thread](https://www.reddit.com/r/ObsidianMD/comments/w46tft/remove_underline_change_color_of_internal_links/)
- I noticed the obsidian forum also doesn't use underline's in links.
- I already set [[URL]] color in [[Obsidian distinguish internal & external links]]. I should be able to remove underline there too.
- [x] links to non-existing notes are currently distinguished by not being underlined.  It'd be better to change this e.g. to color red. Else when we remove the underline for working links it'll look too similar.
	- [x] [[Obsidian - color unlinked notes red]] 
### Solution
add 
```css
text-decoration: none !important; /* remove underline*/
```
to each css entry
```
.span.cm-link a.cm-underline
.span.cm-url a.cm-underline
.external-link
.cm-hmd-internal-link a.cm-underline
```
I added it in the same css as [[Obsidian distinguish internal & external links]].

### Review
looks a lot better, now that underline is removed, i increased color slightly again since we still need links to stand out somehow. I got the right balance now and text reads a lot more natural now.


## tags
[[Obsidian css]]
[[Obsidian improvements]]

