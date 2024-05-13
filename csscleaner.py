import sys
import os
import re


#Basic stack implementation to track the beginning and end of the useStyles hook
class BracketStack():

    def __init__(self, stack):
        self.stack = stack
        self.pushBracketCharacters = ['(', '{', '[']
        self.popBracketCharacters = [']', '}', ')']

    def operate(self, item):
        if item in self.pushBracketCharacters:
            self.stack.append(item)

        if item in self.popBracketCharacters:
            self.stack.pop()

    def getLength(self):
        return len(self.stack)


#Object for information about each file that's being parsed
class UseStylesFileInformation():
    def __init__(self, fileLocation):
        self.fileLocation = fileLocation
        self.hookStartLine = None
        self.hookEndLine = None
        self.keys = []
        self.unusedKeys = []


#Info for each key in the object being parsed
class UseStylesKeyInformation():
    def __init__(self, name, start, end):
        self.name = name
        self.start = start
        self.end = end


# This does a DFS through the directories, adding each tsx file path to a list to be iterated over later.
def getAllTsxFiles(srcPath):
    directories = [x[0] for x in os.walk(srcPath)]
    files = set()

    for directory in directories:
        subDirectories = os.listdir(directory)
        for subDirectory in subDirectories:
            if subDirectory.endswith(".tsx"):
                files.add(directory + '\\' + subDirectory)

    return files


#Read in file line by line looking for "useStyles"
#At that line, start reading in parhenteses and brackets
#When they match one another, stop reading in.

def getUseStylesHookLocation(file):
    stack = BracketStack([])

    with open(file, 'r') as f:
        lineCount = 0
        useStylesStart = None
        useStylesEnd = None

        # This is here to catch a case where the formatting of one of the lines isn't able to be read in.  In this rare case, better to just return None and keep on going
        try:
            for line in f.readlines():
                lineCount += 1
                if useStylesStart is None and line.find('useStyles') != -1:
                    useStylesStart = lineCount

                if useStylesStart is not None:
                    for char in line:
                        stack.operate(char)

                if useStylesEnd is None and useStylesStart is not None and stack.getLength() == 0:
                    useStylesEnd = lineCount

                if useStylesStart is not None and useStylesEnd is not None:
                    return useStylesStart, useStylesEnd
        except:
            return None


def getUseStylesKeys(fileLocation, lineStart, lineEnd):
    with open(fileLocation, 'r') as f:
        useStylesLines = f.readlines()[lineStart:lineEnd]
        keys = []

        lineNumber = lineStart

        for i in useStylesLines:
            lineNumber += 1

            # Checking for lines that are indented a single tab
            expression = re.compile("^ {4}([a-zA-Z]+)", flags=re.MULTILINE)
            result = expression.finditer(i.strip('\n'))

            # For each match, strip the whitespace, mark the line it was found on
            for match in result:
                key = str(match.group()).strip()
                keyLineStart = lineNumber
                keyLineEnd = None

                # If we have other keys already, mark the end of the last key to be the line before the start of this one
                if len(keys):
                    keys[-1].end = keyLineStart - 1

                keys.append(UseStylesKeyInformation(key, keyLineStart, keyLineEnd))

        # Marks the final key's ending line to be the line before the end of the hook
        if len(keys):
            keys[-1].end = lineEnd - 1

        f.close()
        return keys

def checkForUnusedKeys(fileLocation, keys):
    unusedKeys = []

    with open(fileLocation, 'r') as f:
        file = f.read()

        # Check to make sure there's a usage of "classes.keyName" in the file
        # This is purposely ambiguous in the case that it's not named classes
        for i in keys:
            count = file.count(str("." + i.name))

            if count == 0:
                unusedKeys.append(i)

    return unusedKeys


def removeUnusedKeys(fileInformation, unusedKeys):
    with open(fileInformation.fileLocation, 'r') as f:
        lines = f.readlines()
        f.close()

    with open(fileInformation.fileLocation, 'w') as w:
        for lineNumber in range(len(lines)):
            shouldWriteLine = True
            # If we're in the range of lines in the file where useStyles is
            if fileInformation.hookEndLine - 1 > lineNumber > fileInformation.hookStartLine - 1:
                # Then go through unused keys and see if it matches the section where we are
                for unusedKey in unusedKeys:
                    # Set shouldWriteLine to false if the unused key is in the section
                    # then break out since we're not going to write this line no matter what the rest of the keys are
                    if unusedKey.start - 1 <= lineNumber <= unusedKey.end - 1:
                        shouldWriteLine = False
                        break

            if shouldWriteLine:
                w.write(lines[lineNumber])
        w.close()


def main():
    try:
        # Gets the path passed in when this script is run
        srcPath = sys.argv[1]
        useStylesFileInformation = []

        # Gets all .tsx files and stubs out the objects
        for file in getAllTsxFiles(srcPath):
            useStylesFileInformation.append(UseStylesFileInformation(file))

        for i in useStylesFileInformation:
            hookLocation = getUseStylesHookLocation(i.fileLocation)
            if hookLocation is not None:
                i.hookStartLine, i.hookEndLine = hookLocation
                i.keys = getUseStylesKeys(i.fileLocation, i.hookStartLine, i.hookEndLine)

                if len(i.keys) > 0:
                    i.unusedKeys = checkForUnusedKeys(i.fileLocation, i.keys)

                if len(i.unusedKeys) > 0:
                    removeUnusedKeys(i, i.unusedKeys)

    except IndexError:
        print("No argument for src path was provided")


if __name__ == '__main__':
    main()
