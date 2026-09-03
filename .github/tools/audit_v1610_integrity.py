from __future__ import annotations

import ast
import builtins
import json
import symtable
from pathlib import Path

BASE = Path('code/releases/015_260903_v1.6.9.ipynb')
CUR = Path('code/releases/016_260904_v1.6.10.ipynb')


def load_cell(path: Path, cell_id: str) -> str:
    nb = json.loads(path.read_text(encoding='utf-8'))
    cell = next(c for c in nb['cells'] if c.get('id') == cell_id)
    return ''.join(cell.get('source', []))

base_program = load_cell(BASE, 'v169-program')
cur_settings = load_cell(CUR, 'v1610-settings')
cur_program = load_cell(CUR, 'v1610-program')

compile(base_program, 'v169-program', 'exec')
compile(cur_settings, 'v1610-settings', 'exec')
compile(cur_program, 'v1610-program', 'exec')
print('COMPILE_OK')

base_tree = ast.parse(base_program)
cur_tree = ast.parse(cur_program)
settings_tree = ast.parse(cur_settings)


def target_names(node):
    out = set()
    if isinstance(node, ast.Name):
        out.add(node.id)
    elif isinstance(node, (ast.Tuple, ast.List)):
        for e in node.elts:
            out |= target_names(e)
    return out


def stmt_definitions(stmt):
    names = set()
    if isinstance(stmt, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
        names.add(stmt.name)
    elif isinstance(stmt, ast.Assign):
        for t in stmt.targets:
            names |= target_names(t)
    elif isinstance(stmt, ast.AnnAssign):
        names |= target_names(stmt.target)
    elif isinstance(stmt, ast.AugAssign):
        names |= target_names(stmt.target)
    elif isinstance(stmt, (ast.Import, ast.ImportFrom)):
        for a in stmt.names:
            if a.asname:
                names.add(a.asname)
            elif isinstance(stmt, ast.Import):
                names.add(a.name.split('.')[0])
            else:
                names.add(a.name)
    return names


def module_definitions(tree):
    names = set()
    kinds = {}
    for stmt in tree.body:
        for n in stmt_definitions(stmt):
            names.add(n)
            kinds.setdefault(n, type(stmt).__name__)
    return names, kinds

base_defs, base_kinds = module_definitions(base_tree)
cur_defs, cur_kinds = module_definitions(cur_tree)
settings_defs, _ = module_definitions(settings_tree)
missing_from_base = sorted(base_defs - cur_defs - settings_defs)
print('BASE_DEFINED_COUNT', len(base_defs))
print('CURRENT_DEFINED_COUNT', len(cur_defs))
print('MISSING_BASE_DEFINITIONS_COUNT', len(missing_from_base))
for n in missing_from_base:
    print('MISSING_BASE_DEFINITION', base_kinds.get(n), n)

class ImmediateLoadVisitor(ast.NodeVisitor):
    def __init__(self):
        self.loads = set()
        self.comp_locals = [set()]
    def visit_Name(self, node):
        if isinstance(node.ctx, ast.Load) and node.id not in self.comp_locals[-1]:
            self.loads.add(node.id)
    def visit_FunctionDef(self, node):
        for d in node.decorator_list:
            self.visit(d)
        for d in node.args.defaults:
            self.visit(d)
        for d in node.args.kw_defaults:
            if d is not None:
                self.visit(d)
        if node.returns:
            self.visit(node.returns)
        for a in list(node.args.args) + list(node.args.kwonlyargs):
            if a.annotation:
                self.visit(a.annotation)
    visit_AsyncFunctionDef = visit_FunctionDef
    def visit_ClassDef(self, node):
        for b in node.bases:
            self.visit(b)
        for k in node.keywords:
            self.visit(k.value)
        for d in node.decorator_list:
            self.visit(d)
    def visit_Lambda(self, node):
        pass
    def _visit_comp(self, node, value_nodes):
        local = set(self.comp_locals[-1])
        for gen in node.generators:
            self.visit(gen.iter)
            local |= target_names(gen.target)
            self.comp_locals.append(local)
            for cond in gen.ifs:
                self.visit(cond)
            self.comp_locals.pop()
        self.comp_locals.append(local)
        for v in value_nodes:
            self.visit(v)
        self.comp_locals.pop()
    def visit_DictComp(self, node):
        self._visit_comp(node, [node.key, node.value])
    def visit_ListComp(self, node):
        self._visit_comp(node, [node.elt])
    visit_SetComp = visit_ListComp
    def visit_GeneratorExp(self, node):
        self._visit_comp(node, [node.elt])

predefined = set(dir(builtins)) | {'__name__', '__file__'} | settings_defs
sequential = set(predefined)
use_before_def = []
for stmt in cur_tree.body:
    v = ImmediateLoadVisitor()
    v.visit(stmt)
    missing = sorted(x for x in v.loads if x not in sequential)
    if missing:
        use_before_def.append((getattr(stmt, 'lineno', None), type(stmt).__name__, missing))
    sequential |= stmt_definitions(stmt)
print('TOP_LEVEL_USE_BEFORE_DEF_COUNT', len(use_before_def))
for line, typ, names in use_before_def:
    print('TOP_LEVEL_USE_BEFORE_DEF', line, typ, ','.join(names))

all_available = cur_defs | settings_defs | set(dir(builtins)) | {'__name__', '__file__'}
root_st = symtable.symtable(cur_program, 'v1610-program', 'exec')
function_global_issues = []

def walk_table(tab, prefix=''):
    for child in tab.get_children():
        qname = f'{prefix}.{child.get_name()}' if prefix else child.get_name()
        missing = []
        for sym in child.get_symbols():
            if sym.is_referenced() and sym.is_global() and sym.get_name() not in all_available:
                missing.append(sym.get_name())
        if missing:
            function_global_issues.append((child.get_lineno(), qname, sorted(set(missing))))
        walk_table(child, qname)
walk_table(root_st)
print('FUNCTION_UNRESOLVED_GLOBAL_COUNT', len(function_global_issues))
for line,name,names in function_global_issues:
    print('FUNCTION_UNRESOLVED_GLOBAL', line, name, ','.join(names))

main_marker='if __name__ == "__main__":\n    run_scanner()'
print('MAIN_CALL_COUNT', cur_program.count(main_marker))
print('MAIN_IS_LAST', cur_program.rstrip().endswith(main_marker))
for marker in [
    'compute_broker_fill_delta', 'reconcile_managed_quantities',
    'get_broker_pending_orders', 'get_broker_positions',
    'request_entry_cancel_for_exit', 'pending_auto_sell_qty',
    'auto_managed_qty', 'external_qty', 'save_live_state', 'os.replace',
    'BASE', 'PRE_HISTORY', 'FIRST_75_PASS', 'LATER_PASS', 'CONFIRM',
    'LIVE_FILTER_SHADOW', 'SHADOW_SCORE_70_74', 'WIDE_HIGH_GAP_SHADOW',
    'PRE_FAIL_PULLBACK_SHADOW', 'ENTRY_PATH', 'POST_EXIT'
]:
    print('MARKER', marker, marker in cur_program)

if missing_from_base or use_before_def or function_global_issues:
    raise SystemExit(2)
