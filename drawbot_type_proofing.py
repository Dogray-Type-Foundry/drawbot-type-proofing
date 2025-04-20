from importlib import reload
import unicodedata
import datetime
import os
import random
import logging
import drawBot as db

from wordsiv import WordSiv
from itertools import product

from fontTools.ttLib import TTFont
from fontTools.agl import toUnicode

from drawBotGrid import BaselineGrid, columnBaselineGridTextBox

import proof_texts

reload(proof_texts)
import proof_texts as pte


########################
# SETUP

# Change logging to WARNING if you want to know when wordsiv can't find a word
# with the parameters you requested
log = logging.getLogger("wordsiv")
log.setLevel(logging.ERROR)


# Font path
def get_files(path):
    files_toprocess = []
    extensions = (".ttf", ".otf")
    for root, dirs, files in os.walk(path):
        for e in extensions:
            files_toprocess += [
                str(os.path.join(root, f)) for f in files if f.endswith(e)
            ]
    return files_toprocess


fontFolder = "fonts/"

customLocation = ("fonts/WorkSans[wght].ttf",)
# customLocation = ()

if customLocation:
    fonts = customLocation
else:
    fonts = get_files(fontFolder)

# Set your own axes values manually. Otherwise, leave empty and the script
# will automatically use the master instances.
axesValues = {"wght": (100, 400, 900)}
# axesValues = {}
# axesValues = {"wght": (100, 900), "ital": (0,1)}

# Some constants related to page and layout
# Page dimensions and margin
pageDimensions = "A4Landscape"
marginVertical = 50
marginHorizontal = 40

# Font sizes
charsetFontSize = 90
spacingFontSize = 14
largeTextFontSize = 24
smallTextFontSize = 9
fullCharSetSize = 48

# Seeds used for wordsiv and for regular vs italic/bold proofs
wordsivSeed = 987654
dualStyleSeed = 1029384756

# OpenType features
otfeatures = dict(kern=True)

# Fallback font. Adobe Blank should be in the same folder as the script
# when running it.
myFallbackFont = "adobe_blank/AdobeBlank.otf"

useFontContainsCharacters = True


# Some fsSelection values in bits format
class FsSelection:
    ITALIC = 1 << 0
    BOLD = 1 << 5
    REGULAR = 1 << 6


#################################
# Some helpers and categorisation

# Font and file names as well as date format
fontFileName = os.path.basename(fonts[0])
familyName = os.path.splitext(fontFileName)[0].split("-")[0]
now = datetime.datetime.now()
nowformat = now.strftime("%Y-%m-%d_%H%M")


# Character set, filtering out empty glyphs that would normally have outlines.
def filteredCharset(inputFont):
    f = TTFont(inputFont)
    gset = f.getGlyphSet()
    charset = ""
    for i in gset:
        if "." in i:
            pass
        else:
            if "CFF " in f:
                top_dict = f["CFF "].cff.topDictIndex[0]
                char_strings = top_dict.CharStrings
                char_string = char_strings[i]
                bounds = char_string.calcBounds(char_strings)
                if bounds is None:
                    continue
                else:
                    charset = charset + toUnicode(i)
            elif "glyf" in f:
                if f["glyf"][i].numberOfContours == 0:
                    continue
                else:
                    charset = charset + toUnicode(i)
    return charset


# Some set templates
upperTemplate = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
lowerTemplate = "abcdefghijklmnopqrstuvwxyz"


def findAccented(g):
    decomp = unicodedata.normalize("NFD", g)
    if len(decomp) < 2:
        pass
    else:
        if unicodedata.category(decomp[1]) == "Mn":
            return True


