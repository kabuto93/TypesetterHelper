# -*- coding: utf-8 -*-
"""
A utility to format .txt files for use in typesetter. Running from command line, it accepts and {input file} argument
and an {output file} argument
"""
import string
import sys
import codecs
import os
import configparser
import collections
import re

config = configparser.ConfigParser()
configfile = 'program.ini'
Settings = collections.namedtuple("Settings", "input, output, decorators")
INP = None
OUT = None
SPLITCHAR = None
DECORATIONS = None
CHAPTERLABEL = None
FEATURES = None


def main(argv):
    filelines = []
    print_header("                   Typesetterer Formatter")

    # Parse config or build one if needed
    print_header("                       Parsing Config",)
    if os.path.exists(configfile):
        print("Parsing config file")
        config.read(configfile)
        seriesconfig = config["BASIC"]["perseriesconfig"]
        print(seriesconfig)
        if seriesconfig == "":
            parse_config()
        else:
            config.remove_section("FEATURES")
            config.remove_section("BASIC")
            config.remove_section("ADVANCED")
            config.read(seriesconfig)
            parse_config()
    else:
        with open(configfile, 'w') as fout:
            print("Building config file...")
            build_config()
            config.write(fout)

    # Get the input and output files
    print_header("                    Obtaining file names")
    if not FEATURES["inputisouput"]:
        files = get_files(argv)
    else:
        files = INP, OUT
    print("Input file is {}.".format(files[0]))
    print("Output file is {}.\n".format(files[1]))
    with codecs.open(files[0], 'r', encoding='utf-8') as fout:
        for line in fout.readlines():
            filelines.append(line)

    # Preprocess files to remove or replace characters
    if FEATURES["preprocess"]:
        print_header("                        Preprocessing")
        print("{} lines to process.\n".format(len(filelines)))
        filelines = preprocess(filelines)

    # Remove user defined decorations
    if FEATURES["decorations"]:
        print_header("                   Removing Decorations")
        filelines, decoratorcount = remove_decorations(filelines)
        print("{} decorations have been removed.\n".format(decoratorcount))

    # Remove panel labels
    if FEATURES["panels"]:
        print_header("                    Removing Panel Labels")
        filelines, panelcount = remove_panels(filelines)
        print("{} panel labels have been removed.\n".format(panelcount))

    # Remove non-Latin style characters
    if FEATURES["nonlatin"]:
        print_header("      Filtering lines with non-Latin style characters")
        filelines, removed, remlines = test_file(filelines)
        print("{} lines have been removed.\n".format(removed))

    # Remove speaker labels
    if FEATURES["speakers"]:
        print_header("                 Removing speaker labels")
        filelines, speakercount = remove_speaker(filelines)
        print("{} speaker labels have been removed.\n".format(speakercount))

    # Truncate tildes
    if FEATURES["tildes"]:
        print_header("                    Truncating tildes")
        filelines, tildecount = truncate_tildes(filelines)
        print("{} lines have had tildes truncated.\n".format(tildecount))

    # Truncate ellipses
    if FEATURES["ellipses"]:
        print_header("                   Truncating ellipses")
        filelines, ellipsiscount = truncate_ellipses(filelines)
        print("{} lines have had ellipses truncated.\n".format(ellipsiscount))

    # Remove blank lines
    if FEATURES["blanklines"]:
        print_header("                    Remove blank lines")
        filelines, blankcount = remove_blank_lines(filelines)
        print("{} blank lines have been removed.\n".format(blankcount))

    # Write to output file
    print_header("                 Writing output to file")
    outcount = write_output(files[1], filelines)
    print("{} lines have been written to {}.\n".format(outcount, files[1]))
    print_header("                         Complete")


def build_config():
    """
    Builds config file if none exists
    """
    config['BASIC'] = {'input': '',
                       'output': '',
                       'chapterlabel': 'chapter',
                       'perseriesconfig': ''}
    config['ADVANCED'] = {'splitchar': ',',
                          'regex': ''}
    config['FEATURES'] = {'preprocess': 'True',
                          'decorations': 'True',
                          'panels': 'True',
                          'nonlatin': 'True',
                          'speakers': 'True',
                          'tildes': 'True',
                          'ellipses': 'True',
                          'blanklines': 'True',
                          'inputisoutput': 'False'}
    with open(configfile, 'w') as fout:
        config.write(fout)


