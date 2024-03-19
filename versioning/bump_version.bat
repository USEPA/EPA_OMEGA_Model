REM bump_version [major|minor|patch] or bump_version --new-version VERSION minor

REM auto-commit any changes otherwise bumpversion will fail if there are outstanding commits:
REM git commit -m "commit before version bump" --all

REM bump the version
bumpversion %1 --verbose