# Categorize each character base on it's unicode category.
def categorize(charset):
    uniLu = ""  # Letter Uppercase
    uniLl = ""  # Letter Lowercase
    uniPo = ""  # Punctuation Other
    uniPc = ""  # Punctuation Connector
    uniPd = ""  # Punctuation Dash
    uniPs = ""  # Punctuation Open
    uniPe = ""  # Punctuation Close
    uniPi = ""  # Punctuation Initial Quote
    uniPf = ""  # Punctuation Final Quote
    uniSm = ""  # Symbol Math
    uniSc = ""  # Symbol Currency
    uniNd = ""  # Numbers
    uniNo = ""  # Other numerical characters like fractions
    uniLlBase = ""
    uniLuBase = ""
    accented = ""

    for i in charset:
        if unicodedata.category(i) == "Ll":
            uniLl += i
            if findAccented(i):
                accented += i
            elif not findAccented(i):
                uniLlBase += i
        elif unicodedata.category(i) == "Lu":
            uniLu += i
            if findAccented(i):
                accented += i
            elif not findAccented(i):
                uniLuBase += i
        elif unicodedata.category(i) == "Po":
            uniPo += i
        elif unicodedata.category(i) == "Pc":
            uniPc += i
        elif unicodedata.category(i) == "Pd":
            uniPd += i
        elif unicodedata.category(i) == "Ps":
            uniPs += i
        elif unicodedata.category(i) == "Pe":
            uniPe += i
        elif unicodedata.category(i) == "Pi":
            uniPi += i
        elif unicodedata.category(i) == "Pf":
            uniPf += i
        elif unicodedata.category(i) == "Sm":
            uniSm += i
        elif unicodedata.category(i) == "Sc":
            uniSc += i
        elif unicodedata.category(i) == "Nd":
            uniNd += i
        elif unicodedata.category(i) == "No":
            uniNo += i

    uppercaseOnly = False
    lowercaseOnly = False

    # Check if Uppercase-only or Lowercase-only, or mixed-case
    if uniLu == "":
        lowercaseOnly = True
    elif uniLl == "":
        uppercaseOnly = True

    return (
        uniLu,
        uniLl,
        uniPo,
        uniPc,
        uniPd,
        uniPs,
        uniPe,
        uniPi,
        uniPf,
        uniSm,
        uniSc,
        uniNd,
        uniNo,
        accented,
        uppercaseOnly,
        lowercaseOnly,
        uniLlBase,
        uniLuBase,
    )


# Is it a Variable Font?
def variableFont(inputFont):
    isVariableFont = ""
    variableDict = db.listFontVariations(inputFont)
    if bool(variableDict):
        isVariableFont = True
    elif not variableDict:
        isVariableFont = False

    def product_dict(**kwargs):
        keys = kwargs.keys()
        vals = kwargs.values()
        for instance in product(*vals):
            yield dict(zip(keys, instance))

    # If it's a VF and you define the list of axis values to use.
    if isVariableFont and axesValues != {}:
        axesProduct = list(product_dict(**axesValues))
    # If it's a VF and you simply want to use extremes and default values.
    elif isVariableFont and axesValues == {}:
        axesContents = dict()
        for axis, data in variableDict.items():
            if (
                data["defaultValue"] == data["minValue"]
                or data["defaultValue"] == data["minValue"]
            ):
                axesContents[axis] = (data["minValue"], data["maxValue"])
            else:
                axesContents[axis] = (
                    data["minValue"],
                    data["defaultValue"],
                    data["maxValue"],
                )
        axesProduct = list(product_dict(**axesContents))
    else:
        axesProduct = ""
    return axesProduct


# This functions helps us pair uprights with italics when they exist on statics
def pairStaticStyles(fonts):
    staticUpItPairs = dict()
    staticRgBdPairs = dict()
    uprights = []
    italics = []
    regulars = []
    bolds = []

    for i in fonts:
        f = TTFont(i)
        if f["OS/2"].fsSelection & FsSelection.ITALIC:
            italics.append(i)
        else:
            uprights.append(i)

        if str(f["name"].names[0]) == f["name"].getBestFamilyName():
            if f["name"].getBestSubFamilyName() == "Regular":
                regulars.append(i)
            if f["name"].getBestSubFamilyName() == "Bold":
                bolds.append(i)

    for u in uprights:
        for i in italics:
            upfont = TTFont(u)
            itfont = TTFont(i)
            if upfont["OS/2"].usWeightClass == itfont["OS/2"].usWeightClass:
                staticUpItPairs[upfont["OS/2"].usWeightClass] = (u, i)
    for r in regulars:
        for b in bolds:
            rgfont = TTFont(r)
            bdfont = TTFont(b)
            if (
                rgfont["name"].getBestFamilyName()
                == bdfont["name"].getBestFamilyName()
            ):
                staticRgBdPairs[rgfont["name"].getBestFamilyName()] = (r, b)

    return dict(sorted(staticUpItPairs.items())), dict(
        sorted(staticRgBdPairs.items())
    )


