# keys

Files encrypted with [age](https://age-encryption.org). One passphrase opens all of them.

## Decrypt (on any computer)

1. Install age: `sudo pacman -S age` · `sudo apt install age` · `brew install age` ·
   Windows/other: download from https://github.com/FiloSottile/age/releases
2. Get the files: `git clone` this repository, or download `key.age` and the file you
   need from the GitHub web page (open the file, then "Download raw file").
3. Run, and type the passphrase when asked:

   ```
   age -d -i key.age github.age
   ```

## Add or replace a file

```
python storeKeys.py add github ~/path/to/file.txt
```

No passphrase needed for this. `storeKeys.py` commits, pushes, and copies to Google Drive
if an rclone remote called `gdrive:` exists.
