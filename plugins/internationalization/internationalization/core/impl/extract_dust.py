'''
Created on Jun 19, 2013

@package: internationalization
@copyright: 2013 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Martin Saturka

The scanner used for extracting the localized text messages from dust.
'''

STATE_NAME = 1
STATE_VALUES = 2
STATE_END = 4

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

    from tokenize import generate_tokens, COMMENT, NAME, OP, STRING

    def readline():
        line = fileobj.readline()
        if isinstance(line, bytes):
            try:
                line = line.decode(encoding)
            except UnicodeDecodeError:
                import pdb; pdb.set_trace()
        return line

    curr_name = None
    curr_values = []
    curr_comments = []
    curr_state = None

    tokens = generate_tokens(readline)
    for tok, value, (lineno, _), _, _ in tokens:
        if tok == NAME and value in keywords:
            curr_name = value
            curr_values = []
            curr_comments = []
            curr_state = STATE_NAME
        elif curr_state == STATE_NAME and tok == OP and value == '(':
            curr_state = STATE_VALUES
        elif curr_state == STATE_VALUES and tok == COMMENT:
            curr_comments.append(value)
        elif curr_state == STATE_VALUES and tok == STRING:
            curr_values.append(value)
        elif curr_state == STATE_VALUES and tok == OP and value == ',':
            pass
        elif curr_state == STATE_VALUES and tok == OP and value == ')':
            curr_state = STATE_END
        elif curr_state == STATE_END and tok == OP and value == ';':
            if curr_values:
                yield(lineno, curr_name, curr_values, curr_comments)
            curr_state = None
        else:
            curr_state = None
