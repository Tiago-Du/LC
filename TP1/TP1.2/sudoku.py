# /// script
# requires-python = ">=3.12"
# dependencies = [
#     "marimo>=0.24.2",
#     "ortools",
# ]
# ///

import marimo

__generated_with = "0.25.1"
app = marimo.App(width="medium")


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ##TP1.2 - SUDOKU
    * Miguel de Matos Poço Cabral Gonçalves (A110879)
    * Tiago Du (A112235)
    """)
    return


@app.cell
def _():
    import marimo as mo
    import random
    from ortools.sat.python import cp_model

    return cp_model, mo, random


@app.cell
def _(mo):
    mo.md(r"""
    # Sudoku Genérico como CSP

    ## Problema

    Um Sudoku $n^2 \times n^2$ é uma grelha em que cada linha, cada coluna e
    cada bloco $n \times n$ contém todos os valores de $1$ a $n^2$ sem
    repetições. Algumas células vêm preenchidas à partida, as pistas, e o
    objetivo é completar a grelha ou concluir que não existe solução.

    ## Abordagem

    **Modelação como CSP.** Cada célula é uma variável inteira com domínio
    $[1, n^2]$. Todas as regras do Sudoku têm a mesma forma: um conjunto de
    células tem de ter valores todos diferentes. Só muda quais as células do
    conjunto. Por isso existe uma única abstração, o `Box`, e o modelo não
    distingue linhas, colunas, blocos ou pistas.

    **Estrutura de dados.** O `Box` guarda um dicionário
    `{(linha, coluna): valor ou None}`. O dicionário é suficiente porque os
    grupos são pequenos e esparsos, e permite construir qualquer forma de
    grupo célula a célula.

    **Técnica de resolução.** Usa-se o CP-SAT do OR-Tools. Tem propagação
    forte para a restrição `AllDifferent`, distingue soluções de
    insatisfazibilidade e resolve a grelha $9 \times 9$ em milissegundos.

    **Pistas aleatórias.** Como o modelo impõe valores diferentes dentro de
    cada grupo, o grupo de pistas também os exige. Por isso os valores das
    pistas são sorteados sem repetição, o que obriga a $k \le n^2$. Sem esta
    escolha, o grupo seria insatisfazível por construção.

    **Puzzle sem solução.** Mesmo com valores distintos, duas pistas podem
    violar uma linha, coluna ou bloco. Nesse caso geram-se novas pistas até
    obter um puzzle solúvel, porque é barato e devolve sempre uma grelha
    válida. Se as tentativas se esgotarem, é devolvido `None`.

    **Apresentação.** A grelha resolvida é mostrada numa tabela, com as
    pistas a negrito.

    **Validação.** Verifica-se que cada linha, coluna e bloco contém
    exatamente $1 \ldots n^2$, que as pistas mantêm o valor e que `add`
    rejeita coordenadas e valores inválidos. O fluxo corre para $n=2$ e
    $n=3$.

    ## Correspondência com o enunciado

    | Requisito | Nome neste notebook |
    |---|---|
    | R1 | `Box`, `add`, `to_matrix` |
    | R2 | `Cube` |
    | R3 | `Path` |
    | R4 | `pistas_aleatorias` |
    | R5 | `ModeloSudoku`, `add_groups`, `solve` |
    | R6 | `sudoku_completo` |
    """)
    return


@app.class_definition
class Box:
    def __init__(self, n, cells=None):
        self.n = n
        self.cells = {}
        for (i, j), val in (cells or {}).items():
            self.add(i, j, val)

    def add(self, i, j, val=None):
        side = self.n**2
        if not (0 <= i < side and 0 <= j < side):
            raise ValueError(f"Célula {i}, {j} fora da grelha {side}x{side}")
        if val is not None and not (1 <= val <= side):
            raise ValueError(f"Valor {val} fora do intervalo [1, {side}]")
        self.cells[(i, j)] = val

    def to_matrix(self):
        side = self.n**2
        m = [[0] * side for _ in range(side)]
        for (i, j), val in self.cells.items():
            if val is not None:
                m[i][j] = val
        return m


@app.cell
def _():
    class Cube(Box):
        def __init__(self, n, i, j):
            if not (0 <= i < n and 0 <= j < n):
                raise ValueError(f"Índices de bloco {i}, {j} fora de [0, {n}[")
            super().__init__(n)
            for a in range(n):
                for b in range(n):
                    self.add(i * n + a, j * n + b)

    class Path(Box):
        def __init__(self, n, inicio, fim):
            super().__init__(n)
            i0, j0 = inicio
            i1, j1 = fim
            if i0 != i1 and j0 != j1:
                raise ValueError("O troço tem de ser horizontal ou vertical")
            di = (i1 > i0) - (i1 < i0)
            dj = (j1 > j0) - (j1 < j0)
            for k in range(max(abs(i1 - i0), abs(j1 - j0)) + 1):
                self.add(i0 + k * di, j0 + k * dj)

    return Cube, Path


@app.cell
def _(random):
    def pistas_aleatorias(n, k=None, rng=None):
        rng = rng or random
        side = n**2
        k = n if k is None else k
        if k > side:
            raise ValueError("k não pode exceder n^2")
        todas = [(i, j) for i in range(side) for j in range(side)]
        celulas = rng.sample(todas, k)
        valores = rng.sample(range(1, side + 1), k)
        grupo = Box(n)
        for (i, j), v in zip(celulas, valores):
            grupo.add(i, j, v)
        return grupo

    return (pistas_aleatorias,)


@app.cell
def _(cp_model):
    class ModeloSudoku:
        def __init__(self, n):
            self.n = n
            side = n**2
            self.model = cp_model.CpModel()
            self.x = [
                [self.model.NewIntVar(1, side, f"x_{i}_{j}") for j in range(side)]
                for i in range(side)
            ]

        def add_groups(self, *groups):
            for g in groups:
                if g.n != self.n:
                    raise ValueError("Grupo com n diferente do modelo")
                self.model.AddAllDifferent([self.x[i][j] for i, j in g.cells])
                for (i, j), val in g.cells.items():
                    if val is not None:
                        self.model.Add(self.x[i][j] == val)

        def solve(self):
            solver = cp_model.CpSolver()
            status = solver.Solve(self.model)
            if status in (cp_model.OPTIMAL, cp_model.FEASIBLE):
                side = self.n**2
                return [
                    [solver.Value(self.x[i][j]) for j in range(side)]
                    for i in range(side)
                ]
            return None

    return (ModeloSudoku,)


@app.cell
def _(Cube, ModeloSudoku, Path, pistas_aleatorias, random):
    def estrutura(n):
        s = n**2
        linhas = [Path(n, (i, 0), (i, s - 1)) for i in range(s)]
        colunas = [Path(n, (0, j), (s - 1, j)) for j in range(s)]
        blocos = [Cube(n, i, j) for i in range(n) for j in range(n)]
        return linhas + colunas + blocos

    def sudoku_completo(n, k=None, seed=None, max_tentativas=200):
        rng = random.Random(seed)
        for _ in range(max_tentativas):
            pistas = pistas_aleatorias(n, k, rng)
            modelo = ModeloSudoku(n)
            modelo.add_groups(*estrutura(n), pistas)
            grelha = modelo.solve()
            if grelha is not None:
                return grelha, pistas
        return None, None

    return (sudoku_completo,)


@app.cell
def _():
    def validar(n, grelha, pistas=None):
        s = n**2
        alvo = set(range(1, s + 1))
        linhas = [set(r) for r in grelha]
        colunas = [{grelha[i][j] for i in range(s)} for j in range(s)]
        blocos = [
            {grelha[bi * n + a][bj * n + b] for a in range(n) for b in range(n)}
            for bi in range(n)
            for bj in range(n)
        ]
        ok = all(g == alvo for g in linhas + colunas + blocos)
        if pistas is not None:
            ok = ok and all(
                grelha[i][j] == v for (i, j), v in pistas.cells.items()
            )
        return ok

    def testa_rejeicoes(n):
        s = n**2
        casos = [(-1, 0, None), (0, s, None), (s, 0, None), (0, 0, 0), (0, 0, s + 1)]
        for i, j, v in casos:
            try:
                Box(n).add(i, j, v)
            except ValueError:
                continue
            return False
        return True

    return testa_rejeicoes, validar


@app.cell
def _(mo, sudoku_completo, testa_rejeicoes, validar):
    _linhas = []
    for _n in (2, 3):
        _g, _p = sudoku_completo(_n, seed=42)
        _ok = _g is not None and validar(_n, _g, _p)
        _linhas.append(
            f"- n={_n}: solução válida **{_ok}**, rejeições de `add` **{testa_rejeicoes(_n)}**"
        )
    mo.md("## Testes\n\n" + "\n".join(_linhas))
    return


@app.cell
def _(mo, sudoku_completo, validar):
    _n = 3
    _g, _p = sudoku_completo(_n, seed=42)
    _s = _n**2
    _tabela = [
        {
            str(j + 1): f"**{_g[i][j]}**" if (i, j) in _p.cells else str(_g[i][j])
            for j in range(_s)
        }
        for i in range(_s)
    ]
    mo.vstack(
        [
            mo.md(f"## Solução {_s}x{_s}\n\nPistas a negrito. Válida: **{validar(_n, _g, _p)}**"),
            mo.ui.table(_tabela, selection=None, page_size=_s),
        ]
    )
    return


if __name__ == "__main__":
    app.run()