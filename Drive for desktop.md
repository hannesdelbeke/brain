You can [[file sync|sync]] or [[virtual file system|mirror]] files from [[Google Drive]] to your [[Windows]] pc.
When [[backup|backing up]] a folder, you're given the option to store on Drive or [[Google Photos]].
- drive. local edits or deletes are synced to drive
- photos: local edits upload a new file. local deletes are ignored. not a true [[file sync|sync]]

> [!NOTE]- friction points - Google Photos
> since [[Google Photos]] doesn't support true sync, it's a bit limited.
> Seems only [[Google Takeout]] can be used atm to back up Photos, which is a manual step. 
>
> - how to back up google photos [reddit thread](https://www.reddit.com/r/GooglePixel/comments/15kjvmb/whats_the_best_way_for_an_individual_to_backup/)
> - From March 31, 2025 rclone can only download photos it uploaded. In the past it could be used to backkup google photos. see https://rclone.org/googlephotos/
> - The Google Photos API has quite a few limitations
> 	- https://rclone.org/googlephotos/#limitations
> 	- seems the API is designed for compressed quality, aimed at online view, not raw source files.


