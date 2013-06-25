'''
Created on Jun 19, 2013

@package: internationalization
@copyright: 2013 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Martin Saturka

The scanner used for extracting the localized text messages from dust.
'''

def extract_dust(fileobj, keywords, comment_tags, options):
    '''
    Parses the dust files for localizations. It expects fairly simple structure.

    :param fileobj: the seekable, file-like object the messages should be
                    extracted from
    :param keywords: a list of keywords (i.e. function names) that should be
                     recognized as translation functions
    :param comment_tags: not used
    :param options: a dictionary of additional options (optional)
    :return: an iterator over ``(lineno, funcname, message, comments)`` tuples
    :rtype: ``iterator``
    '''
    encoding = options.get('encoding', 'utf-8')

    def readline():
        line = fileobj.readline()
        if isinstance(line, bytes):
            try:
                line = line.decode(encoding)
            except UnicodeDecodeError:
                import pdb; pdb.set_trace()
        return line

    line_number = 0
    while True:
        line_number += 1
        line = readline()
        if not line: break

        for one_found in find_in_line(line, keywords):
            yield(line_number, one_found['name'], one_found['params'], [])

def find_in_line(line, name_keywords):
    '''
    looking for structures like __name__("",...);

    set the terminal point to the end of line
    find the "(", then:
    * check the "(" points in back-to-front way (i.e. taking the possible embedded ones):
    * on a single "("-point:
        * go backward, check if the preceding name is in keywords, if yes
        * go forward, look for the ");" strings; till the terminal point, if found
        * take them from the first to the last one;
            * check if the inner only contains "'-delimited \s,-separated strings inside
            * if yes, break the current ");" cycle; set the terminal point just before the preceding name
            * take the current taken data
    '''
    # initial setting
    found_functions = []
    other_word_chars = '_'
    line = str(line).strip()
    terminal_point = len(line)
    if not terminal_point:
        return found_functions
    # find the "(" parts
    last_tested_opening = terminal_point
    open_position = None
    while True:
        open_position = line.rfind('(', 0, last_tested_opening)
        if -1 == open_position:
            break
        last_tested_opening = open_position
        if -1 == open_position:
            break
        # find the preceding name
        check_name_position = open_position - 1
        function_name = ''
        while check_name_position > -1:
            if line[check_name_position] not in ' \t':
                break
            check_name_position -= 1
        while check_name_position > -1:
            if line[check_name_position].isalnum() or (line[check_name_position] in other_word_chars):
                function_name = line[check_name_position] + function_name
                check_name_position -= 1
                continue
            break
        # check the found preceding name
        if function_name not in name_keywords:
            continue
        # find the possible closing ");" ... try to get the first (correct) one
        inner_part = None
        last_tested_closing = open_position
        while True:
            check_close_position = line.find(')', last_tested_closing, terminal_point)
            last_tested_closing = check_close_position + 1
            if -1 == check_close_position:
                break
            check_semi_position = check_close_position + 1
            closing_correct = False
            while check_semi_position < terminal_point:
                if line[check_semi_position] == ' \t':
                    check_semi_position += 1
                    continue
                if line[check_semi_position] == ';':
                    closing_correct = True
                    break
                break
            if not closing_correct:
                continue
            # test the inner part to be comma(space)-separated quoted strings
            inner_part = test_inner_strings(line[(open_position+1):(check_close_position)])
            # if wrong inner part, test another (if remaining) closing
            if inner_part is None:
                continue
            # here we have checked all the name, start parenthesis, strings params, and closing to be correct
            found_functions.append({'name': function_name, 'params': inner_part})
            # set the ending for a possible next function
            terminal_point = open_position # could be even lower - by the function name, but this does not damage anything
            # close this cycling over the found (possible) endings
            break

    found_functions.reverse() # to output the found occurrences from left to right
    return found_functions

def test_inner_strings(line_part):
    '''
    Checking the line_part to be of structure "a param", 'another param', ...

    Returns the found params or None if wrong line_part
    '''

    PARAMS_START = 1
    STRING_INNER = 2
    STRING_AFTER = 4
    STRING_BETWEEN = 8

    quots = '\'"'
    params = []
    wrong = None

    line_part = line_part.strip()
    if not line_part:
        return params

    check_position = 0
    state = PARAMS_START
    taken_string = ''
    string_opened = ''
    line_part_len = len(line_part)
    while True:
        if check_position == line_part_len:
            if state not in [PARAMS_START, STRING_AFTER]:
                return wrong
            return params
        check_char = line_part[check_position]
        check_position += 1

        if PARAMS_START == state:
            if check_char not in quots:
                return wrong
            string_opened = check_char
            state = STRING_INNER
            continue

        if STRING_INNER == state:
            if check_char == string_opened:
                state = STRING_AFTER
                params.append(taken_string)
                taken_string = ''
                continue
            taken_string += check_char
            continue

        if STRING_AFTER == state:
            if check_char in ' \t':
                continue
            if check_char == ',':
                state = STRING_BETWEEN
                continue
            return wrong

        if STRING_BETWEEN == state:
            if check_char in ' \t':
                continue
            if check_char in quots:
                string_opened = check_char
                state = STRING_INNER
                continue
            return wrong

def test():
    from io import StringIO

    test_dust = '''
    testing
    <a>_("a", 'b');
    <tag>N_(); //"none _(''_('example'); _("
    <a>_('c', "def");
    '''

    for one in extract_dust(StringIO(test_dust), ['_', 'N_'], [], {}):
        print(one)
