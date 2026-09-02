# Consulta de Links e Internet

Projeto Streamlit organizado por módulos.

## Estrutura

- `app.py` — ponto de entrada da aplicação.
- `modules/config.py` — configurações, colunas e filtros.
- `modules/data_loader.py` — carregamento e normalização dos dados.
- `modules/formatting.py` — moeda e datas.
- `modules/sidebar.py` — barra lateral e aplicação dos filtros.
- `modules/table_view.py` — tabela principal e download.
- `modules/analysis.py` — cálculos, indicadores, gráficos e análises.

## Correções principais

1. Os valores monetários permanecem numéricos durante toda a análise.
2. A formatação `R$ x.xxx,xx` é aplicada apenas na camada de apresentação.
3. A soma de `VALOR GLOBAL` não depende mais de converter texto formatado.
4. O botão de limpar filtros também limpa os valores dos widgets.
5. A coluna auxiliar `_SIGLA_AUTOMATICA` não aparece na tabela nem no CSV.
