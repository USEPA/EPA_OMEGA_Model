REM usage build_dist [major|minor|patch]

SET PYTHONPATH=C:\Users\Public\OMEGA2\Python3.6.7

cd ..

move dist\*.* dist_old

%PYTHONPATH%\python setup.py sdist

%PYTHONPATH%\Scripts\twine upload --repository-url https://test.pypi.org/legacy/ dist/*