def parse_config():
    """
    Sets global variables from config
    """
    global INP, OUT, SPLITCHAR, DECORATIONS, CHAPTERLABEL, FEATURES
    INP = config['BASIC']['input']
    OUT = config['BASIC']['output']
    CHAPTERLABEL = config['BASIC']['chapterlabel']
    SPLITCHAR = config['ADVANCED']['splitchar']
    DECORATIONS = config['ADVANCED']['regex'].split(SPLITCHAR)
    FEATURES = {"preprocess": config['FEATURES'].getboolean('preprocess'),
                "decorations": config['FEATURES'].getboolean('decorations'),
                "panels": config['FEATURES'].getboolean('panels'),
                "nonlatin": config['FEATURES'].getboolean('nonlatin'),
                "speakers": config['FEATURES'].getboolean('speakers'),
                "tildes": config['FEATURES'].getboolean('tildes'),
                "ellipses": config['FEATURES'].getboolean('ellipses'),
                "blanklines": config['FEATURES'].getboolean('blanklines'),
                "inputisouput": config['FEATURES'].getboolean('inputisoutput')}
    if FEATURES["inputisouput"]:
        OUT = INP


def print_header(header):
    """
    Print various headers based on index
    :param header: String containing header text
    :return: Incremented header index
    """
    line = "==========================================================="
    print('{0}\n{1}\n{0}'.format(line, header))


