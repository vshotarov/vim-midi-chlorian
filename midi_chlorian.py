import vim
import jedi
import sys


# Get the extra python paths from vim's variables
extra_paths = []
if 'mc_extra_python_paths' in vim.vars.keys():
    extra_paths = vim.eval('g:mc_extra_python_paths')

python_path = extra_paths + sys.path


def createScript():
    '''Creates a jedi.Script object using the current buffer data.'''
    text = '\n'.join(vim.current.buffer)
    line, column = vim.current.window.cursor

    return jedi.Script(text, line, column,
                       path=vim.current.buffer.name, sys_path=python_path)


def complete():
    '''Finds available completions using Jedi and stores them in a vim
    variable - s:completions.'''
    script = createScript()

    completions = []
    for compl in script.completions():
        docstring = compl.docstring()

        # Check if we can grab a call signature
        signature = ' ' + compl.name
        if '(' in docstring:
            # Split until the first closing bracket
            signature = ' ' + docstring.split(')')[0].replace('\n', ' ') + ')'

        # Create a vim.Dictionary and add it to the list
        # We need a dictionary, so the popup menu can have more than just
        # the text being completet - the type, the signaturem etc.
        completions.append(vim.Dictionary({'word': compl.complete,
                                           'abbr': compl.name,
                                           'info': docstring,
                                           'kind': compl.type + signature}))

    return completions

def _choose_definition(definitions):
    '''Presents the user with an input list of definitions to choose one.'''
    str_definitions = []

    for i, d in enumerate(definitions):
        definition_options.append('%i: %s %s %s' % (i,
                                                    d.full_name,
                                                    d.type,
                                                    d.module_path))

    vim.command('let s:definition_choice=inputlist(%s)' % str_definitions)
    choice = int(vim.eval('s:definition_choice')) - 1

    return definitions[choice]

def goto_definition(assignment=False, recursive=True):
    '''Looks for definitions matching the word under the cursor and attempts
    to open them in a new buffer or go to the line in the current buffer.'''
    script = createScript()
    if assignment:
        definitions = script.goto_assignments()
    else:
        definitions = script.goto_definitions()

    if not definitions:
        vim.command('echo "No definitions found"')
        return

    definition = definitions[0]
    if len(definitions) > 1:
        definition = _choose_definition(definitions)

    if not definition.line:
        if not recursive:
            return
        # If the path and line attributes are None, that means that the definition
        # is in the current file and it's probably just a simple variable.
        # In that case, we need to use goto_assignments()
        return goto_definition(assignment=True, recursive=False)

    vim_goto_commands = '''
split %s
:%s
normal! zt''' % (definition.module_path, definition.line)

    if definition.module_path == vim.eval('expand("%:p")'):
        # If the definition is in the current file, just go to that
        # line instead of opening a new buffer
        vim_goto_commands = '''
:%s
normal! zz''' % definition.line

    for cmd in vim_goto_commands.split('\n')[1:]:
        vim.command(cmd)
