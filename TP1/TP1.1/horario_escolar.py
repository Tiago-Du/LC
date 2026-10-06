import marimo

__generated_with = "0.25.1"
app = marimo.App(width="medium")


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ##TP1.1 - HORÁRIO ESCOLAR
    * Miguel de Matos Poço Cabral Gonçalves (A110879)
    * Tiago Du (A112235)
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Importação e Visualização de Dados em Tabelas

    Nesta primeira fase, importamos os dados da pasta "dados", disponível no DropBox e criamos tabelas para facilitar a leitura dos dados.

    * Bibliotecas: Utilização do Pandas para uma leitura eficiente e estruturada dos ficheiros CSV, respeitando a R8 e facilitando a extração posterior de listas e dicionários. O Marimo serve para desenhar a parte visual do projeto no ecrã

    * Atalho para a pasta: criamos a variável pasta logo no início para indicar onde estão os ficheiros. Assim, para cumprir a regra da construção incremental (R9) basta mudar de "dados/" para "dados_v2/" e o programa carrega a informação nova sem termos de mexer no resto do código.

    * Leitura dos dados: juntámos o mo.ui.tabs, que cria separadores, com o .head(), que mostra apenas as primeiras linhas da tabela. isto permite confirmar que os ficheiros foram bem lidos, sem inundar o ecrã com milhares de linhas de texto desnecessárias.
    """)
    return


@app.cell
def _():
    import marimo as mo
    import pandas as pd

    pasta = "dados/"

    df_turmas = pd.read_csv(f"{pasta}turmas.csv")
    df_disciplinas = pd.read_csv(f"{pasta}disciplinas.csv")
    df_salas = pd.read_csv(f"{pasta}salas.csv")
    df_excecoes = pd.read_csv(f"{pasta}disponibilidade_excecoes.csv")

    mo.ui.tabs({
        "Turmas": mo.as_html(df_turmas.head()),
        "Disciplinas": mo.as_html(df_disciplinas.head()),
        "Salas": mo.as_html(df_salas.head()),
        "Exceções": mo.as_html(df_excecoes.head())
    })
    return df_disciplinas, df_excecoes, df_salas, df_turmas, mo, pd


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ##Iniciar o solver
    """)
    return


@app.cell
def _():
    from ortools.sat.python import cp_model
    modelo = cp_model.CpModel()
    return cp_model, modelo


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Criação das variáveis de decisão
    """)
    return


@app.cell
def _(df_disciplinas, df_turmas, modelo):
    dias = ['Seg', 'Ter', 'Qua', 'Qui', 'Sex']
    tempos = [1, 2, 3, 4, 5]

    turmas_lista = df_turmas['turma'].tolist()
    disciplinas_lista = df_disciplinas['disciplina'].tolist()
    professores_lista = df_disciplinas['professor'].unique().tolist()

    #Criar as variáveis de decisão
    x = {}

    for _t in turmas_lista:
        for _d in disciplinas_lista:
            for _dia in dias:
                for _tempo in tempos:

                    # Dá um nome único para identificação interna
                    _nome_variavel = f"aula_{_t}_{_d}_{_dia}_{_tempo}"

                    # Cria a variável booleana e guarda-a no dicionário x
                    x[(_t, _d, _dia, _tempo)] = modelo.NewBoolVar(_nome_variavel)
    return dias, disciplinas_lista, professores_lista, tempos, turmas_lista, x


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ##R1

    * Num dado dia e período, uma turma não pode ter mais do que uma disciplina a decorrer. Utilizamos `AddAtMostOne` agrupando as variáveis de todas as disciplinas para aquele momento exato.
    """)
    return


