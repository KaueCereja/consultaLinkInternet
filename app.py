import streamlit as st
import pandas as pd
import re

st.set_page_config(page_title="Links e Internet", layout="wide")

st.markdown("""
## 📡 Consulta de Links de Dados e Internet
""")

# ==================== CARREGAMENTO DE DADOS ====================
@st.cache_data(ttl=3600)
def load_data():
    url = "https://docs.google.com/spreadsheets/d/e/2PACX-1vStCsK-I9n6aQ6argn2xcQ1jIe5BCcvHrG5PNmq7xd13dd6i5iZovnR8ahCOzUQZztC8DlT4vYAZyRf/pub?output=csv"
    
    try:
        df = pd.read_csv(url)
    except Exception as e:
        st.warning(f"⚠️ Erro ao carregar do Google Sheets: {e}")
        try:
            df = pd.read_csv("internet-link-CT-14-05-2026 - servicos-contratos.csv", encoding='utf-8')
        except:
            st.error("❌ Não foi possível carregar os dados.")
            return pd.DataFrame()
    
    df.columns = [col.strip() for col in df.columns]
    
    # ===== TRATAMENTO DA COLUNA SIGLA - PRESERVANDO TODOS OS REGISTROS =====
    if 'SIGLA' in df.columns:
        # Limpar espaços e converter para maiúsculas (apenas onde há valor)
        df['SIGLA'] = df['SIGLA'].astype(str).str.strip().str.upper()
        df['SIGLA'] = df['SIGLA'].replace(['NAN', 'NONE', 'N/A', 'nan', 'None'], '')
        df['SIGLA'] = df['SIGLA'].fillna('')
        
        # ===== NOVO: Criar uma SIGLA alternativa usando o CLIENTE =====
        # Para registros sem SIGLA, extrair do nome do cliente
        def extrair_sigla_do_cliente(cliente):
            if pd.isna(cliente) or not isinstance(cliente, str):
                return ''
            # Tentar extrair sigla do nome (ex: "FUNDACAO PROPAZ" -> "FUNDPROPAZ")
            palavras = cliente.split()
            if len(palavras) >= 2:
                # Pega primeiras letras ou abreviação comum
                sigla = ''.join([p[0] for p in palavras if len(p) > 2])[:10]
                return sigla if sigla else palavras[0][:8]
            return cliente[:8] if len(cliente) > 8 else cliente
        
        # Preencher SIGLAS vazias com siglas derivadas do CLIENTE
        mask_sem_sigla = df['SIGLA'] == ''
        if mask_sem_sigla.any():
            df.loc[mask_sem_sigla, 'SIGLA'] = df.loc[mask_sem_sigla, 'CLIENTE'].apply(extrair_sigla_do_cliente)
    
    # Converter valores monetários
    money_cols = ['VALOR UNITARIO', 'VALOR UNITARIO ATUAL', 'VALOR ANUAL', 'VALOR GLOBAL']
    for col in money_cols:
        if col in df.columns:
            df[col] = df[col].astype(str).str.replace('R$ ', '').str.replace('.', '').str.replace(',', '.').str.replace('"', '')
            df[col] = pd.to_numeric(df[col], errors='coerce')
    
    # Converter datas
    date_cols = ['DATA INICIO CT', 'DATA FIM CT', 'DATA INICIO ADITIVO', 'DATA FIM ADITIVO']
    for col in date_cols:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], format='%d/%m/%Y', errors='coerce')
    
    return df

df = load_data()

if df.empty:
    st.stop()

# ===== ESTATÍSTICAS DE DIAGNÓSTICO =====
total_registros = len(df)
registros_com_sigla = len(df[df['SIGLA'] != ''])
registros_sem_sigla = total_registros - registros_com_sigla

