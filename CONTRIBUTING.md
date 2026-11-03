# Team GitHub workflow

Use one shared repository. Each member uses their own GitHub account and Git commit name/email. The repository owner invites members as collaborators. A private repository is accessible only to authorised members.

## First time

Install Git and Python with Tkinter support. Clone the repository using its actual GitHub URL, then open the cloned folder in VS Code. The current local project already has Git initialised; its owner does not need to clone it again.

```sh
git clone YOUR_REPOSITORY_URL
```

The URL above is a placeholder: replace it with the real repository URL. Run `python3 simulator.py` on Mac or `py simulator.py` on Windows. Use a Python installation with modern Tk support on Mac.

Configure your identity once inside your clone:

```sh
git config user.name "Your Name"
git config user.email "YOUR_GITHUB_VERIFIED_OR_NOREPLY_EMAIL"
```

## For each change

Start from an up-to-date main branch. Commit your current work before switching branches.

```sh
git switch main
git pull --ff-only
git switch -c feature/describe-your-change
```

Edit and run the simulator. Check the simulation rules:

```sh
python3 -m unittest discover -v
```

On Windows, replace `python3` with `py`. Review the changes before committing:

```sh
git status
git diff
git add simulator.py README.md
git diff --cached
git commit -m "Describe what changed"
git push -u origin HEAD
```

Only stage files you actually intended to change; adjust the example filenames. Open a pull request on GitHub and have another team member review it. Merge after review and passing checks. Everyone then updates main with `git pull --ff-only`.

Avoid editing the same part of simulator.py at the same time. Coordinate ownership of functions. If Git reports a conflict, resolve it together before continuing; do not force-push shared main.

Push after each complete, tested change so team members can retrieve it. Editing or saving a file alone does not upload it to GitHub.

Never commit passwords, access tokens or local environments. Authenticate through GitHub sign-in, not by sharing credentials in chat. The machine-specific Mac launcher is intentionally excluded from Git.
