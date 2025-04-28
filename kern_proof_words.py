from drawBotGrid import BaselineGrid, columnBaselineGridTextBox
import datetime
import itertools
import drawBot as db
from wordsiv import WordSiv, FilterError, Vocab

# When you add more fonts, it stacks the strings for each
# weight to enable easy comparisons.
fonts = ("fonts/WorkSans[wght].ttf",)
fontnumber = len(fonts)
familyname = "WorkSans"

# fontFileName = os.path.basename(fonts[0])
# familyname = os.path.splitext(fontFileName)[0].split("-")[0]
now = datetime.datetime.now()
nowformat = now.strftime("%Y-%m-%d_%H%M")

# These are the strings fo characters that will be mashed together
# to generate the kerning strings. You do have to take care with
# escaping certain characters.
ucchars = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
lcchars = "abcdefghijklmnopqrstuvwxyz"

# Template characters to use as context for strings
uc1 = "H"
uc2 = "O"
lc1 = "n"
lc2 = "o"


# This function helps with making the lines of strings
# have a specific amount of *words* per line.
def wrap_by_word(s, n):
    """returns a string where \\n is inserted between every n words"""
    a = s.split()
    ret = ""
    for i in range(0, len(a), n):
        ret += " ".join(a[i : i + n]) + "\n"
    return ret


# Make a footer per page. This comes from DJR's simple proof script.
def drawFooter(section):
    with db.savedState():
        folio = db.FormattedString(
            str(db.pageCount()),
            font="Courier",
            fontSize=9,
            lineHeight=9,
            align="right",
        )
        today = datetime.date.today()

        # assemble footer text
        footerText = f"{today} | {familyname} | {section}"

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
        db.textBox(footer, (40, 25, db.width() - 25 * 2, 9))
        db.textBox(folio, (40, 25, db.width() - 50 * 2, 9))


MY_GLYPHS = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz "
ll_vocab = Vocab(
    lang="ll", data_file="merged_languages_no_accents.tsv", bicameral=True
)
wsv = WordSiv(glyphs=MY_GLYPHS)
wsv.add_vocab("all_lang", ll_vocab)

kernlist = []
text = itertools.combinations_with_replacement(lcchars, 2)
for pair in text:
    try:
        makestr = f"{lc1}{lc1}{''.join(pair)}{lc1}{lc1} "
        kernlist.append(
            makestr
            + " | "
            + " ".join(
                wsv.words(
                    vocab="all_lang",
                    n_words=5,
                    case="lc_force",
                    inner="".join(pair),
                    min_wl=6,
                    max_wl=12,
                    raise_errors=True,
                )
            )
        )
    except FilterError as e:
        makestr = f"{lc1}{lc1}{''.join(pair)}{lc1}{lc1} "
        kernlist.append(makestr)
    try:
        makestr = f"{lc1}{lc1}{''.join(pair)[::-1]}{lc1}{lc1} "
        kernlist.append(
            makestr
            + " | "
            + " ".join(
                wsv.words(
                    vocab="all_lang",
                    n_words=5,
                    case="lc_force",
                    inner="".join(pair)[::-1],
                    min_wl=6,
                    max_wl=12,
                    raise_errors=True,
                )
            )
        )
    except FilterError as e:
        makestr = f"{lc1}{lc1}{''.join(pair)[::-1]}{lc1}{lc1} "
        kernlist.append(makestr)
# print(kernlist)

text = "\n".join(kernlist)
while text:
    db.newPage("A4")
    drawFooter("WS Kerning")
    db.fill(0)
    db.fontSize(15)
    db.lineHeight(20 * fontnumber)

    db.openTypeFeatures(calt=True, liga=True, kern=True)
    db.hyphenation(False)
    baselines = BaselineGrid.from_margins((0, -40, 0, -40), 5)
    # Uncomment the line below to see the baseline grid.
    # baselines.draw()

    # The code below is what draw the text to the page. Because
    # of how the while text loop works, I need to make a copy of
    # the text for each font I want to use, otherwise the text
    # gets used up by the first font, and the next font would use
    # the next line. I also use sa vertical shift to shift the text
    # boxes for each font after the first one.
    vshift = 0
    textprerun = text
    runs = 0
    for fi, f in enumerate(fonts, start=1):
        db.font(f)
        text = columnBaselineGridTextBox(
            text,
            (40, 40 - vshift, db.width() - 80, db.height() - 80),
            baselines,
            subdivisions=1,
            gutter=20,
            draw_grid=False,
        )
        vshift = vshift + 20
        runs += 1
        if runs == fontnumber:
            continue
        else:
            text = textprerun


db.saveImage(f"proofs/{nowformat}_{familyname}-kerning-example.pdf")
print(datetime.datetime.now() - now)