@app.cell
def _(
    df_disciplinas,
    dias,
    disciplinas_lista,
    modelo,
    tempos,
    turmas_lista,
    x,
):
    carga_sem = df_disciplinas.set_index('disciplina')['carga_semanal'].to_dict()

    #Uma turma não pode ter duas aulas em simultâneo
    for _t in turmas_lista:
        for _dia in dias:
            for _tempo in tempos:
                _aulas_nesse_tempo = [x[(_t, _d, _dia, _tempo)] for _d in disciplinas_lista]
                modelo.AddAtMostOne(_aulas_nesse_tempo)
    return (carga_sem,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## R2
    * Garantimos que a soma total de aulas de uma disciplina, ao longo dos 5 dias e 5 períodos, é estritamente igual ao valor estipulado no DataFrame original (carga horária semanal).
    """)
    return


@app.cell
def _(carga_sem, dias, disciplinas_lista, modelo, tempos, turmas_lista, x):
    for _t in turmas_lista:
        for _d in disciplinas_lista:
            _aulas_da_semana = [x[(_t, _d, _dia, _tempo)] for _dia in dias for _tempo in tempos]
            _carga_esperada = int(carga_sem[_d])
            modelo.Add(sum(_aulas_da_semana) == _carga_esperada)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## R3

    * Evita a sobrecarga dos alunos limitando a repetição de disciplinas teóricas (que não precisam de blocos duplos). A regra obriga a que a turma tenha, no máximo, apenas uma aula dessa disciplina por dia.
    """)
    return


@app.cell
def _(
    df_disciplinas,
    dias,
    disciplinas_lista,
    modelo,
    tempos,
    turmas_lista,
    x,
):
    duplo_per = df_disciplinas.set_index('disciplina')['duplo_periodo'].to_dict()

    for _t in turmas_lista:
        for _d in disciplinas_lista:
            for _dia in dias:

                # Só aplicamos esta regra se a disciplina não for de bloco duplo
                if duplo_per[_d] == 'nao':

                    # Agrupa os interruptores desta disciplina neste dia
                    _aulas_no_dia = [x[(_t, _d, _dia, _tempo)] for _tempo in tempos]
                    _soma_aulas_dia = sum(_aulas_no_dia)
        
                    # A soma destas aulas tem de ser menor ou igual a 1
                    modelo.Add(_soma_aulas_dia <= 1)
    return (duplo_per,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ##R4
    * Para disciplinas práticas (como Ed. Física ou EV), obriga a que, se houver aula num determinado dia, esta tenha a duração de dois tempos seguidos.
    """)
    return


@app.cell
def _(dias, disciplinas_lista, duplo_per, modelo, tempos, turmas_lista, x):
    for _t in turmas_lista:
        for _d in disciplinas_lista:
            for _dia in dias:

                if duplo_per[_d] == 'sim':

                    _aulas_no_dia = [x[(_t, _d, _dia, _tempo)] for _tempo in tempos]
                    _soma_aulas_dia = sum(_aulas_no_dia)
        
                    _teve_aula = modelo.NewBoolVar(f'teve_aula_{_t}_{_d}_{_dia}')

                    modelo.Add(_soma_aulas_dia == 2).OnlyEnforceIf(_teve_aula)
                    modelo.Add(_soma_aulas_dia == 0).OnlyEnforceIf(_teve_aula.Not())

                    _blocos_validos = []
                    for _i in range(1, 5): 
                        _bloco = modelo.NewBoolVar(f'bloco_{_t}_{_d}_{_dia}_{_i}')

                        modelo.AddImplication(_bloco, x[(_t, _d, _dia, _i)])
                        modelo.AddImplication(_bloco, x[(_t, _d, _dia, _i+1)])
                        _blocos_validos.append(_bloco)

                    modelo.AddExactlyOne(_blocos_validos).OnlyEnforceIf(_teve_aula)

                    for _b in _blocos_validos:
                        modelo.Add(_b == 0).OnlyEnforceIf(_teve_aula.Not())
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## R5

    Nesta etapa, garantimos que os recursos humanos não sofrem sobreposições e que os seus horários de indisponibilidade são respeitados.
    * **Regra R5 (Sem Sobreposição):** Para cada professor, em cada tempo específico (dia e hora), agrupamos todas as variáveis de todas as disciplinas que ele leciona, cruzando com todas as turmas. Aplicando `AddAtMostOne`, garantimos que o professor não está em duas turmas ao mesmo tempo.
    """)
    return