def is_english(s):
    """
    Determine if a string contains non-latin style characters in it
    :param s: String to test for non-latin style characters
    :return: True if there are only latin style characters
    """
    punctuation = set(string.punctuation)
    num = set(string.digits)
    alpha = set(string.ascii_letters)
    diacritics = {'Á', 'á', 'Ǽ', 'ǽ', 'Ć', 'ć', 'É', 'é', 'Ǵ', 'ǵ', 'Í', 'í', 'Ḱ', 'ḱ', 'Ĺ', 'ĺ', 'Ḿ', 'ḿ', 'Ń', 'ń',
                  'Ó',
                  'ó', 'Ǿ', 'ǿ', 'Ṕ', 'ṕ', 'Ŕ', 'ŕ', 'Ś', 'ś', 'Ú', 'ú', 'Ẃ', 'ẃ', 'Ý', 'ý', 'Ź', 'ź', 'Ṥ', 'ṥ', 'Ă',
                  'ă',
                  'Ĕ', 'ĕ', 'Ğ', 'ğ', 'Ĭ', 'ĭ', 'Ŏ', 'ŏ', 'Ŭ', 'ŭ', 'Ắ', 'ắ', 'Ặ', 'ặ', 'Ằ', 'ằ', 'Ẳ', 'ẳ', 'Ẵ', 'ẵ',
                  'Ḫ',
                  'ḫ', 'Ǎ', 'ǎ', 'Č', 'č', 'Ď', 'ď', 'Ě', 'ě', 'Ǧ', 'ǧ', 'Ȟ', 'ȟ', 'Ǐ', 'ǐ', 'ǰ', 'Ǩ', 'ǩ', 'Ľ', 'ľ',
                  'Ň',
                  'ň', 'Ǒ', 'ǒ', 'Ř', 'ř', 'Š', 'š', 'Ť', 'ť', 'Ǔ', 'ǔ', 'Ž', 'ž', 'Ǯ', 'ǯ', 'Ṧ', 'ṧ', 'Ç', 'ç', 'Ḑ',
                  'ḑ',
                  'Ȩ', 'ȩ', 'Ģ', 'ģ', 'Ḩ', 'ḩ', 'Ķ', 'ķ', 'Ļ', 'ļ', 'Ņ', 'ņ', 'Ŗ', 'ŗ', 'Ş', 'ş', 'Ţ', 'ţ', 'Ḉ', 'ḉ',
                  'Ḝ',
                  'ḝ', 'Â', 'â', 'Ĉ', 'ĉ', 'Ê', 'ê', 'Ĝ', 'ĝ', 'Ĥ', 'ĥ', 'Î', 'î', 'Ĵ', 'ĵ', 'Ô', 'ô', 'Ŝ', 'ŝ', 'Û',
                  'û',
                  'Ŵ', 'ŵ', 'Ŷ', 'ŷ', 'Ẑ', 'ẑ', 'Ấ', 'ấ', 'Ế', 'ế', 'Ố', 'ố', 'Ậ', 'ậ', 'Ệ', 'ệ', 'Ộ', 'ộ', 'Ầ', 'ầ',
                  'Ề',
                  'ề', 'Ồ', 'ồ', 'Ẩ', 'ẩ', 'Ể', 'ể', 'Ổ', 'ổ', 'Ẫ', 'ẫ', 'Ễ', 'ễ', 'Ỗ', 'ỗ', 'Ḓ', 'ḓ', 'Ḙ', 'ḙ', 'Ḽ',
                  'ḽ',
                  'Ṋ', 'ṋ', 'Ṱ', 'ṱ', 'Ṷ', 'ṷ', 'Ș', 'ș', 'Ț', 'ț', 'Ä', 'ä', 'Ë', 'ë', 'Ḧ', 'ḧ', 'Ï', 'ï', 'Ö', 'ö',
                  'ẗ',
                  'Ü', 'ü', 'Ẅ', 'ẅ', 'Ẍ', 'ẍ', 'Ÿ', 'ÿ', 'Ḯ', 'ḯ', 'Ǘ', 'ǘ', 'Ǚ', 'ǚ', 'Ǜ', 'ǜ', 'Ǟ', 'ǟ', 'Ȫ', 'ȫ',
                  'Ǖ',
                  'ǖ', 'Ṳ', 'ṳ', 'Ȧ', 'ȧ', 'Ḃ', 'ḃ', 'Ċ', 'ċ', 'Ḋ', 'ḋ', 'Ė', 'ė', 'Ḟ', 'ḟ', 'Ġ', 'ġ', 'Ḣ', 'ḣ', 'İ',
                  'Ṁ',
                  'ṁ', 'Ṅ', 'ṅ', 'Ȯ', 'ȯ', 'Ṗ', 'ṗ', 'Ṙ', 'ṙ', 'Ṡ', 'ẛ', 'ṡ', 'Ṫ', 'ṫ', 'Ẇ', 'ẇ', 'Ẋ', 'ẋ', 'Ẏ', 'ẏ',
                  'Ż',
                  'ż', 'Ǡ', 'ǡ', 'Ȱ', 'ȱ', 'Ạ', 'ạ', 'Ḅ', 'ḅ', 'Ḍ', 'ḍ', 'Ẹ', 'ẹ', 'Ḥ', 'ḥ', 'Ị', 'ị', 'Ḳ', 'ḳ', 'Ḷ',
                  'ḷ', 'Ṃ', 'ṃ', 'Ṇ', 'ṇ', 'Ọ', 'ọ', 'Ṛ', 'ṛ', 'Ṣ', 'ṣ', 'Ṭ', 'ṭ', 'Ụ', 'ụ', 'Ṿ', 'ṿ', 'Ẉ', 'ẉ', 'Ỵ',
                  'ỵ',
                  'Ẓ', 'ẓ', 'Ṩ', 'ṩ', 'Ḹ', 'ḹ', 'Ṝ', 'ṝ', 'Ő', 'ő', 'Ű', 'ű', 'Ȁ', 'ȁ', 'Ȅ', 'ȅ', 'Ȉ', 'ȉ', 'Ȍ', 'ȍ',
                  'Ȑ',
                  'ȑ', 'Ȕ', 'ȕ', 'À', 'à', 'È', 'è', 'Ì', 'ì', 'Ǹ', 'ǹ', 'Ò', 'ò', 'Ù', 'ù', 'Ẁ', 'ẁ', 'Ỳ', 'ỳ', 'Ả',
                  'ả',
                  'Ẻ', 'ẻ', 'Ỉ', 'ỉ', 'Ỏ', 'ỏ', 'Ủ', 'ủ', 'Ỷ', 'ỷ', 'Ơ', 'ơ', 'Ư', 'ư', 'Ớ', 'ớ', 'Ứ', 'ứ', 'Ợ', 'ợ',
                  'Ự',
                  'ự', 'Ờ', 'ờ', 'Ừ', 'ừ', 'Ở', 'ở', 'Ử', 'ử', 'Ỡ', 'ỡ', 'Ữ', 'ữ', 'Ȃ', 'ȃ', 'Ȇ', 'ȇ', 'Ȋ', 'ȋ', 'Ȏ',
                  'ȏ',
                  'Ȓ', 'ȓ', 'Ȗ', 'ȗ', 'Ā', 'ā', 'Ǣ', 'ǣ', 'Ē', 'ē', 'Ḡ', 'ḡ', 'Ī', 'ī', 'Ō', 'ō', 'Ū', 'ū', 'Ȳ', 'ȳ',
                  'Ḗ',
                  'ḗ', 'Ṓ', 'ṓ', 'Ṻ', 'ṻ', 'Ḕ', 'ḕ', 'Ṑ', 'ṑ', 'Ḇ', 'ḇ', 'Ḏ', 'ḏ', 'ẖ', 'Ḵ', 'ḵ', 'Ḻ', 'ḻ', 'Ṉ', 'ṉ',
                  'Ṟ',
                  'ṟ', 'Ṯ', 'ṯ', 'Ẕ', 'ẕ', 'Ą', 'ą', 'Ę', 'ę', 'Į', 'į', 'Ǫ', 'ǫ', 'Ų', 'ų', 'Ǭ', 'ǭ', 'Å', 'å', 'Ů',
                  'ů',
                  'ẘ', 'ẙ', 'Ǻ', 'ǻ', 'Ḁ', 'ḁ', 'Ã', 'ã', 'Ẽ', 'ẽ', 'Ĩ', 'ĩ', 'Ñ', 'ñ', 'Õ', 'õ', 'Ũ', 'ũ', 'Ṽ', 'ṽ',
                  'Ỹ',
                  'ỹ', 'Ṍ', 'ṍ', 'Ṹ', 'ṹ', 'Ṏ', 'ṏ', 'Ȭ', 'ȭ', 'Ḛ', 'ḛ', 'Ḭ', 'ḭ', 'Ṵ', 'ṵ', ' ', '’', ':', '​', '—', '”', '”', '‘'}
    slist = set(s)
    slist = list(((((slist - punctuation) - diacritics) - alpha) - num))
    s = ''.join(slist)
    if not s or (s == '\ufeff'):
        r = True
    else:
        r = False
    return r


