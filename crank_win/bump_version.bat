REM bump_version [major|minor|patch]

cd ..

REM auto-commit any changes (might remove this in the future) otherwise bumpversion will fail if there are
REM     outstanding commits
REM git commit -m "commit before version bump" --all

REM bump the version
bumpversion %1 --verbose

cd crank_win
