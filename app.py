import streamlit as st
import math
import time
from PIL import Image

# --- CONFIGURAÇÕES GERAIS ---
st.set_page_config(page_title="Calculadora IsolaFácil", layout="wide")

# --- ESTILO VISUAL ---
st.markdown("""
<style>
    .main {
        background-color: #FFFFFF;
    }
    .block-container {
        padding-top: 2rem;
    }
    h1, h2, h3, h4 {
        color: #003366;  /* Azul escuro */
    }
    .stButton>button {
        background-color: #198754;  /* Verde escuro */
        color: white;
        border-radius: 8px;
        height: 3em;
        width: 100%;
    }
    .stTextInput>div>div>input, .stNumberInput>div>div>input, .stSelectbox>div>div>div {
        background-color: #FFFFFF;
        color: #003366;
    }
    .stTextInput>label, .stNumberInput>label, .stSelectbox>label {
        color: #003366;
    }
    input[type="radio"], input[type="checkbox"] {
        accent-color: #003366;  /* Azul escuro */
    }
</style>
""", unsafe_allow_html=True)

# Carregando e exibindo a imagem do logo
logo = Image.open("logo.png")

# Exibição no topo da página com a imagem do logo ajustada
col1 = st.columns([1])
with col1[0]:
    st.image(logo, width=300)  # Ajuste o valor de 'width' conforme necessário

# --- ESTADO INICIAL ---
if 'isolantes' not in st.session_state:
    st.session_state.isolantes = [
        {
            'nome': "Manta de fibra cerâmica 128kg/m³",
            'densidade': 128.0,
            'k_func': "0.0387 * math.exp(0.0019 * T)"
        }
    ]

# --- FUNÇÕES ---
def cadastrar_isolante(nome, densidade, k_func):
    isolante = {'nome': nome, 'densidade': densidade, 'k_func': k_func}
    st.session_state.isolantes.append(isolante)

def excluir_isolante(nome):
    st.session_state.isolantes = [i for i in st.session_state.isolantes if i['nome'] != nome]

def calcular_k(k_func_str, T_media):
    try:
        return eval(k_func_str, {"math": math, "T": T_media})
    except Exception as ex:
        st.error(f"Erro ao calcular k(T): {ex}")
        return None

# --- SIDEBAR PARA CADASTRO E GESTÃO ---
st.sidebar.title("Cadastro de Isolantes")
aba = st.sidebar.radio("Escolha a opção", ["Cadastrar Isolante", "Gerenciar Isolantes"])

if aba == "Cadastrar Isolante":
    st.sidebar.subheader("Cadastrar Novo Isolante")
    nome = st.sidebar.text_input("Nome do Isolante")
    densidade = st.sidebar.number_input("Densidade [kg/m³]", value=1000.0)
    k_func = st.sidebar.text_input("Função k(T) (use T em °C)", value="0.0387 * math.exp(0.0019 * T)")
    if st.sidebar.button("Cadastrar"):
        cadastrar_isolante(nome, densidade, k_func)
        st.sidebar.success(f"Isolante {nome} cadastrado com sucesso!")

elif aba == "Gerenciar Isolantes":
    st.sidebar.subheader("Isolantes Cadastrados")
    for i in st.session_state.isolantes:
        st.sidebar.write(f"**{i['nome']}** - Densidade: {i['densidade']} kg/m³")
        if st.sidebar.button(f"Excluir {i['nome']}"):
            excluir_isolante(i['nome'])
            st.sidebar.success(f"Isolante {i['nome']} excluído com sucesso!")

# --- INTERFACE PRINCIPAL ---
st.title("Cálculo Térmico - IsolaFácil")

st.markdown("""
Esta aplicação calcula a temperatura da face fria de um isolante térmico,
considerando propriedades do material, condições de temperatura e tipo de geometria.
""")

# --- OPÇÃO DE GEOMETRIA ---
geometria = st.radio("Selecione a geometria:", ["Placa plana", "Cilindro"])

# --- SELEÇÃO DO MATERIAL ---
materiais = [i['nome'] for i in st.session_state.isolantes]
material_selecionado = st.selectbox("Escolha o material do isolante", materiais)
isolante = next(i for i in st.session_state.isolantes if i['nome'] == material_selecionado)
k_func_str = isolante['k_func']

# --- ENTRADAS ---
L = st.number_input("Espessura do isolante (L) [m]", value=0.051)
Tq = st.number_input("Temperatura da face quente (Tq) [°C]", value=250.0)
To = st.number_input("Temperatura ambiente (To) [°C]", value=30.0)
h_conv = st.number_input("Coef. de convecção (h) [W/m²·K]", value=10.0)
e = st.number_input("Emissividade (ε)", value=0.9)
sigma = 5.67e-8

# --- BOTÃO DE CALCULAR ---
calcular_button = st.button("Calcular Temperatura da Face Fria")

if calcular_button:
    # --- CÁLCULO DA TEMPERATURA DA FACE FRIA ---
    Tf = 100.0
    max_iter = 1000
    step = 1.0
    tolerancia = 0.1

    progress = st.progress(0)

    for i in range(max_iter):
        progress.progress(i / max_iter)
        T_media = (Tq + Tf) / 2
        k = calcular_k(k_func_str, T_media)
        if k is None:
            break

        if geometria == "Placa plana":
            q_conducao = k * (Tq - Tf) / L
        else:
            r1 = 0.05
            r2 = r1 + L
            q_conducao = k * (Tq - Tf) / math.log(r2 / r1)

        Tf_K = Tf + 273.15
        To_K = To + 273.15
        hr = e * sigma * (Tf_K**2 + To_K**2) * (Tf_K + To_K)
        h_total = h_conv + hr
        q_conv = h_conv * (Tf - To)
        q_rad = hr * (Tf - To)
        q_transferencia = q_conv + q_rad

        erro = q_conducao - q_transferencia
        if abs(erro) < tolerancia:
            break

        Tf += step if erro > 0 else -step
        time.sleep(0.01)

    # --- RESULTADOS ---
    st.subheader("Resultados")
    st.success(f"Temperatura da face fria: {Tf:.2f} °C")
    st.info(f"Perda por convecção: {q_conv:.2f} W/m²")
    st.info(f"Perda por radiação: {q_rad:.2f} W/m²")
    st.info(f"Perda total (conv. + rad.): {q_transferencia:.2f} W/m²")

    Tq_K = Tq + 273.15
    hr_sem = e * sigma * (Tq_K**2 + To_K**2) * (Tq_K + To_K)
    h_total_sem = h_conv + hr_sem
    q_sem_isolante = h_total_sem * (Tq - To)

    st.warning(f"Perda total sem isolante: {q_sem_isolante:.2f} W/m²")