# ==================== SIDEBAR ====================
with st.sidebar:
    st.markdown("# 🎯 Filtros")
    
    # Mostrar estatísticas
    st.caption(f"📊 Total: {total_registros} registros")
    if registros_sem_sigla > 0:
        st.caption(f"⚠️ {registros_sem_sigla} registros sem SIGLA original (preenchidos automaticamente)")
    
    if st.button("🔄 Limpar Todos os Filtros", use_container_width=True):
        st.cache_data.clear()
        st.rerun()
    
    st.divider()
    
    filtros = {}
    
    # 1. SIGLA - INCLUINDO TODOS OS REGISTROS
    siglas_validas = sorted([s for s in df['SIGLA'].unique() if s and s != ''])
    
    if siglas_validas:
        sigla_sel = st.multiselect(
            "🏢 Cliente (SIGLA)",
            options=siglas_validas,
            help="Selecione uma ou mais SIGLAS. Registros sem SIGLA foram preenchidos automaticamente."
        )
        if sigla_sel:
            filtros['SIGLA'] = sigla_sel
    
    # 2. MUNICÍPIO
    municipios = sorted(df['MUNICIPIO'].dropna().unique())
    municipio_sel = st.multiselect("📍 Município", options=municipios)
    if municipio_sel:
        filtros['MUNICIPIO'] = municipio_sel
    
    # 3. REGIÃO
    regioes = sorted(df['REGIÃO'].dropna().unique())
    regiao_sel = st.multiselect("🗺️ Região", options=regioes)
    if regiao_sel:
        filtros['REGIÃO'] = regiao_sel
    
    # 4. SERVIÇO
    servicos = sorted(df['SERVICO'].dropna().unique())
    servico_sel = st.multiselect("🔌 Serviço", options=servicos)
    if servico_sel:
        filtros['SERVICO'] = servico_sel
    
    # 5. STATUS DO SERVIÇO
    status_serv = sorted(df['STATUS SERVICO'].dropna().unique())
    status_sel = st.multiselect("⚡ Status do Serviço", options=status_serv)
    if status_sel:
        filtros['STATUS SERVICO'] = status_sel
    
    # 6. STATUS DO CONTRATO
    status_cont = sorted(df['STATUS CONTRATO'].dropna().unique())
    status_cont_sel = st.multiselect("📄 Status do Contrato", options=status_cont)
    if status_cont_sel:
        filtros['STATUS CONTRATO'] = status_cont_sel
    
    st.divider()
    

# ==================== APLICAÇÃO DOS FILTROS ====================
df_filtrado = df.copy()

if 'SIGLA' in filtros:
    df_filtrado = df_filtrado[df_filtrado['SIGLA'].isin(filtros['SIGLA'])]

if 'MUNICIPIO' in filtros:
    df_filtrado = df_filtrado[df_filtrado['MUNICIPIO'].isin(filtros['MUNICIPIO'])]

if 'REGIÃO' in filtros:
    df_filtrado = df_filtrado[df_filtrado['REGIÃO'].isin(filtros['REGIÃO'])]

if 'SERVICO' in filtros:
    df_filtrado = df_filtrado[df_filtrado['SERVICO'].isin(filtros['SERVICO'])]

if 'STATUS SERVICO' in filtros:
    df_filtrado = df_filtrado[df_filtrado['STATUS SERVICO'].isin(filtros['STATUS SERVICO'])]

if 'STATUS CONTRATO' in filtros:
    df_filtrado = df_filtrado[df_filtrado['STATUS CONTRATO'].isin(filtros['STATUS CONTRATO'])]


# ==================== FORMATAÇÃO ====================

# Formatar moeda
money_cols = ['VALOR UNITARIO', 'VALOR UNITARIO ATUAL', 'VALOR ANUAL', 'VALOR GLOBAL']

for col in money_cols:
    if col in df_filtrado.columns:
        df_filtrado[col] = df_filtrado[col].apply(
            lambda x: f'R$ {x:,.2f}'.replace(',', 'X').replace('.', ',').replace('X', '.')
            if pd.notnull(x) else ''
        )

# Formatar datas
date_cols = ['DATA INICIO CT', 'DATA FIM CT', 'DATA INICIO ADITIVO', 'DATA FIM ADITIVO']

for col in date_cols:
    if col in df_filtrado.columns:
        df_filtrado[col] = pd.to_datetime(df_filtrado[col], errors='coerce').dt.strftime('%d/%m/%y')

# ==================== EXIBIÇÃO ====================

st.dataframe(
    df_filtrado,
    use_container_width=True,
    height=min(600, len(df_filtrado) * 35 + 50)
)

if len(df_filtrado) > 0:
    csv = df_filtrado.to_csv(index=False).encode('utf-8')
    st.download_button(
        "📥 Baixar CSV",
        csv,
        "dados_filtrados.csv",
        "text/csv",
        use_container_width=True
    )

# ==================== ANÁLISE DOS DADOS ====================

st.divider()
st.header("📊 Análise dos Dados Filtrados")

# usar exatamente o filtrado
df_analise = df_filtrado.copy()

