REM usage bumpversion [major|minor|patch]

SET PYTHONPATH=C:\Users\Public\OMEGA2\Python3.6.7

cd ..

git commit -m "commit before version bump" --all

%PYTHONPATH%\Scripts\bumpversion %1 --verbose
