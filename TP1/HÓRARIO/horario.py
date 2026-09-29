import marimo

__generated_with = "0.25.0"
app = marimo.App(width="medium")


@app.cell
def _():
    import marimo as mo
    import pandas as pd

    # Definir a pasta de origem (isto vai facilitar o requisito R9 quando testarmos a pasta "dados_v2")
    pasta_dados = "dados/"

    # Ler os ficheiros CSV para DataFrames do Pandas
    df_turmas = pd.read_csv(f"{pasta_dados}turmas.csv")
    df_disciplinas = pd.read_csv(f"{pasta_dados}disciplinas.csv")
    df_salas = pd.read_csv(f"{pasta_dados}salas.csv")
    df_excecoes = pd.read_csv(f"{pasta_dados}disponibilidade_excecoes.csv")

    # Limpar dados: substituir os valores nulos (NaN) na sala_especial por strings vazias para evitar erros no código futuro
    df_disciplinas['sala_especial'] = df_disciplinas['sala_especial'].fillna("")

    # Visualizar as tabelas diretamente na interface do Marimo organizadas por separadores
    mo.ui.tabs({
        "Turmas": mo.as_html(df_turmas),
        "Disciplinas": mo.as_html(df_disciplinas),
        "Salas": mo.as_html(df_salas),
        "Exceções de Horário": mo.as_html(df_excecoes)
    })
    return


if __name__ == "__main__":
    app.run()