# ================= EXTRAÇÃO DE MBPS =================

def extrair_mbps(linha):

    texto = " ".join(
        [
            str(v)
            for v in linha.values
            if pd.notna(v)
        ]
    ).upper()

    texto = (
        texto
        .replace(",", ".")
        .replace("GBPS", "G")
        .replace("GB", "G")
        .replace("MBPS", "M")
        .replace("MB", "M")
    )

    total = 0

    # captura:
    # 100M
    # 500 MBPS
    # 1G
    # 2.5 GBPS
    matches = re.findall(
        r'(\d+(?:\.\d+)?)\s*(G|M)',
        texto
    )

    for valor, unidade in matches:

        valor = float(valor)

        if unidade == "G":
            valor *= 1000

        total += valor

    return total


# aplicar na linha inteira
df_analise["MBPS"] = (
    df_analise
    .apply(
        extrair_mbps,
        axis=1
    )
)
# ================= CLASSIFICAÇÃO =================

servico = (
    df_analise["SERVICO"]
    .astype(str)
    .str.upper()
)

internet_df = (
    df_analise[
        servico.str.contains(
            r"INTERNET",
            regex=True,
            na=False
        )
    ]
)

fibra_df = (
    df_analise[
        servico.str.contains(
            r"FIBRA",
            regex=True,
            na=False
        )
    ]
)

radio_df = (
    df_analise[
        servico.str.contains(
            r"RADIO|RÁDIO",
            regex=True,
            na=False
        )
    ]
)

# ================= RESUMO =================

def soma_valor(df_temp):

    if (
        "VALOR GLOBAL"
        not in df_temp.columns
    ):
        return 0

    return (
        pd.to_numeric(
            df_temp["VALOR GLOBAL"],
            errors="coerce"
        )
        .fillna(0)
        .sum()
    )


internet_valor = soma_valor(
    internet_df
)

fibra_valor = soma_valor(
    fibra_df
)

radio_valor = soma_valor(
    radio_df
)

c1, c2, c3 = st.columns(3)

with c1:

    st.metric(
        "🌐 Internet",
        f"{internet_df['MBPS'].sum():,.0f} Mbps"
    )

    st.caption(
        (
            "Valor Global: "
            +
            f"R$ {internet_valor:,.2f}"
            .replace(",", "X")
            .replace(".", ",")
            .replace("X", ".")
        )
    )


with c2:

    st.metric(
        "🧵 Link Dados Fibra",
        f"{fibra_df['MBPS'].sum():,.0f} Mbps"
    )

    st.caption(
        (
            "Valor Global: "
            +
            f"R$ {fibra_valor:,.2f}"
            .replace(",", "X")
            .replace(".", ",")
            .replace("X", ".")
        )
    )


with c3:

    st.metric(
        "📡 Link Dados Rádio",
        f"{radio_df['MBPS'].sum():,.0f} Mbps"
    )

    st.caption(
        (
            "Valor Global: "
            +
            f"R$ {radio_valor:,.2f}"
            .replace(",", "X")
            .replace(".", ",")
            .replace("X", ".")
        )
    )
# ================= DISTRIBUIÇÃO =================

st.subheader("📶 Distribuição de Banda")

grafico_total = pd.DataFrame({
    "Tipo":[
        "Internet",
        "Fibra",
        "Rádio"
    ],
    "Mbps":[
        internet_df["MBPS"].sum(),
        fibra_df["MBPS"].sum(),
        radio_df["MBPS"].sum()
    ]
})

st.bar_chart(
    grafico_total.set_index("Tipo"),
    use_container_width=True
)


# ================= POR REGIÃO =================

if "REGIÃO" in df_analise.columns:

    st.subheader("🗺️ Mbps por Região")

    regiao = (
        df_analise
        .groupby("REGIÃO")
        .apply(
            lambda g: pd.Series({

                "INTERNET_Mbps":
                    g.loc[
                        g.index.isin(
                            internet_df.index
                        ),
                        "MBPS"
                    ].sum(),

                "FIBRA_Mbps":
                    g.loc[
                        g.index.isin(
                            fibra_df.index
                        ),
                        "MBPS"
                    ].sum(),

                "RADIO_Mbps":
                    g.loc[
                        g.index.isin(
                            radio_df.index
                        ),
                        "MBPS"
                    ].sum()

            })
        )
        .reset_index()
    )

    st.dataframe(
        regiao,
        use_container_width=True
    )

    st.bar_chart(
        regiao.set_index("REGIÃO"),
        use_container_width=True
    )


