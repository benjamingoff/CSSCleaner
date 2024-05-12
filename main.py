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

    def operateByLine(self, line):
        for char in self.pushBracketCharacters:
            count = line.count(char)
            if count != 0:
                self.stack.append()
    def getLength(self):
        return len(self.stack)


class UseStylesFileInformation():
    def __init__(self, fileLocation):
        self.fileLocation = fileLocation
        self.hookStartLine = None
        self.hookEndLine = None
        self.keys = []
        self.unusedKeys = []


class UseStylesKeyInformation():
    def __init__(self, name, start, end):
        self.name = name
        self.start = start
        self.end = end


# This does a DFS through the directories, adding each tsx file path to a list to be iterated over later.
# Use a set instead of a list actually for constant time lookups
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


def getUseStylesKeys(fileLocation, lineStart, lineEnd):
    with open(fileLocation, 'r') as f:
        hookLines = f.readlines()[lineStart:lineEnd]
        keys = []

        lineNumber = lineStart

        for i in hookLines:
            lineNumber += 1

            expression = re.compile("^ {4}([a-zA-Z]+)", flags=re.MULTILINE)
            result = expression.finditer(i.strip('\n'))

            for match in result:
                key = str(match.group()).strip()
                keyLineStart = lineNumber
                keyLineEnd = None

                if len(keys):
                    keys[-1].end = keyLineStart - 1

                keys.append(UseStylesKeyInformation(key, keyLineStart, keyLineEnd))

        if len(keys):
            keys[-1].end = lineEnd - 1

        f.close()

        return keys

def checkForUnusedKeys(fileLocation, keys):
    unusedKeys = []

    with open(fileLocation, 'r') as f:
        file = f.read()

        for i in keys:
            count = file.count(str("classes." + i.name))

            if count == 0:
                unusedKeys.append(i)

    return unusedKeys


def removeUnusedKeys(fileInformation, unusedKeys):
    with open(fileInformation.fileLocation, 'r') as f:
        with open(fileInformation.fileLocation[-10:] + 'test.tsx', 'w') as w:
            lines = f.readlines()
            for lineNumber in range(len(lines)):
                if fileInformation.hookEndLine - 1 > lineNumber >= fileInformation.hookStartLine - 1:
                    for unusedKey in unusedKeys:
                        if unusedKey.start - 1 <= lineNumber <= unusedKey.end - 1:
                            print(lineNumber)
                            break
                        else:
                            w.write(lines[lineNumber])
                else:
                    w.write(lines[lineNumber])
            w.close()
        f.close()




def main():
    #try:
        srcPath = sys.argv[1]
        useStylesFileInformation = []

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

        #for i in useStylesFileInformation:
        #    print(i.unusedKeys)

        #for i in keys:
        #   check = checkForUnusedKeys(i[0], i[1])
        #    if len(check[1]):
        #        filesWithUnusedKeys.append(check)



    #except:
    #    print("No argument for src path was provided")


if __name__ == '__main__':
    main()