def get_files(argv):
    """
    Get the input and output files. Automatically if arguments are given, asking for user input if they are not.
    :param argv: List of arguments [0] = inp, [1] = out
    :return INP: String for input file name
    :return OUT: String for output file name
    """
    global INP, OUT
    if not INP and not OUT:
        inp = ''
        out = ''
        if len(argv) > 0 and os.path.exists(argv[0]) and os.path.exists(os.path.dirname(argv[1])) \
                and os.path.exists(os.path.dirname(argv[1])):
            inp = argv[0]
            out = argv[1]
            return [inp, out]
        elif len(argv) > 0:
            print("Some paths are not recognized")
        if len(argv) == 1 and os.path.exists(argv[0]):
            inp = argv[0]
            while not os.path.exists(os.path.dirname(out)):
                out = inp[:-4] + input("Enter extension to input filename: ") + ".txt"
            return [inp, out]
        elif len(argv) > 0 and not os.path.exists(argv[0]):
            print("Input path is not recognized")
        while not os.path.exists(inp):
            inp = input("Enter input filename: ")
        while not os.path.exists(os.path.dirname(out)):
            out = input("Enter output filename: ")
            if '.' not in out:
                out = inp[:-4] + out + ".txt"
            print(out)
        return [inp, out]
    else:
        if not INP:
            exit("No output file in config, but input file found")
        elif not OUT:
            exit("No input file in config, but output file found")
        else:
            if '.' not in OUT:
                OUT = INP[:-4] + OUT + ".txt"
                return INP, OUT


def test_file(filelines):
    """
    Test each line of a file for non-Latin style characters, creating a list of the lines with only Latin style
    characters
    :param filelines: String of the input file
    :return lines: List of lines containing only Latin-style characters
    :return count: Integer of how many lines contained chapter
    :return notlines: Debug variable to view what was removed
    """
    lines = []
    notlines = []
    count = 0
    for line in filelines:
        line = line.strip()
        if is_english(line):
            lines.append(line)
        else:
            notlines.append(line)
            count += 1
    return lines, count, notlines


