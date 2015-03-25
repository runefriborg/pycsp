# New Release #

Procedure for creating new release.

## Test ##

Tests:
```
cd trunk/test
Run all tests for all implementations
```

Examples:
```
cd trunk/examples
Run all examples for all implementations
```
## Verify ##
```
Update version ids for all implementations.
Update CHANGES.txt to match the actual changes for this version.
Run svn stat to ensure that all relevant files have been committed to trunk.
```

## Create tag release ##
```
svn copy https://pycsp.googlecode.com/svn/trunk https://pycsp.googlecode.com/svn/tags/PyCSP-0.6.2 -m 'Tag release 0.6.2'
```

## Create tgz release file ##

```
svn update
cd tags/PyCSP-0.6.2
python setup.py build sdist
```
## Test install ##

Do test install on as many platforms as possible.
Check that pycsp can be imported and run a few examples.

## Upload tgz to Google Code ##

Go to [Downloads ](http://code.google.com/p/pycsp/downloads/list), upload and
set as Featured.

## Create deb package for PPA ##
Its required to have a debian folder.
from trunk  compile the the source and put it in parent folder
```
python setup.py sdist --dist-dir=../
```
Rename the pycsp_'version'.tar.gz file in the parent folder to pycsp_'version'.orig.tar.gz

From folder where the debian folder exist run:
```
debuild -i -I -S
```
This produces a changes file and it can now be uploaded to launchpad.
In the parent folder run
```
dput -f ppa:pycsp/ppa pycsp_'version'_source.changes 
```