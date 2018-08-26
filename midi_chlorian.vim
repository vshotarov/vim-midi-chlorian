" Store the path of this file, so it can be
let s:path=expand('<sfile>:p:h')

function! Midi_Chlorian_Init()
	" Adds the current path to the python path, so the
	" file midi_chlorian.py can be accessed and then
	" sets some settings
	"
	" Bear in mind this function is called in the end of this file.
python << EOF
import sys
import vim

sys.path.append(vim.eval('s:path'))
import midi_chlorian
EOF
" Settings
autocmd FileType python setlocal omnifunc=Midi_Chlorian_Complete
endfunction

function! Midi_Chlorian_Assign_Completions()
	" Calls the python completion from midi_chlorian.py and
	" assigns it to the completions local variable to be used
	" in the omnifunc completion function
	python << EOF
vim.command("let s:completions=[]")
vim.bindeval("s:completions").extend(midi_chlorian.complete())
EOF
endfunction

function! Midi_Chlorian_Complete(findstart, base)
	" The completion function used by omnifunc
	" The actual completion code is taken directly from :h complete-items
	if a:findstart
		" Return the current cursor column
		return col('.') - 1
	else
		" Call completion from python. The result is stored in
		" s:completions
		python vim.command('let s:completions=[]')
		python vim.bindeval('s:completions').extend(midi_chlorian.complete())
		return s:completions
	endif
endfunction

function! Midi_Chlorian_Goto_Definition()
	python midi_chlorian.goto_definition()
endfunction

" Call the init function
call Midi_Chlorian_Init()