# Draw a simple footer with some minimal but useful info
def drawFooter(title):
    with db.savedState():
        # get date and font name
        today = datetime.date.today()
        fontName = db.font(indFont).split("-")[0]
        # assemble footer text
        footerText = f"{today} | {fontName} | {title}"

        # and display formatted string
        footer = db.FormattedString(
            footerText, font="Courier", fontSize=9, lineHeight=9
        )
        folio = db.FormattedString(
            str(db.pageCount()),
            font="Courier",
            fontSize=9,
            lineHeight=9,
            align="right",
        )
        db.textBox(
            footer,
            (
                marginHorizontal,
                marginVertical - 18,
                db.width() - marginHorizontal * 2,
                9,
            ),
        )
        db.textBox(
            folio,
            (
                marginHorizontal,
                marginVertical - 18,
                db.width() - marginHorizontal * 2,
                9,
            ),
        )


# Function to create a formatted string to feed into textBox
def stringMaker(
    textInput,
    fontSizeInput,
    alignInput="left",
    trackingInput=0,
    OTFeaInput=None,
    VFAxisInput=None,
    upit=False,
    rgbd=False,
):
    textString = db.FormattedString(
        txt="",
        font=indFont,
        fallbackFont=myFallbackFont,
        fontSize=fontSizeInput,
        align=alignInput,
        tracking=trackingInput,
        openTypeFeatures=OTFeaInput,
        fontVariations=VFAxisInput,
    )
    random.seed(a=dualStyleSeed)
    f = TTFont(indFont)

    # If you call for section to mix uprights and italics, and it's a static
    # font with paired up uprights and italics using the
    # pairStaticStyles function.
    if (
        upit
        and pairedStaticStyles[0]
        and f["OS/2"].fsSelection & FsSelection.ITALIC
    ):
        upFont = pairedStaticStyles[0][f["OS/2"].usWeightClass][0]
        itFont = pairedStaticStyles[0][f["OS/2"].usWeightClass][1]
        index = 0
        for i in textInput.split():
            if index % random.randrange(1, 5) == 0:
                textString.append(txt="", font=upFont)
            elif index % random.randrange(1, 5) == 0:
                textString.append(txt="", font=itFont)
            index += 1
            word = i + " "
            textString.append(txt=word)

    # If you call for section to mix uprights and italics, and it's a VF that
    # contains an Italic axis.
    elif axesProduct and upit and "ital" in VFAxisInput:
        if VFAxisInput["ital"] != int(0):
            index = 0
            for i in textInput.split():
                if index % random.randrange(1, 5) == 0:
                    VFAxisInput["ital"] = 0.0
                    textString.append(txt="", fontVariations=VFAxisInput)
                elif index % random.randrange(1, 5) == 0:
                    VFAxisInput["ital"] = 1.0
                    textString.append(txt="", fontVariations=VFAxisInput)
                index += 1
                word = i + " "
                textString.append(txt=word)

    elif (
        rgbd
        and pairedStaticStyles[1]
        and f["name"].getBestSubFamilyName() == "Bold"
    ):
        rgFont = pairedStaticStyles[1][f["name"].getBestFamilyName()][0]
        bdFont = pairedStaticStyles[1][f["name"].getBestFamilyName()][1]
        index = 0
        for i in textInput.split():
            if index % random.randrange(1, 5) == 0:
                textString.append(txt="", font=rgFont)
            elif index % random.randrange(1, 5) == 0:
                textString.append(txt="", font=bdFont)
            index += 1
            word = i + " "
            textString.append(txt=word)

    elif axesProduct and rgbd and "wght" in VFAxisInput:
        if VFAxisInput["wght"] == int(700):
            index = 0
            for i in textInput.split():
                if index % random.randrange(1, 5) == 0:
                    VFAxisInput["wght"] = 400.0
                    textString.append(txt="", fontVariations=VFAxisInput)
                elif index % random.randrange(1, 5) == 0:
                    VFAxisInput["wght"] = 700.0
                    textString.append(txt="", fontVariations=VFAxisInput)
                index += 1
                word = i + " "
                textString.append(txt=word)

    # If you call for section to mix uprights and italics, and the font
    # is a VF, but it has no Italic axis, pass.
    elif (axesProduct and upit and "ital" not in VFAxisInput) or (
        axesProduct and rgbd and "wght" not in VFAxisInput
    ):
        pass

    # If you call for section to mix uprights and italics, and you have
    # statics, but you don't have any paired uprights and italics of the
    # same weight, pass.
    elif (
        not axesProduct
        and not pairedStaticStyles
        and upit is True
        or rgbd is True
    ):
        pass

    # For any section that doesn't mix uprights and italics.
    elif not upit or not rgbd:
        textString.append(txt=textInput)
    return textString