@app.cell
def _(
    df_disciplinas,
    dias,
    disciplinas_lista,
    modelo,
    professores_lista,
    tempos,
    turmas_lista,
    x,
):
    prof_disc = df_disciplinas.set_index('disciplina')['professor'].to_dict()

    for _p in professores_lista:
        _discs_do_prof = [_d for _d in disciplinas_lista if prof_disc[_d] == _p]
        for _dia in dias:
            for _tempo in tempos:
                _aulas_do_prof_neste_tempo = []
                for _t in turmas_lista:
                    for _d in _discs_do_prof:
                        _aulas_do_prof_neste_tempo.append(x[(_t, _d, _dia, _tempo)])
                modelo.AddAtMostOne(_aulas_do_prof_neste_tempo)
    return (prof_disc,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ##R6
    * O modelo itera sobre a base de dados de exceções. Para cada registo de indisponibilidade, identificam-se as disciplinas do professor afetado e força-se o valor das respetivas variáveis booleanas a `0` (desligado) nesse exato dia e período.
    """)
    return


@app.cell
def _(df_excecoes, disciplinas_lista, modelo, prof_disc, turmas_lista, x):
    excecoes_lista = df_excecoes[['professor', 'dia', 'periodo']].values.tolist()

    for _p, _dia_exc, _tempo_exc in excecoes_lista:
        _discs_do_prof = [_d for _d in disciplinas_lista if prof_disc[_d] == _p]
        _tempo_exc_int = int(_tempo_exc)
        for _t in turmas_lista:
            for _d in _discs_do_prof:
                if (_t, _d, _dia_exc, _tempo_exc_int) in x:
                    modelo.Add(x[(_t, _d, _dia_exc, _tempo_exc_int)] == 0)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ##R7

    A Regra R7 garante que os limites físicos da infraestrutura escolar são rigorosamente respeitados a qualquer momento (dia e período).

    * Salas Normais: Em qualquer dia e hora, o número total de turmas a ter aulas normais não pode ultrapassar o limite de salas comuns disponíveis.
    * Salas Especiais: Disciplinas como Educação Física ou Programação exigem salas específicas (Ginásio, Laboratório). O motor cruza a informação com o ficheiro das salas e garante que não há, por exemplo, duas turmas no Laboratório de Informática se a escola só possuir um.
    """)
    return


