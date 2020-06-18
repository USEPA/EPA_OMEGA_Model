@ECHO OFF

pushd %~dp0

REM Command file for Sphinx documentation

C:\Users\Public\OMEGA2\Python3.6.7\Scripts\sphinx-apidoc -o source "C:\Users\tsherwoo\Documents\GitHub\EPA_OMEGA_Model\omega2" -f -a -H omega2 -V 0.0.1 --tocfile code

if "%SPHINXBUILD%" == "" (
	set SPHINXBUILD="C:\Users\Public\OMEGA2\Python3.6.7\Scripts\sphinx-build"
)
set SOURCEDIR=source
set BUILDDIR=build

REM if "%1" == "" goto help

%SPHINXBUILD% >NUL 2>NUL
if errorlevel 9009 (
	echo.
	echo.The 'sphinx-build' command was not found. Make sure you have Sphinx
	echo.installed, then set the SPHINXBUILD environment variable to point
	echo.to the full path of the 'sphinx-build' executable. Alternatively you
	echo.may add the Sphinx directory to PATH.
	echo.
	echo.If you don't have Sphinx installed, grab it from
	echo.http://sphinx-doc.org/
	exit /b 1
)

REM %SPHINXBUILD% -M %1 %SOURCEDIR% %BUILDDIR% %SPHINXOPTS% %O%
goto end

:help
%SPHINXBUILD% -M help %SOURCEDIR% %BUILDDIR% %SPHINXOPTS% %O%

:end
popd
