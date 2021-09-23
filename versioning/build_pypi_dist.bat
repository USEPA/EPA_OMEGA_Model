REM usage build_dist

cd ..

REM move old distributions so twine doesn't try to re-distribute them
move dist\*.* dist_old

REM create source distribution in "dist" folder
python setup.py sdist

REM upload distribution to pypi or trypi
twine upload --repository-url https://test.pypi.org/legacy/ dist/*

cd versioning
