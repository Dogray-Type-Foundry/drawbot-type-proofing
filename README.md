# drawbot-type-proofing
Scripts for generating type proofs using Drawbot

## Requirements

If you are unfamiliar with Drawbot and working with code, using this script will be a bit more difficult at first, but I will do my best to guide you.

First, download the latest Drwbot version from (https://www.drawbot.com/content/download.html).

In order to install the required libraries your computer should be able to use git as a command, and sadly that requires installing a set of command line tools from Apple. You could install those, or you could instead install [Homebrew](https://brew.sh) which will autoamtically install a minimal version of the Apple tools. To install Homebrew, copy the following code into your Terminal app prompt and press `Enter`:

```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
```
Hombrew will install and the tools that we need will be installed with it.

To install the required libraries in DrawBot, open the package manager with the menu `Python -> Install Python Packages` and then copy and paste the following string:

```Python
fonttools unicodedata2 git+https://github.com/mathieureguer/drawbotgrid git+https://github.com/tallpauley/wordsiv
```

and then press `Go`.

Here are the links to the repositories where you can find each library in case you want to know a bit more about what they do:
- [fonttools](https://github.com/fonttools/fonttools)
- [unicodedata2](https://github.com/fonttools/unicodedata2)
- [drawBotGrid](https://github.com/mathieureguer/drawbotgrid)
- [Wordsiv](https://github.com/tallpauley/wordsiv)

## General proofing document generation

After installing the required libraries in Drawbot, open the `drawbot_type_proofing.py` file in Drawbot and make sure you add the fonts you want to proof in `fonts/` folder. Alternatively, you can define a custom list of fonts to proof by adding them as a list to the `customLocation` variable, and that will maintain the order of the list for the proofs themselves. That would look something like this:

```python
customLocation = ("fonts/WorkSans[wght].ttf","fonts/WorkSans-Italic[wght].ttf",)
```

Once the script finishes running, you can find the proof in the `proofs/` folder.

## Credits and thanks

The script started as a fork of DJR's [simpleProof](https://github.com/djrrb/Drawbot-Type-Proofs/blob/master/simpleProof/simpleProof.py) script, which was then expanded with a ton of additional functionality. The structure of the pages is quite flexible thanks to [DrawBotGrid](https://github.com/mathieureguer/drawbotgrid) by Mathieu Réguer. Finally, [Wordsiv](https://github.com/tallpauley/wordsiv) by Chris Pauley is what allows this script to provide usefull texts even at the beginning of a project when you have a small character set. It has been truly game changing.