@app.cell
def _(
    df_disciplinas,
    df_salas,
    dias,
    disciplinas_lista,
    modelo,
    pd,
    tempos,
    turmas_lista,
    x,
):
    sala_req = df_disciplinas.set_index('disciplina')['sala_especial'].to_dict()
    cap_salas_normais = df_salas[df_salas['tipo'] == 'normal']['quantidade'].sum()
    cap_especiais = df_salas[df_salas['tipo'] == 'especial'].set_index('sala')['quantidade'].to_dict()

    for _dia in dias:
        for _tempo in tempos:
            _aulas_normais_neste_tempo = []
            _aulas_especiais_neste_tempo = {_sala: [] for _sala in cap_especiais.keys()}

            for _t in turmas_lista:
                for _d in disciplinas_lista:
                    _req = sala_req[_d]
                    if pd.isna(_req) or _req == "": 
                        _aulas_normais_neste_tempo.append(x[(_t, _d, _dia, _tempo)])
                    elif _req in cap_especiais:
                        _aulas_especiais_neste_tempo[_req].append(x[(_t, _d, _dia, _tempo)])

            modelo.Add(sum(_aulas_normais_neste_tempo) <= cap_salas_normais)

            for _sala_nome, _quantidade in cap_especiais.items():
                modelo.Add(sum(_aulas_especiais_neste_tempo[_sala_nome]) <= _quantidade)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## O1

    * A regra O1 define a função objetivo principal do horário. O seu propósito é melhorar o horário para os professores, minimizando os "furos" (tempos mortos entre aulas) ao longo do dia.
    * Para fazer isto, o modelo calcula qual é o primeiro e o último tempo de aulas de cada professor em cada dia. Os espaços vazios pelo meio são considerados "furos". A missão final que damos ao motor é encontrar um horário onde a soma de todos os furos da escola seja a menor possível.
    """)
    return


@app.cell
def _(
    dias,
    disciplinas_lista,
    modelo,
    prof_disc,
    professores_lista,
    tempos,
    turmas_lista,
    x,
):
    primeiro_tempo = {}
    ultimo_tempo = {}
    furos_diarios = {}
    prof_ativo = {}

    for _p in professores_lista:
        for _dia in dias:
            primeiro_tempo[_p, _dia] = modelo.NewIntVar(min(tempos), max(tempos), f'primeiro_{_p}_{_dia}')
            ultimo_tempo[_p, _dia] = modelo.NewIntVar(min(tempos), max(tempos), f'ultimo_{_p}_{_dia}')
            furos_diarios[_p, _dia] = modelo.NewIntVar(0, len(tempos), f'furos_{_p}_{_dia}')

            for _tempo in tempos:
                prof_ativo[_p, _dia, _tempo] = modelo.NewBoolVar(f'ativo_{_p}_{_dia}_{_tempo}')

    for _p in professores_lista:
        _discs_do_prof = [_d for _d in disciplinas_lista if prof_disc[_d] == _p]

        for _dia in dias:
            for _tempo in tempos:
                _aulas_no_momento = [x[(_t, _d, _dia, _tempo)] for _t in turmas_lista for _d in _discs_do_prof]

                modelo.Add(prof_ativo[_p, _dia, _tempo] == sum(_aulas_no_momento))
                modelo.Add(primeiro_tempo[_p, _dia] <= _tempo).OnlyEnforceIf(prof_ativo[_p, _dia, _tempo])
                modelo.Add(ultimo_tempo[_p, _dia] >= _tempo).OnlyEnforceIf(prof_ativo[_p, _dia, _tempo])

            _total_aulas_hoje = sum(prof_ativo[_p, _dia, _tempo] for _tempo in tempos)
            modelo.Add(furos_diarios[_p, _dia] >= ultimo_tempo[_p, _dia] - primeiro_tempo[_p, _dia] + 1 - _total_aulas_hoje)

    modelo.Minimize(sum(furos_diarios[_p, _dia] for _p in professores_lista for _dia in dias))
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ##Execução do Solver e Verificação de Viabilidade

    Com o modelo matemático totalmente definido (variáveis e restrições R1 a R7), instanciamos o `CpSolver` para procurar uma solução válida.
    O estatuto retornado ditará se as restrições impostas pelos dados permitem a construção de um horário (`OPTIMAL` ou `FEASIBLE`) ou se o problema é sobredimensionado para os recursos (`INFEASIBLE`).
    """)
    return


@app.cell
def _(cp_model, mo, modelo):
    solver = cp_model.CpSolver()

    solver.parameters.log_search_progress = True

    solver.parameters.max_time_in_seconds = 60.0

    status = solver.Solve(modelo)

    if status == cp_model.OPTIMAL or status == cp_model.FEASIBLE:
        mensagem_final = mo.md(f"O motor encontrou um horário válido para a tua escola! (Status: {solver.StatusName(status)})")
    else:
        mensagem_final = mo.md("O motor não conseguiu encontrar nenhuma combinação possível com estas regras. (O horário é impossível)")

    mensagem_final
    return (solver,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ##Extração e Visualização dos Horários

    Uma vez encontrada a solução ótima, o passo final consiste em traduzir os resultados matemáticos de volta para um formato legível.

    **Decisões de Modelação:**
    * **Extração de Dados:** O modelo itera sobre todas as variáveis de decisão da grelha. Através do método `solver.Value()`, verificamos quais os "interruptores" que o motor efetivamente ativou (valor igual a 1).
    * **Estruturação Visual:** Os dados extraídos são organizados em dicionários e convertidos em `DataFrames` do Pandas, onde as linhas representam os tempos letivos e as colunas representam os dias da semana.
    * **Interface (UI):** Recorremos à função `mo.ui.tabs` do Marimo para criar separadores dinâmicos para cada turma, permitindo uma navegação limpa pelos horários sem sobrecarregar o ecrã.
    """)
    return


@app.cell
def _(dias, disciplinas_lista, mo, pd, solver, tempos, turmas_lista, x):
    _tabs_turmas = {}

    for _t in turmas_lista:

        _grelha = { _dia: ["-"] * len(tempos) for _dia in dias }

        for _dia in dias:
            for _tempo in tempos:
                _indice_tempo = _tempo - 1
                for _d in disciplinas_lista:
                    if solver.Value(x[(_t, _d, _dia, _tempo)]) == 1:
                        _grelha[_dia][_indice_tempo] = _d

        _df_horario = pd.DataFrame(_grelha)

        _df_horario.index = [f"{_temp}º Tempo" for _temp in tempos]

        _tabs_turmas[f"Turma {_t}"] = _df_horario

    mo.vstack([
        mo.md("Horários Finais das Turmas"),
        mo.ui.tabs(_tabs_turmas)
    ])
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ##R9

    * A Regra R9 garante a construção incremental do horário. Quando os dados mudam (como novas exceções de professores), o motor gera um novo horário válido, mas tenta mantê-lo o mais igual possível ao horário original (H0).
    * Para isso, guardamos as variáveis do horário antigo em memória. Depois, alteramos a função objetivo: em vez de minimizar os furos, o modelo passa a minimizar as diferenças (mudanças de aulas) entre o horário novo e o antigo.
    """)
    return


