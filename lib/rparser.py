import logging
import re
from collections import defaultdict

FS = '    '  # four spaces not a tab

class Parser():
    
    def __init__(self) -> None:
        """ initialiser of the parser object
        """
        
        # logger
        self.logger = logging.getLogger('parser')

        # these are the characters that are part of the script.
        self.characters = set()
        self.character_id = ''
        self.character_name = ''
        
        # a dictionary of lists, the key is the file name, the value is a list
        # of lines. This will be held in ram because even if its a coupe of GB
        # thats still plenty and i should be able to do some nice things later
        self.output = defaultdict(lambda: [])
        
        # errors that are found in parsing
        self.errors = []
        
        # patterns
        # matches the character variable, optional given name, and any spoken
        # line
        # [character:name] text -> character, name, text
        self.oldSpoken_pattern = re.compile(r'^\[(.+?)(?::(.+?))?\]\s*(.+)\s*$')
        # haven't really played with this one yet, just gets the things in the
        # brackets
        self.command_pattern = re.compile(r'^\[(.+)\]\s*$')
        # gets the title pattern, >> title
        self.title_pattern = re.compile(r'^\>\>\s*(.+)')
        self.comment_pattern = re.compile(r'^#\s*(.+)')
        self.name_pattern = re.compile(r'(^[A-Z][A-Z].+?)(?::(.+?))?\s*$')

    def parse_line(self, file: str, line: str) -> None:
        """ accepts the next line, parses it and stores it internally in ram
        :param file: file from where the line came. really just has to be a
            unique identifier
        :type file: str
        :param line: line to parse
        :type line: str
        """
        # calls the matcher and hands it to the specific type of parser
        if (m := self.oldSpoken_pattern.match(line)):
            l = self._parse_oldSpoken(m)
        # elif (m := self.spoken_pattern.match(line)):
        #     l = self._parse_spoken(m)
        elif (m := self.command_pattern.match(line)):
            l = self._parse_commands(m)
        elif (m := self.title_pattern.match(line)):
            l = self._parse_title(m)
        elif (m := self.comment_pattern.match(line)):
            l = self._parse_comment(line)
        elif (m := self.name_pattern.match(line)):
            self._parse_name(m)
            l = ''  # no output for this line
        elif (line == '\n'):
            l = FS + line # empty line
        else:
            l = self._parse_spoken(line)
            
        # add the line
        self.output[file].append(l)
            
    
    def get_file(self, file) -> tuple:
        """ retrieves the parsed file

        :param file: file to retrieve
        :type file: str
        :return: lines
        :rtype: tuple
        """
        
        return tuple(self.output[file])
    
    def get_init(self) -> tuple:
        """ retrives the parsed init file. This should only be called once all
            of the files have been parsed

        :return: the init file lines
        :rtype: tuple
        """
        
        # lines to be parsed
        lines = []

        for character in self.characters:
            # sets the default character name to the variable name
            chr_str = f'define {character} = Character(\'{character}\')\n'
            lines.append(chr_str)
        
        # adding the game start
        lines.append('\n# script starts bellow\n')
        lines.append('label start:\n')
        lines.append(f'{FS}# change the bellow line to the correct destination\n')
        lines.append(f'{FS}jump [destination]\n')
        
        return tuple(lines)
    
    def _parse_title(self, matcher: re.Match) -> str:
        """ internal function to parse a file of type title

        :param matcher: matcher from the line
        :type matcher: re.Match
        :return: parsed line
        :rtype: str
        """
        
        # get the label from the matcher
        label = matcher[1]
        
        # swap spaces with underscores
        label = label.replace(' ', '_')
        
        # produce the code and return
        output = f'label {label}:\n'  # label xyz:
        return output

    def _parse_oldSpoken(self, matcher: re.Match) -> str:
        """ parses the line and returns the line,
            also stores the speaker to the characters list.
        :param matcher: matcher from the line
        :type matcher: re.Match
        :return: parsed line
        :rtype: str
        """
        
        # get the data from the matcher
        char = matcher[1]
        name = matcher[2]
        line = matcher[3]
    
        
        # cleaning the output and parsing the line
        line = line.replace('"', '\"')  # fix the quotes for renpy
        if char == 'Narration':  # special case, just have the line
            output = f'{FS}\"{line}\"\n'
        else:
            output = f'{FS}{char} \"{line}\"\n'
            
            # adding the character to the init
            # this only happens if its not a narrator
            self.characters.add(char)
        
        # if a name is given add a special name line
        if name:
            name_line = f'{FS}$ {char}.name = \'{name}\'\n'
            output = name_line + output
            
        return output
    
    def _parse_name(self, matcher: re.Match) -> str:
        """ parses the line and returns the line,
            also stores the speaker to the characters list.
        :param matcher: matcher from the line
        :type matcher: re.Match
        :return: parsed line
        :rtype: str
        """
        print(matcher.groups())
        # get the data from the matcher
        char = matcher[1]
        name = matcher[2]

        self.character_id = char.lower().replace(' ', '_').strip()
        self.character_name = name.strip() if name else ''

    def _parse_spoken(self, line: str) -> str:
        """ parses the line and returns the line,
            also stores the speaker to the characters list.
        :param matcher: matcher from the line
        :type matcher: re.Match
        :return: parsed line
        :rtype: str
        """
        
        # get the data from the matcher
        # cleaning the output and parsing the line
        l = line
        l = l.replace('"', '\\"')

        l = l.strip()
        output = f'\"{l}\"'
        if self.character_id != '':
            name = self.character_id
            self.characters.add(name)
            self.character_id = ''  # reset the name after use
            output = name + ' ' + output
        
        output = FS + output
    
        if self.character_name != '':
            name_line = f'{FS}$ {name}.name = \'{self.character_name}\'\n'
            output = name_line + output
            self.character_name = ''  # reset the name after use
        
        return output + '\n'
    
    def _parse_commands(self, matcher: re.Match) -> str:
        """ reads a command line and parses it somehow, todo

        :param matcher: matcher object of the contents of the command
        :type matcher: re.Match
        :return: parsed line
        :rtype: str
        """
        
        # don't need to figure this out just yet
        # self.logger.warning(f'command not implemented: {matcher[1]}')
        # return f'# {matcher[1]}\n'
        return f'{FS}{matcher[1]}\n'
    
    def _parse_comment(self, line: str) -> str:
        # this one accepts a line cause its not doing a regex
        """ parse the line as a comment, accepts comments that start with a #
            as well just a regular line. Non '#' comments raise a warning

        :param line: line to parse
        :type line: str
        :return: parsed line
        :rtype: str
        """
        if line.startswith('#'):  # true comment
            return f'{FS}{line.strip()}\n'  # force the whitespace to be 1 tab
        
        # not a true comment
        self.logger.warning(f'Unable to parse as a line {line}\nparsing as comment')
        return f'# {line}\n'  # don't indent so it is clear
    
    