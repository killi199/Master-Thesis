# LaTeX Beamer Theme "Wismar"

## Installation

To avoid having to clone this theme for each new presentation, you can install it either per user (recommended) or system-wide.

### User Setup

You can install this presentation theme for re-use in your local TeX tree. To find its path, run the following command:

```sh
MYTEXTREE=$(kpsewhich --var-value TEXMFHOME)
```

If the directory does not already exist, create it. Then, clone this repository directly into your local TeX tree:

```sh
git clone https://git.hs-wismar.de/HSW-Vorlagen/beamertheme-wismar.git $MYTEXTREE/tex/latex/
```

### System Setup

For a system-wide installation, you first have to identify the system path of your TeX distribution:

```sh
TEXROOT=$(kpsewhich --var-value TEXMFDIST)
```

Afterwards you can clone the repository and copy it into the system-wide LaTeX path (root privileges might be required):

```sh
git clone https://git.hs-wismar.de/HSW-Vorlagen/beamertheme-wismar.git ./beamertheme-wismar
sudo cp -r ./beamertheme-wismar $TEXROOT/tex/latex/
```

