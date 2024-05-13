# CSSCleaner :  A tool to clean up stranded css 
### Designed to clean up unused entries in the old MUI useStyles API 

## To use the script:
`python3 csscleaner.py pathToSourceDirectory`

_For best performance, use the closest parent to the files you want parsed.  Using repo root will cause the script to check node_modules for tsx files as well_

## Notes:

This script acts on a _false negative_ assumption.  In cases of ambiguity this script is programmed to take the least intrusive and safest approach.
As a result, it may not catch every single orphaned entry in an effort to not have a false positive where an entry was actually used.