# ================= POR MUNICÍPIO =================

if "MUNICIPIO" in df_analise.columns:

    st.subheader("📍 Mbps por Município")

    municipio = (
        df_analise
        .groupby("MUNICIPIO")
        .apply(
            lambda g: pd.Series({

                "INTERNET_Mbps":
                    g.loc[
                        g.index.isin(
                            internet_df.index
                        ),
                        "MBPS"
                    ].sum(),

                "FIBRA_Mbps":
                    g.loc[
                        g.index.isin(
                            fibra_df.index
                        ),
                        "MBPS"
                    ].sum(),

                "RADIO_Mbps":
                    g.loc[
                        g.index.isin(
                            radio_df.index
                        ),
                        "MBPS"
                    ].sum()

            })
        )
        .reset_index()
    )

    st.dataframe(
        municipio,
        use_container_width=True
    )

    st.bar_chart(
        municipio
        .head(20)
        .set_index("MUNICIPIO"),
        use_container_width=True
    )


# ================= POR CLIENTE =================

if "SIGLA" in df_analise.columns:

    st.subheader("🏢 Mbps e Valores por Cliente")

    base = df_analise.copy()

    # garantir valor numérico
    base["VALOR_GLOBAL_NUM"] = (
        base["VALOR GLOBAL"]
        .astype(str)
        .str.replace("R$", "", regex=False)
        .str.replace(".", "", regex=False)
        .str.replace(",", ".", regex=False)
        .str.replace('"', "", regex=False)
    )

    base["VALOR_GLOBAL_NUM"] = pd.to_numeric(
        base["VALOR_GLOBAL_NUM"],
        errors="coerce"
    ).fillna(0)

    serv = (
        base["SERVICO"]
        .astype(str)
        .str.upper()
    )

    base["TIPO"] = "OUTROS"

    base.loc[
        serv.str.contains("INTERNET", na=False),
        "TIPO"
    ] = "INTERNET"

    base.loc[
        serv.str.contains("FIBRA", na=False),
        "TIPO"
    ] = "FIBRA"

    base.loc[
        serv.str.contains(
            r"RADIO|RÁDIO",
            regex=True,
            na=False
        ),
        "TIPO"
    ] = "RADIO"

    # agrega
    resumo = (
        base
        .groupby(
            [
                "SIGLA",
                "TIPO"
            ]
        )
        .agg({
            "MBPS":"sum",
            "VALOR_GLOBAL_NUM":"sum"
        })
        .reset_index()
    )

    tabela = (
        resumo
        .pivot_table(
            index="SIGLA",
            columns="TIPO",
            values=[
                "MBPS",
                "VALOR_GLOBAL_NUM"
            ],
            fill_value=0
        )
    )

    tabela.columns = [
        f"{b}_{a}"
        for a, b in tabela.columns
    ]

    tabela = tabela.reset_index()

    # criar totais
    tabela["VALOR_TOTAL"] = (
        tabela.filter(
            regex="VALOR_GLOBAL"
        )
        .sum(axis=1)
    )

    tabela["MBPS_TOTAL"] = (
        tabela.filter(
            regex="MBPS"
        )
        .sum(axis=1)
    )

    # formatar valores
    exibir = tabela.copy()

    cols_valor = [
        c
        for c in exibir.columns
        if "VALOR" in c
    ]

    for c in cols_valor:

        exibir[c] = exibir[c].apply(
            lambda x:
            f"R$ {x:,.2f}"
            .replace(",", "X")
            .replace(".", ",")
            .replace("X", ".")
        )

    st.dataframe(
        exibir,
        use_container_width=True
    )

    # gráfico Mbps
    colunas_mbps = [
        c
        for c in tabela.columns
        if c.endswith("MBPS")
        and c != "MBPS_TOTAL"
    ]

    st.subheader("📊 Mbps por Cliente")

    st.bar_chart(
        tabela
        .head(20)
        .set_index("SIGLA")[
            colunas_mbps
        ],
        use_container_width=True
    )

    # gráfico valores
    colunas_valor = [
        c
        for c in tabela.columns
        if "VALOR_GLOBAL" in c
    ]

    st.subheader("💰 Valor por Cliente")

    st.bar_chart(
        tabela
        .head(20)
        .set_index("SIGLA")[
            colunas_valor
        ],
        use_container_width=True
    )
