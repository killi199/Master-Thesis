[![en](https://img.shields.io/badge/lang-en-blue.svg)](https://git.fiw.hs-wismar.de/HSW-Vorlagen/fiw-thesis/src/branch/master/README.en.md)
[![de](https://img.shields.io/badge/lang-de-blue.svg)](https://git.fiw.hs-wismar.de/HSW-Vorlagen/fiw-thesis/src/branch/master/README.de.md)

# LaTeX Thesis Template FIW

Template for thesis papers at FIW using the typesetting system LaTeX.

## Contents

```text
anlagen/                        Attachments, appendices, etc.
    beispiel.tex                Example attachment
    cd.tex                      File tree of the CD accompanying the printed version
    exampleCode.c               Example program code
bilder/                         Graphics
    HSLogo.jpg                  Example graphic
kapitel/                        Directory for chapters
    aufgabenstellung.tex        Assignment
    beispiel.tex                Example chapter
    einleitung.tex              Placeholder Introduction
    schluss.tex                 Placeholder Conclusion
tools/                          Small helper programs
    dirtree.pl                  Perl script for semi-automatic generation of DirTree contents
verzeichnisse/                  Abbreviations, symbols, glossary
    abkuerzungen.tex            Content of abbreviation directory
    glossar.tex                 Content of glossary
    symbole.tex                 Content of symbol directory
fiwthesis.cls                   Document class (edit only if you know what you are doing!)
Makefile                        Makefile for creating the thesis
quellen.bib                     Literature database
README.md                       Information about the template (this file)
thesis.tex                      Central document / framework of the thesis
.drone.yml                      Configuration file for Drone CI/CD Pipeline
```

## LaTeX Environment Installation

The template provides the possibility to use various operating systems and development environments to create the thesis.
For more information, please refer to the following installation instructions.

For a containerized LaTeX environment, see section [Visual Studio Code and Devcontainer](#visual-studio-code-and-devcontainer).

### Prerequisites

To create your thesis in PDF format, you need:

- an up-to-date LaTeX distribution ([TeX Live](https://www.tug.org/texlive/), [MiKTeX](https://miktex.org/), or [MacTeX](https://www.tug.org/mactex/))
- the LaTeX compiler lualatex (usually included in the distributions)
- [Python](https://www.python.org/downloads/) (version 2.6 or higher) for the minted LaTeX package
- [Perl](https://www.perl.org/get.html) for auxiliary programs
- the Perl scripts [`makeglossaries`](https://ctan.org/tex-archive/macros/latex/contrib/glossaries) and [`biber`](https://biblatex-biber.sourceforge.net/) for creating the glossary, abbreviation and symbol directories, and bibliography (should also be included in the distribution)

Due to the use of the packages _fontspec_ and _selnolig_, LuaLaTeX must be used as the compiler.

If you use a specific LaTeX editor such as Kile, TeXstudio, TeXnicCenter, etc., the required dependencies are usually already fulfilled.
However, please verify that the paths to the required commands, especially `makeglossaries`, are correctly set.

### GNU/Linux

#### Ubuntu / Debian / Linux Mint / ElementaryOS / Pop!_OS / Raspberry Pi OS

1. Install the required packages:

```sh
sudo apt-get install texlive-base texlive-xetex texlive-luatex texlive-science texlive-latex-extra texlive-bibtex-extra texlive-lang-german texlive-pictures biber python3 python3-pygments ttf-bitstream-vera
```

### MacOS

1. Download [MacTeX](https://tug.org/mactex/mactex-download.html)
2. Follow the installation instructions

### Windows 10 / Windows 11

The recommended approach for Windows 10 and 11 is to use the Windows Subsystem for Linux (WSL).
For editing, it is recommended to use VSCode with the WSL extension.

1. Install the ['WSL' extension](https://marketplace.visualstudio.com/items?itemName=ms-vscode-remote.remote-wsl).
1. Connect to WSL via `CTRL + SHIFT + P` and execute `>WSL: connect to WSL` or by clicking on the Remote Window Button at the bottom left corner of the window.
By default, this installs Ubuntu 22.04.
1. Open a terminal in WSL via the menu bar `Terminal/New Terminal` and execute the following command:

```sh
sudo apt-get update && sudo apt-get upgrade && sudo apt-get install texlive-base texlive-xetex texlive-luatex texlive-science texlive-latex-extra texlive-bibtex-extra texlive-lang-german texlive-pictures biber python3 python3-pygments ttf-bitstream-vera
```

This updates the system and installs all necessary packages.

## Compilation

The sequence of commands to create a PDF version of the thesis is identical to the 'all' rule in the Makefile:

1. lualatex thesis
1. biber thesis
1. makeglossaries thesis
1. lualatex thesis
1. lualatex thesis
1. lualatex thesis

or simply `make`, if installed.

Please ensure that the "Build Chain" of your LaTeX editor is set up exactly like this if you are not using a Makefile.

## Editor Integration

### Visual Studio Code

#### Installation

1. Install an up-to-date LaTeX distribution, e.g., TeX Live.
1. Open the template in VS Code (File > Open Folder).
1. VS Code prompts you to install the LaTeX extension.
If not, please manually install the LaTeX extension by searching for LaTeX Workshop in the Extension Explorer and install it.

#### Usage

In the `.vscode` folder, you will find the two files `extensions.json` and `settings.json`, which contain recommended extensions and settings for the LaTeX-Workshop extension.

The `LaTeX-Workshop` extension is a powerful toolkit highly recommended for writing in VSCode.
It provides code snippets, command auto-completion, and environments auto-completion.
However, for additional optional useful features like `latexindent` and `synctex`, packages are required, which need to be manually installed and configured.
More information on configuring LaTeX Workshop can be found in the project wiki on GitHub.

By default, all generated log files are hidden in the File Explorer to ensure better clarity.

### Visual Studio Code and Devcontainer

With the help of a [Devcontainer](https://code.visualstudio.com/docs/devcontainers/containers), you can use VS Code without having to install a LaTeX compiler or any other LaTeX packages on your system.
You only need to meet the following requirements:

1. You must have Visual Studio Code installed on your system
1. You must have Docker installed on your system
1. You must have the `Dev Containers` extension installed in VS Code.

All recommended extensions are also installed in the Devcontainer.

#### Starting the Devcontainer

To start the Devcontainer, open the Command Palette (`CTRL + SHIFT + P`) and type `Dev Containers: Reopen in Container` (or the equivalent in your set language).
This will start the container.
The initial start may take a moment.
Once you are connected to the container (indicated by the green VS Code connection indicator in the lower-left corner), you can start writing.

## Note for Overleaf Users

If you use this template in Overleaf, please note that following project settings (to be reached by clicking the top left Menu button) have to be set:

- Compiler: LuaLaTeX
- TeX Live version: 2023
- Main Document: thesis.tex

## Using This Repository as a Template for Your Own Repository

When creating your own repository for your thesis, you can select HSW-Vorlagen/fiw-thesis as a template.
This automatically provides you with the currently active version as the basis for your work.

## Customization

Start customizing the thesis by inserting your personal information into the file 'thesis.tex' instead of the placeholder text.

There is already an example chapter in the 'kapitel/' directory.
If you are new to LaTeX, take a look at it.

Create a separate file in the 'kapitel/' directory for each chapter and reference this file in 'thesis.tex' after the introduction.
This way, you can quickly change the structure.

This template includes a small selection of useful packages.
If you need additional packages, include them in the preamble of 'thesis.tex'.
Describing all functions of each package here is not meaningful.
All used packages can be found on [CTAN](https://ctan.org/), as well as their respective documentation, which provides a deeper insight into each package.

Attachments are stored for clear separation in the separate directory 'anlagen/'; please store images and graphics in the 'bilder' directory.

The file 'fiwthesis.cls' contains all formatting options as well as the title page of the thesis and the declaration of independence.
Please only change the text if it is an official change.
In this case, please publish this change in [Git](https://giw.fiw.hs-wismar.de).

If you create abbreviation, symbol, and glossary directories, the program makeglossaries must be installed on your computer.
The necessary files for the abbreviation directory and glossary are usually not automatically created by the LaTeX compiler.

## Drone CI/CD Pipeline

For this project, there is a [Drone CI/CD](https://www.drone.io) pipeline defined in the file .drone.yml.
This file is only used to automate the further development of the project and is not necessary for building the LaTeX project.

The pipeline consists of two steps: 'make project' and 'pdf push master'.
The former is executed on every push and attempts to rebuild the project from scratch using `make clean && make all`.
The second step is only executed if the first step is successfully completed AND the current branch is `master`.
A commit is then created for the generated PDF file and pushed to the `master` branch.

## Contribution

This project is accessible in the [Git der FIW](https://git.fiw.hs-wismar.de/HSW-Vorlagen/fiw-thesis).

If you wish to contribute changes to the project, please open a [pull request](https://git.fiw.hs-wismar.de/HSW-Vorlagen/fiw-thesis/pulls) (only for the development branch).

## Questions

Questions, issues, or errors can be opened in the Git repository as [issues](https://git.fiw.hs-wismar.de/HSW-Vorlagen/fiw-thesis/issues).
This also helps future users in answering questions that may be frequently asked.

## Related Projects

### HSW-Beamer

Presentation slides in the design of the Hochschule Wismar with LaTeX.

[https://git.fiw.hs-wismar.de/HSW-Vorlagen/hsw-beamer](https://git.fiw.hs-wismar.de/HSW-Vorlagen/hsw-beamer)

### FIW-Poster

Poster for the thesis with LaTeX.

[https://git.fiw.hs-wismar.de/HSW-Vorlagen/fiw-poster](https://git.fiw.hs-wismar.de/HSW-Vorlagen/fiw-poster)
