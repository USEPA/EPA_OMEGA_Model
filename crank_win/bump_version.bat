REM bumpversion [major|minor|patch]
REM or
REM bumpversion --new-version x.y.z
REM or any other valid bumpversion argument

cd ..

REM auto-commit any changes (might remove this in the future) otherwise bumpversion will fail if there are
REM     outstanding commits
git commit -m "commit before version bump" --all

REM bump the version
bumpversion %1 --verbose

cd crank_win
