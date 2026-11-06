#!/usr/bin/env python3
"""storeKeys.py - encrypt files with age, commit + push them, and copy them to Google Drive.

  python storeKeys.py init                    create key.age (asks for your passphrase) + recipient.txt
  python storeKeys.py add <company> <file>    encrypt <file> as <company>.age and publish it

Adding never needs the passphrase: files are encrypted to the public key in recipient.txt.
Only decrypting needs it:  age -d -i key.age <company>.age
"""
import argparse
import os
import re
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent
KEY = REPO / "key.age"
RECIPIENT = REPO / "recipient.txt"
# rclone "remote:folder" for the Google Drive copy; skipped if the remote isn't configured
DRIVE = os.environ.get("STOREKEYS_DRIVE", "gdrive:keys")


def run(*cmd, **kw):
    return subprocess.run(cmd, check=True, **kw)


def git(*args, **kw):
    return run("git", "-C", str(REPO), *args, **kw)


def publish(files, message):
    git("add", *files)
    if subprocess.run(["git", "-C", str(REPO), "diff", "--cached", "--quiet"]).returncode:
        git("commit", "-q", "-m", message)
        print(f"Committed: {message}")
    else:
        print("Nothing changed, no commit made.")

    if "origin" in git("remote", capture_output=True, text=True).stdout.split():
        try:
            git("push", "-q", "origin", "HEAD")
            print("Pushed to GitHub.")
        except subprocess.CalledProcessError:
            print("!! git push FAILED - run `git push` in", REPO, "when the problem is fixed.")
    else:
        print("No 'origin' remote yet, skipped GitHub push.")

    remote = DRIVE.split(":")[0] + ":"
    if remote in run("rclone", "listremotes", capture_output=True, text=True).stdout.split():
        try:
            run("rclone", "copy", str(REPO), DRIVE,
                "--include", "*.age", "--include", "recipient.txt", "--include", "README.md")
            print(f"Copied to Google Drive ({DRIVE}).")
        except subprocess.CalledProcessError:
            print("!! Google Drive copy FAILED - the GitHub copy is unaffected.")
    else:
        print(f"No rclone remote '{remote}' configured, skipped Google Drive.")


def cmd_init(_args):
    if KEY.exists():
        sys.exit("key.age already exists. Refusing to overwrite it (that would lock you out of every file).")
    identity = run("age-keygen", capture_output=True).stdout          # private key, kept in memory only
    public = run("age-keygen", "-y", input=identity, capture_output=True).stdout
    print("Choose your passphrase. age asks for it twice; leave it empty to have one generated for you.")
    run("age", "-p", "-a", "-o", str(KEY), input=identity)
    RECIPIENT.write_bytes(public)
    publish(["key.age", "recipient.txt"], "Add key")
    print("\nNext: add a file, then check you can open it:  age -d -i key.age <company>.age")


def cmd_add(args):
    name = args.company.lower()
    if not re.fullmatch(r"[a-z0-9][a-z0-9-]*", name):
        sys.exit("Use a simple name like github, vercel or google-work (letters, digits, dashes).")
    if not RECIPIENT.exists():
        sys.exit("Run `python storeKeys.py init` first.")
    src = Path(args.file).expanduser()
    if not src.is_file():
        sys.exit(f"No such file: {src}")
    out = REPO / f"{name}.age"
    action = "Replaced" if out.exists() else "Added"
    run("age", "-a", "-R", str(RECIPIENT), "-o", str(out), str(src))
    print(f"{action} {out.name} (encrypted from {src}; the original was not touched).")
    publish([out.name], f"Update {name}")


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="cmd", required=True)
    sub.add_parser("init", help="create the passphrase-protected key").set_defaults(func=cmd_init)
    a = sub.add_parser("add", help="encrypt a file and publish it")
    a.add_argument("company", help="name for the encrypted file, e.g. github")
    a.add_argument("file", help="plaintext file to encrypt")
    a.set_defaults(func=cmd_add)
    args = p.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
