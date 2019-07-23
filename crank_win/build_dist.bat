SET PYTHONPATH=C:\Users\Public\OMEGA2\Python3.6.7

cd ..

%PYTHONPATH%\Scripts\bumpversion minor

%PYTHONPATH%\python setup.py sdist

%PYTHONPATH%\Scripts\twine upload --repository-url https://test.pypi.org/legacy/ dist/*