def write_output(file, lines):
    """
    Create and fill output file
    :param file: String of output file name
    :param lines: List of lines to write to output
    :param notlines: List of lines that have been removed, only used for debugging
    :return count: Integer of how many lines were written to output
    """
    count = 0
    with codecs.open(file, 'w', encoding='utf-8') as fout:
        for line in lines:
            fout.write('{}\r\n'.format(line))
            count += 1
    # with codecs.open("debug.txt", 'w', encoding='utf-8') as fout:
    #     for line in notlines:
    #         fout.write('{}\r\n'.format(line))
    return count


def preprocess(lines):
    """
    Preprocess the script for future steps to run smoothly
    :param lines: List of lines with only Latin-style characters
    :return: List of preprocessed lines
    """
    linesout = []
    badchars = {'...': ['…'],
                "'": ['’', '‘', '『', '』', '﹃', '﹄', '〈', '〉', ],
                '"': ['“', '”', '「', '」', '﹁', '﹂', '《', '》', ]
                }
    for line in lines:
        temp = line
        for key, value in badchars.items():
            for item in value:
                temp = temp.replace(item, key)
        linesout.append(temp)
    return linesout


def remove_panels(lines):
    """
    Remove the panel labels from the file
    :param lines: List of lines with only Latin-style characters
    :return outlines: List of lines containing only Latin-style characters
    :return count: Integer of how many lines contained panel labels
    """
    outlines = []
    count = 0
    for line in lines:
        if line.lower().startswith('panel'):
            count += 1
        else:
            outlines.append(line)
    return outlines, count


def remove_speaker(lines):
    """
    Remove the speaker labels from the file
    :param lines: List of lines with only Latin-style characters
    :return outlines: List of lines containing only Latin-style characters
    :return speakercount: Integer of how many lines contained chapter labels
    """
    global CHAPTERLABEL
    print('Chapter label is: {}'.format(CHAPTERLABEL))
    outlines = []
    speakercount = 0
    for line in lines:
        charcount = 0
        if ":" in line:
            for char in line:
                charcount += 1
                if char == ":":
                    curline = line[:charcount].lower()
                    try:
                        cursplit = curline.split(":")
                        if curline[-4:].strip().lower() == "sfx:" or curline[-5:].strip().lower() == "note:" \
                                or curline[:len(CHAPTERLABEL)].strip().lower() == CHAPTERLABEL:
                            outlines.append(line)
                        elif len(cursplit) > 1:
                            split = cursplit[0]
                            if "note" in split or "/n" in split or "\\n" in split:
                                outlines.append(line)
                        else:
                            if curline.count(" ") > 1:
                                print(line)
                                if input("Is this speaker text? [y/n] ").lower() == "y":
                                    speakercount += 1
                                    outlines.append(line[charcount:].strip())
                                else:
                                    outlines.append(line)
                            else:
                                speakercount += 1
                                outlines.append(line[charcount:].strip())
                    except:
                        pass
        else:
            outlines.append(line)
    return outlines, speakercount


def remove_decorations(lines):
    """
    Remove decorations from the file using regex
    :param lines: List of lines with only Latin-style characters
    :return outlines: List of lines containing only Latin-style characters
    :return dcount: Integer of how many lines contained decorations
    """
    outlines = []
    dcount = 0
    for line in lines:
        templine = line
        for d in DECORATIONS:
            templine = re.sub(d, "", templine)
        outlines.append(templine)
        if line != templine:
            dcount += 1
    return outlines, dcount


def truncate_tildes(lines):
    outlines = []
    count = 0
    for line in lines:
        temp = re.sub("~+", "~", line)
        outlines.append(temp)
        if temp != line:
            count += 1
    return outlines, count


def truncate_ellipses(lines):
    outlines = []
    count = 0
    for line in lines:
        temp = re.sub("(\.\.\.)+", "...", line)
        outlines.append(temp)
        if temp != line:
            count += 1
    return outlines, count


def remove_blank_lines(lines):
    outlines = []
    count = 0
    for line in lines:
        if not line.strip() == '':
            outlines.append(line)
        else:
            count += 1
    return outlines, count


if __name__ == '__main__':
    main(sys.argv[1:])
