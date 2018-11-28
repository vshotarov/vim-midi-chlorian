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
        # If the path and line attributes are None, that means that the 
        # definition is in the current file and it's probably just a simple 
        # variable. In that case, we need to use goto_assignments()
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


def call_signature():
    '''Attempts to find a call signature for the word underneath the cursor and
    prints it using echo.'''
    param_str_len = 6  # len('param_')

    try:
        # Unfortunately this operation errors out sometimes, with an error
        # saying - Please provide a position that exists on this node
        # The error is coming from parso which jedi uses.
        # So, we have to handle the exception.
        signature = createScript().call_signatures()
    except ValueError as e:
        return

    vim.command('echo ""')  # Cleans the line
    # If we don't want to do that on every text change event, we can move this
    # inside the if statement. It's here, so it gets rid of the signature when
    # we are no longer inside of the function call.
    # The presumption being, this is used inside of a TextChangedI event
    if signature:
        signature = signature[0]
        params = ', '.join(
            [p.description[param_str_len:].replace('\n', ' ')
             for p in signature.params])

        vim.command('echon "%s"' %
                    (signature.name + '(' + params.replace('\"', '\\"') + ')'))


def show_docstring():
    '''Attempts to find the docstring for a definition and disply it in a
    preview window.'''
    # TODO: Syntax highlighting would be cool
    definitions = createScript().goto_definitions()

    if not definitions:
        return

    definition = definitions[0]
    if len(definitions) > 1:
        definition = _choose_definition(definitions)

    vim.command('let s:docstring=[]')
    vim.bindeval('s:docstring').extend([definition.docstring()])

    vim_docstring_cmds = '''
split Doc
setlocal noswapfile
setlocal buftype=nofile
setlocal modifiable
silent $put=s:docstring[0]
silent normal! ggdd
setlocal nomodifiable
setlocal nomodified
noremap <buffer> q :q<CR>
highlight Midi_Chlorian_Docstring ctermfg=blue
match Midi_Chlorian_Docstring /./
'''

    for cmd in vim_docstring_cmds.split('\n')[1:]:
        vim.command(cmd)