# Function to draw content
def drawContent(textToDraw, pageTitle, columnNumber):
    while textToDraw:
        db.newPage(pageDimensions)
        drawFooter(pageTitle)
        db.hyphenation(False)
        baselines = BaselineGrid.from_margins(
            (0, -marginVertical, 0, -marginVertical),
            textToDraw.fontLineHeight() / 2,
        )
        # baselines.draw(show_index=True)
        textToDraw = columnBaselineGridTextBox(
            textToDraw,
            (
                marginHorizontal,
                marginVertical,
                db.width() - marginHorizontal * 2,
                db.height() - marginVertical * 2,
            ),
            baselines,
            subdivisions=columnNumber,
            gutter=20,
            draw_grid=False,
        )


# Function to generate long text proofing strings either through wordsiv
# or by taking the premade string from Hoefler
def generateTextProofString(
    characterSet, para=2, casing=False, bigProof=True, forceWordsiv=False
):
    textProofString = ""
    if (
        uppercaseOnly
        and all([x in set(uniLu) for x in set(upperTemplate)])
        and forceWordsiv is False
    ):
        textProofString = pte.smallUpperText
    elif (
        lowercaseOnly
        and all([x in set(uniLl) for x in set(lowerTemplate)])
        and forceWordsiv is False
    ):
        textProofString = pte.smallLowerText
    elif (
        all([x in set(uniLu) for x in set(upperTemplate)])
        and all([x in set(uniLl) for x in set(lowerTemplate)])
        and forceWordsiv is False
    ):
        textProofString = pte.smallMixedText + " " + pte.smallUpperText
    elif (
        uppercaseOnly is False
        and lowercaseOnly is False
        or forceWordsiv is True
    ):
        caplc = ""
        for u in uniLuBase:
            capAndLower = ""
            capAndLower = u + uniLlBase
            wsv = WordSiv(vocab="en", seed=wordsivSeed)
            capitalisedList = wsv.words(
                glyphs=capAndLower,
                case="cap",
                n_words=2,
                min_wl=5,
                max_wl=14,
            )
            if not capitalisedList:
                continue
            else:
                capitalisedString = " ".join(
                    [str(elem) for elem in capitalisedList]
                )
            caplc += capitalisedString + " "

            lcList = wsv.words(
                glyphs=capAndLower,
                case="lc_force",
                contains=u.lower(),
                n_words=4,
                min_wl=5,
                max_wl=14,
            )
            if not lcList:
                continue
            else:
                lcString = " ".join([str(elem) for elem in lcList])
            caplc += lcString + " "

        wsvtext = wsv.text(
            glyphs=uniLu
            + uniLl
            + uniNd
            + uniPo
            + uniPc
            + uniPd
            + uniPi
            + uniPf
            + "(){}",
            numbers=0.1,
            rnd_punc=0.1,
            n_paras=para,
            para_sep=" ",
        )

        textProofString = caplc
        mixedTextProof = wsvtext
        textProofString += (
            "\n\n" + mixedTextProof + "\n\n" + mixedTextProof.upper()
        )
    elif uppercaseOnly:
        upperInitials = ""
        upperInitialsHelper = charset.lower()
        for u in uniLu:
            individualUpper = ""
            individualUpper = u + upperInitialsHelper
            upperwsv = WordSiv(glyphs=individualUpper, seed=wordsivSeed)
            upperList = upperwsv.words(
                vocab="en", case="cap", n_words=4, min_wl=5, max_wl=14
            )
            upperInitialsString = " ".join([str(elem) for elem in upperList])
            upperInitials += upperInitialsString.upper() + " "

        wsv = WordSiv(glyphs=charset)
        wsvtext = wsv.paras(
            vocab="en",
            n_paras=para,
            min_wl=1,
            max_wl=14,
            case="uc",
        )
        textProofString = upperInitials
        textProofString += "- " + " ".join([str(elem) for elem in wsvtext])
    elif lowercaseOnly:
        lowerInitials = ""
        for lower in uniLl:
            individualLower = ""
            individualLower = lower.upper() + charset
            lowerwsv = WordSiv(glyphs=individualLower, seed=wordsivSeed)
            lowerList = lowerwsv.words(
                vocab="en", case="cap", n_words=4, min_wl=5, max_wl=14
            )
            lowerInitialsString = " ".join([str(elem) for elem in lowerList])
            lowerInitials += lowerInitialsString.lower() + " "

        wsv = WordSiv(glyphs=charset)
        wsvtext = wsv.paras(
            vocab="en",
            n_paras=para,
            min_wl=1,
            max_wl=14,
        )
        textProofString = lowerInitials
        textProofString += " ".join([str(elem) for elem in wsvtext])
    return textProofString


