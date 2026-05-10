from .file_tools import file_tools
from .web_tools import web_tools
from .system_tools import system_tools
from .code_tools import code_tools
from .linter_tools import lint_code, fix_lint_errors

# Wrap linter functions into a list to match the pattern of other tool sets
linter_tools = [lint_code, fix_lint_errors]

all_tools = file_tools + web_tools + system_tools + code_tools + linter_tools
