# Description of Display

## Common
![](pic/ss02.png)
- "Save all changes" buttton
  - save captions to text file
    - changes will not be applied to the text files until you press this button
  - if "Backup original text file" is checked, original text files will be renamed not to be overwritten
    - backup file name will be like filename.000, -.001, -.002, ...
  - new caption text file will be created if it does not exist
- "Reload/Save Settings" Accordion (closed initially)
  - you can reload/save/restore all settings in the UI here
  - settings will be saved in `.../tag-editor-root-dir/config.json`
- "Dataset Directory" text box
  - input the directory of training images and load them by clicking "Load" button
  - loading options are below
  - you can make caption on loading by using interrogator if needed
- "Dataset Images" gallery
  - to view and select images
  - the number of colums can be changed in web UI's "Settings" tab

***

## "Filter by Tags" tab
![](pic/ss03.png)
### Common
- "Clear tag filters" button
  - clear tag search text and tag selection
- "Clear ALL filters" button
  - clear all filters including image selection filter in the next tab

### Search tags / Filter images by tags
Positive (inclusive) / Negative (exclusive) filters can be used by toglling tabs.
- "Search Tags" text box
  - search and filter the tags displayed below
- "Sort by / Sort order" radio buttons
  - change sort order of the tags displayed below
- "Filter Images by Tags" checkboxes
  - filter images displayed in the left gallery by tags
    - also filter tags depending on captions of the displayed images

***

## "Filter by Selection" tab
![](pic/ss04.png)

- "Add selection" button
  - to include selected dataset image in selection
  - "Enter" is shortcut key
  - Tips: you can change the selected image in gallery using arrow keys
- "Remove selection" button
  - to remove selected image from selection
  - "Delete" is shortcut key
- "Invert selection" button
  - select all images in the entire dataset that have not been selected
- "Clear selection" button
  - to remove all current selection, not to clear current filter
- "Apply selection filter" button
  - apply selection filter on displaying dataset images

***

## "Batch Edit Captions" tab
![](pic/ss05.png)
### "Search and Replace" tab

- "Edit common tags" is a simple way to edit tags.
  - "Common Tags" text box (not editable)
    - shows the common tags among the displayed images in comma separated style
  - "Edit Tags" text box
    - you can edit the selected tags for all captions of the displayed images
      - each tags will be replaced by the tags in "same place"
      - erase tags by changing it into blank
      - you can add some tags to the captions by appending new tags
        - the tags will be added to the beggining/end of text files depending on the checkbox below
  - "Apply changes to filtered images" button
    - apply the tag changes only to displayed images

- "Search and Replace" is a little complicated but powerful way to edit tags.
  - Regular expression can be used here.
  - "Search/Replace Text" textboxes
    - "Search Text" will be replaced by "Replace Text"
  - "Search and Replace in" radio buttons 
    - to select the replacing method
      - "Only Selected Tags" : do replace sepalately in each only selected tags
      - "Each Tags" : do replace sepalately in each tags
      - "Entire Caption" : do replace in entire caption at once
  - "Search and Replace" button to apply

### "Remove" tab
Simple way to batch remove tags
- "Remove duplicate tags" button
  - make each tags in each captions appear only once
- "Remove selected tags" button
  - remove tags selected below

***

## "Edit Caption of Selected Image" tab
![](pic/ss06.png)

### "Read Caption from Selected Image" tab
- "Caption of Selected Image" textbox
  - shows the caption of the selected image in the dataset gallery

### "Interrogate Selected Image" tab
- "Interrogate Result" textbox
  - shows the result of interrogator

### Common
- "Copy and Overwrite / Prepend / Apppend" button
  - copy/prepend/append the content in the textbox above to the textbox below
- "Edit Caption" textbox
  - edit caption here
- "Apply changes to selected image" button
  - change the caption of selected image into the text in "Edit Tags" textbox

***

## "Move or Delete Files" tab
![](pic/ss07.png)
- "Move or Delete" radio buttons to select target image
- "Target" checkboxes to select which files to be moved or deleted
- "Move File(s)" button
  - move files to "Destination Directory"
- "DELETE File(s)" button
  - delete files
  - Note: This won't move the files into $Recycle.Bin, just do DELETE them completely.