#####################
# DRAW
# Let’s build this proof.

#####################
# charset proof


def charsetProof(characterSet):
    if not characterSet:
        pass
    else:
        sectionName = "Character set proof"
        if axesProduct:
            axisDict = {}
            for axisData in axesProduct:
                axisDict = dict(axisData)
                charsetString = stringMaker(
                    characterSet,
                    charsetFontSize,
                    "center",
                    24,
                    otfeatures,
                    axisDict,
                )
                drawContent(
                    charsetString, sectionName + " - " + str(axisData), 1
                )

        elif axesProduct == "":
            charsetString = stringMaker(
                characterSet, charsetFontSize, "center", 24, otfeatures
            )
            drawContent(
                charsetString,
                sectionName + " - " + db.font(indFont).split("-")[1],
                1,
            )


#####################
# spacing proof


# create empty formatted string that we will fill with spacing strings
def generateSpacingString(characterSet):
    spacingString = ""
    for char in characterSet:
        # determine control characters for each character
        if useFontContainsCharacters and not db.fontContainsCharacters(char):
            continue

        # ignoring linebreaks and space characters
        if char not in ["\n", " "]:
            control1 = "H"
            control2 = "O"
            if unicodedata.category(char) == "Ll":
                control1 = "n"
                control2 = "o"
            elif unicodedata.category(char) == "Nd":
                control1 = "0"
                control2 = "1"

            perCharSpacingString = f"{control1}{control1}{control1}{char}{control1}{control2}{control1}{char}{control2}{char}{control2}{control2}{control2}\n"
            spacingString += perCharSpacingString
    return spacingString


def spacingProof(characterSet):
    sectionName = "Spacing proof"
    if axesProduct:
        axisDict = {}
        for axisData in axesProduct:
            axisDict = dict(axisData)
            spacingStringInput = generateSpacingString(characterSet)
            spacingString = stringMaker(
                spacingStringInput,
                spacingFontSize,
                OTFeaInput=dict(liga=False, kern=False),
                VFAxisInput=axisDict,
            )
            drawContent(spacingString, sectionName + " - " + str(axisData), 2)

    elif axesProduct == "":
        spacingStringInput = generateSpacingString(characterSet)
        spacingString = stringMaker(
            spacingStringInput,
            spacingFontSize,
            OTFeaInput=dict(liga=False, kern=False),
        )
        drawContent(
            spacingString,
            sectionName + " - " + db.font(indFont).split("-")[1],
            2,
        )


#####################
# text proof


def textProof(
    characterSet,
    cols=2,
    para=3,
    casing=False,
    textSize=smallTextFontSize,
    sectionName="Text Proof",
    upit=False,
    rgbd=False,
    forceWordsiv=False,
    injectText=None,
    otFea=otfeatures,
    accents=0,
):
    sectionName = sectionName
    # If font is a VF
    textStringInput = ""
    if accents:
        for a in characterSet:
            accentList = []
            if a.lower() in pte.accentedDict:
                available = []
                for s in pte.accentedDict[a.lower()]:
                    if all(x in charset.lower() for x in s):
                        available.append(s)
                if len(available) < accents:
                    count = len(available)
                else:
                    count = accents
                textStringInput += " |" + a + "| "
                accentList = random.sample(available, k=count)
                for w in accentList:
                    if a.isupper():
                        textStringInput += w.replace("ß", "ẞ").upper() + " "
                    else:
                        textStringInput += w + " "
                if textSize == smallTextFontSize:
                    textStringInput += "\n"
    elif not injectText:
        textStringInput = generateTextProofString(
            characterSet, para, casing, forceWordsiv=forceWordsiv
        )
    elif injectText:
        for t in injectText:
            textStringInput += t + "\n"
    if axesProduct:
        axisDict = {}
        for axisData in axesProduct:
            axisDict = dict(axisData)
            textString = stringMaker(
                textStringInput,
                textSize,
                OTFeaInput=otFea,
                VFAxisInput=axisDict,
                upit=upit,
                rgbd=rgbd,
            )
            drawContent(
                textString,
                sectionName + " - " + str(axisData),
                columnNumber=cols,
            )

    # If font is static
    elif axesProduct == "":
        textString = stringMaker(
            textStringInput,
            textSize,
            OTFeaInput=otfeatures,
            upit=upit,
            rgbd=rgbd,
        )
        drawContent(
            textString,
            sectionName + " - " + db.font(indFont).split("-")[1],
            columnNumber=cols,
        )


