[![License](https://img.shields.io/badge/License-GPL%20v2-blue.svg)](https://gitlab.xfce.org/apps/xfce4-panel-profiles/-/blob/master/COPYING)

# xfce4-panel-profiles

Xfce4-panel-profiles is a simple application to manage Xfce panel layouts.

With the modular Xfce Panel, a multitude of panel layouts can be created.
This tool makes it possible to backup, restore, import, and export these
panel layouts.

----

This version is a fork of the original project, please check the changelog 
for further information. Basically this fork provide a better UI and the possibility
to change panels monitors when screen setup has changed. 

This come with the `template` concept, where panel-1 is always attached on primary, and other
panels to other screens, from top right to down left. Also, it is able to remove extra panels.
There are more granular options in the code, but they have been hidden be to keep things simple.

While I didn't found a reliable way to trigger a script when display setup changed, I've
this shell alias I use to fix all my panels:

```
alias reload_panels='xfce4-panel-profiles template ~/.local/share/xfce4-panel-profiles/template-home.tar.bz2'
```

Eventually, this should be called each time panels are misplaced or overlapped, but it will
be another feature for later.

Finally, I eventually plan to give back this work to the XFCE4 community, if they're interested 
by this fork. For further developpement, I took the initiative to make this program easier to install
from regular tools like `pip` or `poetry`.

To test this project, ensure you have installed glib (no issues if you're running XFCE4), git clone
this project, go into it and then run `poetry install`. You should be able to run 
the `xfce4-panel-profiles`.


Note about glade: You may need to add to your setting path a`libxfce4ui-2.xml` file, ensure the file reference your
correctly named `libray='libxfce4ui-2'`, this is an example for archlinux:

```
<?xml version="1.0" encoding="UTF-8"?>
<glade-catalog version="4.12.0" supports="gtkbuilder" name="libxfce4ui-2" library="libxfce4ui-2" domain="glade3" depends="gtk+" book="xfce4">
  <glade-widget-classes>
    <glade-widget-class name="XfceTitledDialog" generic-name="xfce-titled-dialog" title="Titled Dialog">
      <post-create-function>glade_xfce_titled_dialog_post_create</post-create-function>
      <get-internal-child-function>glade_xfce_titled_dialog_get_internal_child</get-internal-child-function>

```

----


### Homepage

[Xfce4-panel-profiles documentation](https://docs.xfce.org/apps/xfce4-panel-profiles/start)

### Changelog

See [NEWS](https://gitlab.xfce.org/apps/xfce4-panel-profiles/-/blob/master/NEWS) for details on changes and fixes made in the current release.

### Source Code Repository

[Xfce4-panel-profiles source code](https://gitlab.xfce.org/apps/xfce4-panel-profiles)

### Download a Release Tarball

[Xfce4-panel-profiles archive](https://archive.xfce.org/src/apps/xfce4-panel-profiles)
    or
[Xfce4-panel-profiles tags](https://gitlab.xfce.org/apps/xfce4-panel-profiles/-/tags)

### Installation

From source code repository: 

    % cd xfce4-panel-profiles
    % ./autogen.sh
    % make
    % make install

From release tarball:

    % tar xf xfce4-panel-profiles-<version>.tar.bz2
    % cd xfce4-panel-profiles-<version>
    % ./configure
    % make
    % make install

From developpement:

    % cd xfce4-panel-profiles
    % virtualenv .venv
    % . .venv/bin/python
    % pip install poetry
    % poetry install

### Reporting Bugs

Visit the [reporting bugs](https://docs.xfce.org/apps/xfce4-panel-profiles/bugs) page to view currently open bug reports and instructions on reporting new bugs or submitting bugfixes.

