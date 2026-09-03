from __future__ import annotations

import ast
import builtins
import json
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
    def visit_Name(self, node):
        if isinstance(node.ctx, ast.Load):
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
class FunctionGlobalVisitor(ast.NodeVisitor):
    def __init__(self):
        self.issues=[]
    def visit_FunctionDef(self,node):
        params=set(a.arg for a in node.args.args+node.args.kwonlyargs)
        if node.args.vararg: params.add(node.args.vararg.arg)
        if node.args.kwarg: params.add(node.args.kwarg.arg)
        assigned=set(); imported=set(); globals_decl=set(); nonlocals=set()
        class LocalCollector(ast.NodeVisitor):
            def visit_Name(self,s,n):
                if isinstance(n.ctx,(ast.Store,ast.Del)): assigned.add(n.id)
            def visit_Import(self,s,n):
                for a in n.names: imported.add(a.asname or a.name.split('.')[0])
            def visit_ImportFrom(self,s,n):
                for a in n.names: imported.add(a.asname or a.name)
            def visit_Global(self,s,n): globals_decl.update(n.names)
            def visit_Nonlocal(self,s,n): nonlocals.update(n.names)
            def visit_FunctionDef(self,s,n): assigned.add(n.name)
            visit_AsyncFunctionDef=visit_FunctionDef
            def visit_ClassDef(self,s,n): assigned.add(n.name)
            def visit_Lambda(self,s,n): pass
        lc=LocalCollector()
        for s in node.body: lc.visit(s)
        local=params|assigned|imported
        loads=set()
        class LoadCollector(ast.NodeVisitor):
            def visit_Name(self,s,n):
                if isinstance(n.ctx,ast.Load): loads.add(n.id)
            def visit_FunctionDef(self,s,n): pass
            visit_AsyncFunctionDef=visit_FunctionDef
            def visit_ClassDef(self,s,n): pass
            def visit_Lambda(self,s,n): pass
        lcv=LoadCollector()
        for s in node.body: lcv.visit(s)
        unresolved=sorted(x for x in loads if x not in nonlocals and (x not in local or x in globals_decl) and x not in all_available)
        if unresolved:
            self.issues.append((node.lineno,node.name,unresolved))
        for s in node.body:
            if isinstance(s,(ast.FunctionDef,ast.AsyncFunctionDef)):
                self.visit(s)
    visit_AsyncFunctionDef=visit_FunctionDef

fg=FunctionGlobalVisitor(); fg.visit(cur_tree)
print('FUNCTION_UNRESOLVED_GLOBAL_COUNT', len(fg.issues))
for line,name,names in fg.issues:
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

# Strong failures: any parent module definition lost, or any top-level use-before-def.
if missing_from_base or use_before_def:
    raise SystemExit(2)