@app.cell
def _(cp_model, pd, solver, x):
    memoria_H0 = {}
    for _chaves, _variavel in x.items():
        memoria_H0[_chaves] = solver.Value(_variavel)

    def gerar_horario(pasta_dados, memoria_H0=None):

        df_turmas = pd.read_csv(f"{pasta_dados}turmas.csv")
        df_disciplinas = pd.read_csv(f"{pasta_dados}disciplinas.csv")
        df_salas = pd.read_csv(f"{pasta_dados}salas.csv")
        df_excecoes = pd.read_csv(f"{pasta_dados}disponibilidade_excecoes.csv")

        dias = ['Seg', 'Ter', 'Qua', 'Qui', 'Sex']
        tempos = [1, 2, 3, 4, 5]
        turmas_lista = df_turmas['turma'].tolist()
        disciplinas_lista = df_disciplinas['disciplina'].tolist()
        professores_lista = df_disciplinas['professor'].unique().tolist()

        prof_disc = df_disciplinas.set_index('disciplina')['professor'].to_dict()
        carga_sem = df_disciplinas.set_index('disciplina')['carga_semanal'].to_dict()
        duplo_per = df_disciplinas.set_index('disciplina')['duplo_periodo'].to_dict()
        sala_req = df_disciplinas.set_index('disciplina')['sala_especial'].to_dict()
        cap_salas_normais = df_salas[df_salas['tipo'] == 'normal']['quantidade'].sum()
        cap_especiais = df_salas[df_salas['tipo'] == 'especial'].set_index('sala')['quantidade'].to_dict()

        modelo = cp_model.CpModel()
        x_vars = {}

        for _t in turmas_lista:
            for _d in disciplinas_lista:
                for _dia in dias:
                    for _tempo in tempos:
                        x_vars[(_t, _d, _dia, _tempo)] = modelo.NewBoolVar(f"aula_{_t}_{_d}_{_dia}_{_tempo}")

        #R1
        for _t in turmas_lista:
            for _dia in dias:
                for _tempo in tempos:
                    _aulas_nesse_tempo = [x_vars[(_t, _d, _dia, _tempo)] for _d in disciplinas_lista]
                    modelo.AddAtMostOne(_aulas_nesse_tempo)

        #R2
        for _t in turmas_lista:
            for _d in disciplinas_lista:
                _aulas_da_semana = [x[(_t, _d, _dia, _tempo)] for _dia in dias for _tempo in tempos]
    
                # A correção está aqui: envolver em int()
                _carga_esperada = int(carga_sem[_d])
    
                modelo.Add(sum(_aulas_da_semana) == _carga_esperada)

        #R3 e R4
        for _t in turmas_lista:
            for _d in disciplinas_lista:
                for _dia in dias:
                    if duplo_per[_d] == 'nao':
                        _aulas_no_dia = [x_vars[(_t, _d, _dia, _tempo)] for _tempo in tempos]
                        modelo.Add(sum(_aulas_no_dia) <= 1)
                    elif duplo_per[_d] == 'sim':
                        _aulas_no_dia = [x_vars[(_t, _d, _dia, _tempo)] for _tempo in tempos]
                        _soma_aulas_dia = sum(_aulas_no_dia)
    
                        _teve_aula = modelo.NewBoolVar(f'teve_aula_{_t}_{_d}_{_dia}')
                        modelo.Add(_soma_aulas_dia == 2).OnlyEnforceIf(_teve_aula)
                        modelo.Add(_soma_aulas_dia == 0).OnlyEnforceIf(_teve_aula.Not())
    
                        _blocos_validos = []
                        for _i in range(1, 5): 
                            _bloco = modelo.NewBoolVar(f'bloco_{_t}_{_d}_{_dia}_{_i}')
                            modelo.AddImplication(_bloco, x_vars[(_t, _d, _dia, _i)])
                            modelo.AddImplication(_bloco, x_vars[(_t, _d, _dia, _i+1)])
                            _blocos_validos.append(_bloco)

                        modelo.AddExactlyOne(_blocos_validos).OnlyEnforceIf(_teve_aula)
                        for _b in _blocos_validos:
                            modelo.Add(_b == 0).OnlyEnforceIf(_teve_aula.Not())

        #R5
        for _p in professores_lista:
            _discs_do_prof = [_d for _d in disciplinas_lista if prof_disc[_d] == _p]
            for _dia in dias:
                for _tempo in tempos:
                    _aulas_do_prof_neste_tempo = []
                    for _t in turmas_lista:
                        for _d in _discs_do_prof:
                            _aulas_do_prof_neste_tempo.append(x_vars[(_t, _d, _dia, _tempo)])
                    modelo.AddAtMostOne(_aulas_do_prof_neste_tempo)

        #R6
        excecoes_lista = df_excecoes[['professor', 'dia', 'periodo']].values.tolist()
        for _p, _dia_exc, _tempo_exc in excecoes_lista:
            _discs_do_prof = [_d for _d in disciplinas_lista if prof_disc[_d] == _p]
            _tempo_exc_int = int(_tempo_exc)
            for _t in turmas_lista:
                for _d in _discs_do_prof:
                    if (_t, _d, _dia_exc, _tempo_exc_int) in x:
                        modelo.Add(x[(_t, _d, _dia_exc, _tempo_exc_int)] == 0)

        #R7
        for _dia in dias:
            for _tempo in tempos:
                _aulas_normais_neste_tempo = []
                _aulas_especiais_neste_tempo = {_sala: [] for _sala in cap_especiais.keys()}

                for _t in turmas_lista:
                    for _d in disciplinas_lista:
                        _req = sala_req[_d]
                        if pd.isna(_req) or _req == "": 
                            _aulas_normais_neste_tempo.append(x_vars[(_t, _d, _dia, _tempo)])
                        elif _req in cap_especiais:
                            _aulas_especiais_neste_tempo[_req].append(x_vars[(_t, _d, _dia, _tempo)])

                modelo.Add(sum(_aulas_normais_neste_tempo) <= cap_salas_normais)
                for _sala_nome, _quantidade in cap_especiais.items():
                    modelo.Add(sum(_aulas_especiais_neste_tempo[_sala_nome]) <= _quantidade)


        if memoria_H0 is None:

            primeiro_tempo = {}
            ultimo_tempo = {}
            furos_diarios = {}
            prof_ativo = {}

            for _p in professores_lista:
                for _dia in dias:
                    primeiro_tempo[_p, _dia] = modelo.NewIntVar(min(tempos), max(tempos), f'primeiro_{_p}_{_dia}')
                    ultimo_tempo[_p, _dia] = modelo.NewIntVar(min(tempos), max(tempos), f'ultimo_{_p}_{_dia}')
                    furos_diarios[_p, _dia] = modelo.NewIntVar(0, len(tempos), f'furos_{_p}_{_dia}')
                    for _tempo in tempos:
                        prof_ativo[_p, _dia, _tempo] = modelo.NewBoolVar(f'ativo_{_p}_{_dia}_{_tempo}')

            for _p in professores_lista:
                _discs_do_prof = [_d for _d in disciplinas_lista if prof_disc[_d] == _p]
                for _dia in dias:
                    for _tempo in tempos:
                        _aulas_no_momento = [x_vars[(_t, _d, _dia, _tempo)] for _t in turmas_lista for _d in _discs_do_prof]

                        modelo.Add(prof_ativo[_p, _dia, _tempo] == sum(_aulas_no_momento))
                        modelo.Add(primeiro_tempo[_p, _dia] <= _tempo).OnlyEnforceIf(prof_ativo[_p, _dia, _tempo])
                        modelo.Add(ultimo_tempo[_p, _dia] >= _tempo).OnlyEnforceIf(prof_ativo[_p, _dia, _tempo])

                    _total_aulas_hoje = sum(prof_ativo[_p, _dia, _tempo] for _tempo in tempos)
                    modelo.Add(furos_diarios[_p, _dia] >= ultimo_tempo[_p, _dia] - primeiro_tempo[_p, _dia] + 1 - _total_aulas_hoje)

            modelo.Minimize(sum(furos_diarios[_p, _dia] for _p in professores_lista for _dia in dias))

        else:
            lista_mudancas = []

            for _chaves, _var_nova in x_vars.items():
                if _chaves in memoria_H0:
                    valor_antigo = memoria_H0[_chaves]
                    _mudou = modelo.NewBoolVar(f"mudou_{_chaves}")

                    if valor_antigo == 1:
                        modelo.Add(_mudou == 1 - _var_nova)
                    else:
                        modelo.Add(_mudou == _var_nova)
    
                    lista_mudancas.append(_mudou)

            modelo.Minimize(sum(lista_mudancas))

        return modelo, x_vars, turmas_lista, disciplinas_lista, dias, tempos

    return gerar_horario, memoria_H0


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Construção Incremental

    Nesta secção, simulamos uma alteração de última hora carregando uma nova pasta de dados (`dados_v2/`). O objetivo principal é gerar um novo horário válido, mas minimizando o impacto das alterações face ao horário original (H0).

    * Injeção de Estado (Fotografia): Chamamos a nossa fábrica genérica `gerar_horario` passando-lhe os dados novos, mas injetamos o dicionário `memoria_H0`.
    * Distância de Hamming (XOR Linear): Ao detetar a memória, o modelo altera automaticamente a sua Função Objetivo. Em vez de minimizar os furos (O1), o motor constrói uma função linear (_mudou == 1 - _var_nova` ou `_mudou == _var_nova) para penalizar qualquer variável que assuma um estado diferente do que tinha no H0.
    * Resultado: O motor afunila a pesquisa para encontrar a solução válida mais próxima do estado anterior, desenhando de seguida as matrizes atualizadas do H1.
    """)
    return


@app.cell
def _(cp_model, gerar_horario, memoria_H0, mo, pd):
    modelo_H1, x_H1, turmas_H1, disc_H1, dias_H1, tempos_H1 = gerar_horario("dados_v2/", memoria_H0=memoria_H0)

    solver_H1 = cp_model.CpSolver()
    solver_H1.parameters.max_time_in_seconds = 60.0
    status_H1 = solver_H1.Solve(modelo_H1)

    _tabs_turmas_H1 = {}

    if status_H1 == cp_model.OPTIMAL or status_H1 == cp_model.FEASIBLE:
        for _t in turmas_H1:
            _grelha_H1 = { _dia: ["-"] * len(tempos_H1) for _dia in dias_H1 }

            for _dia in dias_H1:
                for _tempo in tempos_H1:
                    _indice_tempo = _tempo - 1 

                    for _d in disc_H1:
                        if solver_H1.Value(x_H1[(_t, _d, _dia, _tempo)]) == 1:
                            _grelha_H1[_dia][_indice_tempo] = _d

            _df_horario_H1 = pd.DataFrame(_grelha_H1)
            _df_horario_H1.index = [f"{_temp}º Tempo" for _temp in tempos_H1]
            _tabs_turmas_H1[f"Turma {_t}"] = _df_horario_H1

        resultado_R9 = mo.vstack([
            mo.md(f"**SUCESSO R9:** O horário incremental foi gerado! (Status: {solver_H1.StatusName(status_H1)})"),
            mo.md("### Horários Finais Incremenais (H1)"),
            mo.ui.tabs(_tabs_turmas_H1)
        ])
    else:
        resultado_R9 = mo.md("**FALHA:** Os novos dados tornam o horário impossível.")

    resultado_R9
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## TESTES

    * Aqui são feitos os testes com uma pasta nova ("dados_teste") criada por mim com ficheios em CSV.
    """)
    return


