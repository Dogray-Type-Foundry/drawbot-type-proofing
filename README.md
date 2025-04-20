# drawbot-type-proofing
Scripts for generating type proofs using Drawbot

## Requirements

To install the required libraries in DrawBot, open the package manager with the menu Python -> Install Python Packages and then copy and paste the following string:

```Python
fonttools unicodedata2 git+https://github.com/mathieureguer/drawbotgrid git+https://github.com/tallpauley/wordsiv
```

and then press `Go`.

Here are the links to the repositories where you can find each library:
- [fonttools](https://github.com/fonttools/fonttools)
- [unicodedata2](https://github.com/fonttools/unicodedata2)
- [drawBotGrid](https://github.com/mathieureguer/drawbotgrid)
- [Wordsiv](https://github.com/tallpauley/wordsiv)

## How to use

After installing the required libraries in Drawbot, make sure you add the fonts you want to proof in `fonts/` folder. Alternatively, you can define a custom list of fonts to proof, and that will maintain the order of the list for the proofs themselves. Once the script finishes running, you can find the proof in the `proofs/` folder.

## Credits and thanks

The script started as a fork of DJR's [simpleProof](https://github.com/djrrb/Drawbot-Type-Proofs/blob/master/simpleProof/simpleProof.py) script, which was then expanded with a ton of additional functionality. The structure of the pages is quite flexible thanks to [DrawBotGrid](https://github.com/mathieureguer/drawbotgrid) by Mathieu Réguer. Finally, [Wordsiv](https://github.com/tallpauley/wordsiv) by Chris Pauley is what allows this script to provide usefull texts even at the beginning of a project when you have a small character set. It has been truly game changing.