#####################
# full set


def fullSetProof(axesProduct):
    sectionName = "Full set proof"
    if axesProduct:
        axisDict = {}
        for axisData in axesProduct:
            axisDict = dict(axisData)
            fullSet = db.FormattedString(
                txt=None,
                font=indFont,
                fallbackFont=myFallbackFont,
                fontSize=48,
                tracking=16,
                openTypeFeatures=None,
                fontVariations=axisDict,
            )
        for j in fullSet.listFontGlyphNames():
            if j == "space":
                pass
            else:
                fullSet.appendGlyph(j)
        drawContent(fullSet, sectionName + " - " + str(axisData), 1)

    elif axesProduct == "":
        fullSet = db.FormattedString(
            txt=None,
            font=indFont,
            fallbackFont=myFallbackFont,
            fontSize=48,
            tracking=16,
            openTypeFeatures=None,
        )
        for j in fullSet.listFontGlyphNames():
            if j == "space":
                pass
            else:
                fullSet.appendGlyph(j)
        drawContent(
            fullSet, sectionName + " - " + db.font(indFont).split("-")[1], 1
        )


#############
# Build the document

pairedStaticStyles = pairStaticStyles(fonts)

for indFont in fonts:
    charset = filteredCharset(indFont)
    axesProduct = variableFont(indFont)
    (
        uniLu,
        uniLl,
        uniPo,
        uniPc,
        uniPd,
        uniPs,
        uniPe,
        uniPi,
        uniPf,
        uniSm,
        uniSc,
        uniNd,
        uniNo,
        accented,
        uppercaseOnly,
        lowercaseOnly,
        uniLlBase,
        uniLuBase,
    ) = categorize(charset)

    charsetProof(uniLuBase)
    charsetProof(uniLlBase)
    numpunct = (
        uniNd
        + uniSm
        + uniSc
        + uniPo
        + uniPc
        + uniPd
        + uniPs
        + uniPe
        + uniPi
        + uniPf
    )
    num = uniNd + "\n" + uniSm + "\n" + uniSc + "\n" + uniNo
    punct = uniPo + uniPc + uniPd + uniPs + uniPe + uniPi + uniPf
    charsetProof(num)
    charsetProof(punct)
    charsetProof(accented)

    spacingProof(uniLuBase + uniLlBase + num + punct)

    textProof(
        charset,
        cols=1,
        para=2,
        textSize=largeTextFontSize,
        sectionName="Big size proof",
    )

    other = ""
    uc_lc = uniLu + uniLl
    for i in uc_lc:
        if (
            i not in accented
            and i not in lowerTemplate
            and i not in upperTemplate
        ):
            other += i

    accented_plus = accented + other

    textProof(
        accented_plus,
        cols=1,
        textSize=largeTextFontSize,
        sectionName="Big size accented proof",
        accents=3,
    )

    textProof(
        charset,
        cols=2,
        para=5,
        textSize=smallTextFontSize,
        sectionName="Small size proof",
    )

    textProof(
        charset,
        cols=2,
        para=5,
        textSize=smallTextFontSize,
        sectionName="Small size rg & bd proof",
        rgbd=True,
        forceWordsiv=True,
    )

    textProof(
        charset,
        cols=2,
        para=5,
        textSize=smallTextFontSize,
        sectionName="Small size proof mixed",
        forceWordsiv=True,
    )

    textProof(
        accented_plus,
        cols=2,
        textSize=smallTextFontSize,
        sectionName="Small size accented proof",
        accents=5,
    )

    textProof(
        charset,
        cols=2,
        para=5,
        textSize=smallTextFontSize,
        sectionName="Small size misc proof",
        injectText=(pte.bigRandomNumbers, pte.additionalSmallText),
    )


#############
# Saving the entire proof doc
db.saveImage(f"proofs/{nowformat}_{familyName}-proof.pdf")
print(datetime.datetime.now() - now)