@app.cell
def _(
    carga_sem,
    df_disciplinas,
    df_excecoes,
    df_turmas,
    dias,
    disciplinas_lista,
    duplo_per,
    mo,
    prof_disc,
    professores_lista,
    solver,
    tempos,
    turmas_lista,
    x,
):
    status_auditoria= {
        "R1": "OK", "R2": "OK", "R3": "OK", "R4": "OK", 
        "R5": "OK", "R6": "OK", "R8": "OK"
    }

    # TESTE R1:
    for _t in turmas_lista:
        for _dia in dias:
            for _tempo in tempos:
                if sum(solver.Value(x[(_t, _d, _dia, _tempo)]) for _d in disciplinas_lista) > 1:
                    status_auditoria["R1"] = "FALHOU"

    # TESTE R2: 
    for _t in turmas_lista:
        for _d in disciplinas_lista:
            _aulas_dadas = sum(solver.Value(x[(_t, _d, _dia, _tempo)]) for _dia in dias for _tempo in tempos)
            if _aulas_dadas != int(carga_sem[_d]):
                status_auditoria["R2"] = "FALHOU"

    # TESTE R3: 
    for _t in turmas_lista:
        for _d in disciplinas_lista:
            if duplo_per[_d] == 'nao':
                for _dia in dias:
                    if sum(solver.Value(x[(_t, _d, _dia, _tempo)]) for _tempo in tempos) > 1:
                        status_auditoria["R3"] = "FALHOU"

    # TESTE R4: 
    for _t in turmas_lista:
        for _d in disciplinas_lista:
            if duplo_per[_d] == 'sim':
                for _dia in dias:
                    _soma_blocos = sum(solver.Value(x[(_t, _d, _dia, _tempo)]) for _tempo in tempos)
                    if _soma_blocos not in [0, 2]:
                        status_auditoria["R4"] = "FALHOU"

    # TESTE R5: 
    for _p in professores_lista:
        _discs_do_prof = [_d for _d in disciplinas_lista if prof_disc[_d] == _p]
        for _dia in dias:
            for _tempo in tempos:
                if sum(solver.Value(x[(_t, _d, _dia, _tempo)]) for _t in turmas_lista for _d in _discs_do_prof) > 1:
                    status_auditoria["R5"] = "FALHOU"

    # TESTE R6: 
    _excecoes = df_excecoes[['professor', 'dia', 'periodo']].values.tolist()
    for _p, _dia_exc, _tempo_exc in _excecoes:
        _discs_do_prof = [_d for _d in disciplinas_lista if prof_disc[_d] == _p]
        _tempo_exc_int = int(_tempo_exc)
        for _t in turmas_lista:
            for _d in _discs_do_prof:
                if (_t, _d, _dia_exc, _tempo_exc_int) in x:
                    if solver.Value(x[(_t, _d, _dia_exc, _tempo_exc_int)]) == 1:
                        status_auditoria["R6"] = "FALHOU"

    # TESTE R8:
    if df_turmas.empty or df_disciplinas.empty:
        status_auditoria["R8"] = "FALHOU"

    resultado_auditoria = mo.md(f"""
    ### Resultado dos testes:
    - **R1** (Sem sobreposições de turmas): `{status_auditoria['R1']}`
    - **R2** (Carga semanal exata): `{status_auditoria['R2']}`
    - **R3** (Máximo uma disciplina por dia): `{status_auditoria['R3']}`
    - **R4** (Práticas em blocos duplos): `{status_auditoria['R4']}`
    - **R5** (Sem sobreposições de professores): `{status_auditoria['R5']}`
    - **R6** (Exceções de disponibilidade): `{status_auditoria['R6']}`
    - **R8** (Carregamento de dados por CSV): `{status_auditoria['R8']}`
    """)

    resultado_auditoria
    return


if __name__ == "__main__":
    app.run()
