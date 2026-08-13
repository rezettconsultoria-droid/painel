#!/usr/bin/env python3
"""
JP Locações — Atualizador Automático do Painel
=============================================
Este script lê os dois Google Sheets, processa os dados e gera
um novo index.html pronto para publicar no GitHub Pages.

REQUISITOS (instalar uma única vez):
  pip install pandas openpyxl requests gspread google-auth

COMO USAR:
  1. Configure os IDs dos arquivos Google Sheets abaixo (já preenchidos)
  2. Configure o token de acesso ao GitHub (instruções abaixo)
  3. Execute: python atualizar_painel.py
  4. O painel estará atualizado em ~2 minutos no GitHub Pages

ALTERNATIVA SEM TOKEN GITHUB:
  Execute o script e faça upload manual do index.html gerado.
"""

import json, os, sys, base64, re
from datetime import datetime
from pathlib import Path

# ══════════════════════════════════════════════════════════════════════════════
# CONFIGURAÇÃO — edite apenas esta seção
# ══════════════════════════════════════════════════════════════════════════════

# IDs dos arquivos no Google Drive (extraídos das URLs)
ID_FINANCEIRO = "1O7vSdKZT3UYAxV1z1R52Ao8-AGSAemoK"
ID_CARTOES    = "1flbRdMi0qf1RrNZAKlsPO2SS80RqBOOQ"

# GitHub — para publicação automática
# Como obter o token:
#   1. Acesse github.com → Settings → Developer settings → Personal access tokens → Tokens (classic)
#   2. Generate new token → marque "repo" → copie o token
#   3. Cole abaixo (nunca compartilhe este token)
GITHUB_TOKEN = "SEU_TOKEN_AQUI"
GITHUB_USER  = "SEU_USUARIO_GITHUB"  # ex: jplocacoes
GITHUB_REPO  = "painel"              # nome do repositório

# Caminho do template HTML (gerado pela reZett — não modificar)
TEMPLATE_PATH = Path(__file__).parent / "index.html"

# ══════════════════════════════════════════════════════════════════════════════
# FUNÇÕES DE LEITURA
# ══════════════════════════════════════════════════════════════════════════════

def baixar_sheet(sheet_id, nome):
    """Baixa o Google Sheet como arquivo Excel via URL de exportação."""
    try:
        import requests
        url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=xlsx"
        print(f"  ↓ Baixando {nome}...", end=" ", flush=True)
        resp = requests.get(url, timeout=30)
        resp.raise_for_status()
        caminho = Path(f"/tmp/jp_{nome}.xlsx")
        caminho.write_bytes(resp.content)
        print(f"OK ({len(resp.content)//1024}KB)")
        return caminho
    except Exception as e:
        print(f"\n  ❌ Erro ao baixar {nome}: {e}")
        print("  💡 Certifique-se que os arquivos estão compartilhados ('Qualquer pessoa com o link')")
        sys.exit(1)

def extrair_dados(arq_financeiro, arq_cartoes):
    """Extrai e processa todos os dados necessários para o painel."""
    import pandas as pd

    MESES = ['Jan','Fev','Mar','Abr','Mai','Jun','Jul','Ago','Set','Out','Nov','Dez']
    dados = {}

    # ── DRE ──────────────────────────────────────────────────────────────────
    print("  ↻ Processando DRE...", end=" ", flush=True)
    dre = pd.read_excel(arq_financeiro, sheet_name='DRE', header=None)
    skip = {'nan','ANO-BASE:','(R$)',
        'BASE: REGIME DE COMPETENCIA. RECEITA = FATURAMENTO DO PERIODO (SERVICOS FATURADOS, EXCETO CANCELADOS), INDEPENDENTE DO RECEBIMENTO.',
        'NAO DEDUZ INADIMPLENCIA - A VISAO DE CAIXA (RECEBIMENTOS / AGING / INADIMPLENCIA) ESTA NO PAINEL.'}
    dre_data = {}
    for i in range(len(dre)):
        label = str(dre.iloc[i,0]).strip() if pd.notna(dre.iloc[i,0]) else ''
        if not label or label in skip: continue
        vals = [float(dre.iloc[i,j]) if pd.notna(dre.iloc[i,j]) and isinstance(dre.iloc[i,j],(int,float)) else None for j in range(1,14)]
        dre_data[label] = vals
    dados['dre_data'] = dre_data
    print("OK")

    # ── Fluxo de Caixa ────────────────────────────────────────────────────────
    print("  ↻ Processando Fluxo de Caixa...", end=" ", flush=True)
    fc = pd.read_excel(arq_financeiro, sheet_name='FLUXO DE CAIXA', header=None)
    skip_fc = {'nan','ANO-BASE:','(R$)',
        'ENTRADAS = NOTAS RECEBIDAS (DATA DO PAGAMENTO). SAIDAS = TITULOS PAGOS NO MES DO VENCIMENTO. VALORES EM R$.',
        'SALDO INICIAL DOS BANCOS E INFORMADO SOMENTE NA COLUNA JAN'}
    fc_data = {}
    for i in range(len(fc)):
        label = str(fc.iloc[i,0]).strip() if pd.notna(fc.iloc[i,0]) else ''
        if not label or label in skip_fc: continue
        vals = [float(fc.iloc[i,j]) if pd.notna(fc.iloc[i,j]) and isinstance(fc.iloc[i,j],(int,float)) else None for j in range(1,14)]
        fc_data[label] = vals
    dados['fc_data'] = fc_data
    print("OK")

    # ── KPIs mensais ─────────────────────────────────────────────────────────
    print("  ↻ Calculando KPIs mensais...", end=" ", flush=True)
    rec = pd.read_excel(arq_financeiro, sheet_name='RECEITA', header=10)
    rec['ANO'] = pd.to_numeric(rec['ANO'], errors='coerce')
    rec['VALOR DA NOTA'] = pd.to_numeric(rec['VALOR DA NOTA'], errors='coerce')
    rec['VALOR PAGO']    = pd.to_numeric(rec['VALOR PAGO'],    errors='coerce')
    ano_atual = datetime.now().year
    r_ano = rec[rec['ANO']==ano_atual]
    fat_mes = r_ano.groupby('MES')['VALOR DA NOTA'].sum().to_dict()
    rec_mes = r_ano.groupby('MES')['VALOR PAGO'].sum().to_dict()

    kpis = []
    for i, mes in enumerate(range(1,13)):
        kpis.append({
            'm': MESES[i],
            'rec_bruta':   dre_data.get('RECEITA BRUTA DE SERVICOS (FATURAMENTO)',[None]*13)[i],
            'rec_liq':     dre_data.get('(=) RECEITA LIQUIDA',[None]*13)[i],
            'recebimento': fc_data.get('RECEBIMENTO DE CLIENTES',[None]*13)[i],
            'ebitda':      dre_data.get('(=) EBITDA',[None]*13)[i],
            'resultado':   dre_data.get('(=) RESULTADO ANTES DE INVESTIMENTOS',[None]*13)[i],
            'desp_op':     dre_data.get('(-) DESPESAS OPERACIONAIS',[None]*13)[i],
            'desp_dir':    dre_data.get('(-) DESPESAS DIRETORIA',[None]*13)[i],
            'desp_fin':    dre_data.get('(-) DESPESAS FINANCEIRAS',[None]*13)[i],
            'capex':       dre_data.get('(-) INVESTIMENTOS (CAPEX)',[None]*13)[i],
            'mg_contrib':  dre_data.get('MARGEM DE CONTRIBUICAO %',[None]*13)[i],
            'mg_ebitda':   dre_data.get('MARGEM EBITDA %',[None]*13)[i],
            'mg_liq':      dre_data.get('MARGEM LIQUIDA %',[None]*13)[i],
            'saldo_fc':    fc_data.get('(=) SALDO FINAL DE CAIXA',[None]*13)[i],
            'inadimp':     max(0, fat_mes.get(mes,0) - rec_mes.get(mes,0)),
        })
    dados['kpis'] = kpis
    print("OK")

    # ── Cartões ───────────────────────────────────────────────────────────────
    print("  ↻ Processando Cartões...", end=" ", flush=True)
    try:
        dash = pd.read_excel(arq_cartoes, sheet_name='Dashboard 2026', header=None)
        dados['cart_mensal']  = [float(dash.iloc[8,j])  if pd.notna(dash.iloc[8,j])  else 0 for j in range(2,14)]
        dados['cart_lanc']    = [int(dash.iloc[9,j])    if pd.notna(dash.iloc[9,j]) and dash.iloc[9,j]!=0  else 0 for j in range(2,14)]
        dados['cart_ticket']  = [float(dash.iloc[10,j]) if pd.notna(dash.iloc[10,j]) and dash.iloc[10,j]!=0 else 0 for j in range(2,14)]
        nomes_cartao = ['EMPRESARIAL BRADESCO','CRÉDITO C6 BANK','CRÉDITO YAGO/EMPRESA','CRÉDITO HIPERCARD','CRÉDITO PORTO SEGURO']
        dados['cart_por_cartao'] = {}
        for ci, nome in enumerate(nomes_cartao):
            dados['cart_por_cartao'][nome] = [float(dash.iloc[14+ci,j]) if pd.notna(dash.iloc[14+ci,j]) else 0 for j in range(2,14)]
    except Exception as e:
        print(f"⚠️ Aviso cartões: {e}")
        dados.update({'cart_mensal':[0]*12,'cart_lanc':[0]*12,'cart_ticket':[0]*12,'cart_por_cartao':{}})
    print("OK")

    # ── Fixo × Variável ───────────────────────────────────────────────────────
    print("  ↻ Calculando Fixo × Variável...", end=" ", flush=True)
    ctrl = pd.read_excel(arq_financeiro, sheet_name='CONTROLE', header=18)
    ctrl.columns = ['VENCIMENTO','CONTA','SUBCONTA','TIPO_CUSTO','BANCO','FORMA_PAG',
                    'DETALHE','VALOR_PREV','STATUS','MES','DATA_COMPRA','VALOR_PAGO','DESVIO','AJUSTE','EXTRA']
    ctrl = ctrl[ctrl['CONTA'].notna() & (ctrl['CONTA'] != 'CONTA')]
    ctrl['VALOR_PREV_N'] = pd.to_numeric(ctrl['VALOR_PREV'], errors='coerce').fillna(0)
    ctrl['MES_N']        = pd.to_numeric(ctrl['MES'], errors='coerce')
    ctrl_c = ctrl[~ctrl['CONTA'].isin(['INVESTIMENTOS','RECEBIVEIS'])]

    fixo_mes = []; var_mes = []
    for mes in range(1,13):
        m = ctrl_c[ctrl_c['MES_N']==mes]
        fixo_mes.append(round(m[m['TIPO_CUSTO']=='FIXO']['VALOR_PREV_N'].sum(), 2))
        var_mes.append(round(m[m['TIPO_CUSTO']=='VARIAVEL']['VALOR_PREV_N'].sum(), 2))

    dados['fixo_mes']    = fixo_mes
    dados['variavel_mes']= var_mes

    # Break-even
    mc_pct_raw = dre_data.get('MARGEM DE CONTRIBUICAO %',[None]*13)
    rec_bruta  = dre_data.get('RECEITA BRUTA DE SERVICOS (FATURAMENTO)',[None]*13)
    be_clean = []
    mc_clean = []
    for i in range(12):
        mc = mc_pct_raw[i]; rec_b = rec_bruta[i]
        if mc and rec_b and rec_b > 0 and 0 < mc < 2:
            be_clean.append(round(fixo_mes[i]/mc, 2))
            mc_clean.append(round(mc, 4))
        else:
            be_clean.append(None)
            mc_clean.append(None)

    dados['be_clean']    = be_clean
    dados['mc_pct_clean']= mc_clean
    meses_validos = [i for i in range(7) if mc_clean[i] and rec_bruta[i] and rec_bruta[i]>0]
    dados['mc_media']    = round(sum(mc_clean[i] for i in meses_validos)/len(meses_validos),4) if meses_validos else 0.769
    dados['fixo_media']  = round(sum(fixo_mes[:7])/7,2)
    dados['be_media']    = round(dados['fixo_media']/dados['mc_media'],2) if dados['mc_media'] else 0
    dados['fat_media']   = round(sum(r for r in rec_bruta[:7] if r)/7,2) if any(rec_bruta[:7]) else 0

    print("OK")

    # Acumulado
    def safe_sum(lst, n=8):
        return sum(v for v in lst[:n] if v is not None)

    saldo_final = next((fc_data.get('(=) SALDO FINAL DE CAIXA',[None]*13)[i] for i in range(7,-1,-1)
                        if fc_data.get('(=) SALDO FINAL DE CAIXA',[None]*13)[i] is not None), None)

    dados['acumulado'] = {
        'm': 'Acumulado',
        'rec_bruta':   safe_sum(dre_data.get('RECEITA BRUTA DE SERVICOS (FATURAMENTO)',[None]*13)),
        'rec_liq':     safe_sum(dre_data.get('(=) RECEITA LIQUIDA',[None]*13)),
        'recebimento': safe_sum(fc_data.get('RECEBIMENTO DE CLIENTES',[None]*13)),
        'ebitda':      safe_sum(dre_data.get('(=) EBITDA',[None]*13)),
        'resultado':   safe_sum(dre_data.get('(=) RESULTADO ANTES DE INVESTIMENTOS',[None]*13)),
        'desp_op':     safe_sum(dre_data.get('(-) DESPESAS OPERACIONAIS',[None]*13)),
        'desp_dir':    safe_sum(dre_data.get('(-) DESPESAS DIRETORIA',[None]*13)),
        'desp_fin':    safe_sum(dre_data.get('(-) DESPESAS FINANCEIRAS',[None]*13)),
        'capex':       safe_sum(dre_data.get('(-) INVESTIMENTOS (CAPEX)',[None]*13)),
        'mg_contrib':  None, 'mg_ebitda': None, 'mg_liq': None,
        'saldo_fc':    saldo_final,
        'inadimp':     sum(max(0, fat_mes.get(m,0)-rec_mes.get(m,0)) for m in range(1,9)),
        'cart_tot':    sum(dados['cart_mensal'][:8]),
    }
    rec_tot = dados['acumulado']['rec_bruta']
    if rec_tot:
        dados['acumulado']['mg_contrib'] = (dados['acumulado']['rec_bruta'] + dados['acumulado']['desp_op']) / rec_tot if rec_tot else None
        dados['acumulado']['mg_ebitda']  = dados['acumulado']['ebitda'] / rec_tot if rec_tot else None
        dados['acumulado']['mg_liq']     = dados['acumulado']['resultado'] / rec_tot if rec_tot else None

    return dados

def atualizar_js_no_html(html_content, dados):
    """Substitui os blocos de dados JS no HTML pelo conteúdo atualizado."""
    import json

    MESES = ['Jan','Fev','Mar','Abr','Mai','Jun','Jul','Ago','Set','Out','Nov','Dez']

    novos_dados = f"""
// ══ DADOS FIXO × VARIÁVEL ═══════════════════════════════════════════════════
const DATA_FIXO_MES     = {json.dumps(dados['fixo_mes'])};
const DATA_VARIAVEL_MES = {json.dumps(dados['variavel_mes'])};
const DATA_BE_MES       = {json.dumps(dados['be_clean'])};
const DATA_MC_PCT       = {json.dumps(dados['mc_pct_clean'])};

// ══ DADOS MENSAIS ═══════════════════════════════════════════════════════════
const DATA_KPIS = {json.dumps(dados['kpis'], ensure_ascii=False)};
const DATA_ACUMULADO = {json.dumps(dados['acumulado'], ensure_ascii=False)};
const DATA_DRE = {json.dumps(dados['dre_data'], ensure_ascii=False)};
const DATA_FC  = {json.dumps(dados['fc_data'],  ensure_ascii=False)};
const DATA_CART_MENSAL    = {json.dumps(dados['cart_mensal'])};
const DATA_CART_LANC      = {json.dumps(dados['cart_lanc'])};
const DATA_CART_TICKET    = {json.dumps(dados['cart_ticket'])};
const DATA_CART_CARTAO    = {json.dumps(dados.get('cart_por_cartao',{}), ensure_ascii=False)};
const MESES = {json.dumps(MESES)};
"""

    # Substituir bloco de dados entre os marcadores
    pattern = r'// ══ DADOS FIXO × VARIÁVEL.*?const MESES = \[.*?\];'
    novo_html = re.sub(pattern, novos_dados.strip(), html_content, flags=re.DOTALL)

    # Atualizar data de posição no header
    hoje = datetime.now()
    meses_pt = ['Janeiro','Fevereiro','Março','Abril','Maio','Junho',
                 'Julho','Agosto','Setembro','Outubro','Novembro','Dezembro']
    nova_posicao = f"{meses_pt[hoje.month-1]} / {hoje.year}"
    novo_html = re.sub(r'Posição: [A-Za-zÀ-ú]+ \d{4}', f'Posição: {nova_posicao}', novo_html)
    novo_html = re.sub(r'Posição: \d{1,2} [A-Za-zÀ-ú]+ \d{4}', f'Posição: {hoje.strftime("%d")} {meses_pt[hoje.month-1]} {hoje.year}', novo_html)

    return novo_html

def publicar_github(html_content):
    """Faz upload do index.html para o repositório GitHub."""
    if GITHUB_TOKEN == "SEU_TOKEN_AQUI":
        print("  ⚠️  Token GitHub não configurado — pulando publicação automática")
        print("  💡 Faça upload manual do index.html gerado em /tmp/index_atualizado.html")
        return False

    try:
        import requests

        api = f"https://api.github.com/repos/{GITHUB_USER}/{GITHUB_REPO}/contents/index.html"
        headers = {
            "Authorization": f"token {GITHUB_TOKEN}",
            "Accept": "application/vnd.github.v3+json"
        }

        # Verificar se arquivo já existe (para pegar o SHA)
        resp = requests.get(api, headers=headers)
        sha = resp.json().get('sha') if resp.status_code == 200 else None

        # Preparar payload
        conteudo_b64 = base64.b64encode(html_content.encode()).decode()
        payload = {
            "message": f"Atualiza painel — {datetime.now().strftime('%d/%m/%Y %H:%M')}",
            "content": conteudo_b64,
            "branch": "main"
        }
        if sha:
            payload["sha"] = sha

        resp = requests.put(api, headers=headers, json=payload)
        if resp.status_code in [200, 201]:
            print(f"  ✅ Publicado! URL: https://{GITHUB_USER}.github.io/{GITHUB_REPO}")
            return True
        else:
            print(f"  ❌ Erro GitHub: {resp.status_code} — {resp.json().get('message','')}")
            return False

    except ImportError:
        print("  ⚠️  requests não instalado. Execute: pip install requests")
        return False

# ══════════════════════════════════════════════════════════════════════════════
# EXECUÇÃO PRINCIPAL
# ══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    print("=" * 55)
    print("  JP Locações — Atualizador de Painel")
    print(f"  {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
    print("=" * 55)

    # 1. Baixar arquivos
    print("\n📥 Baixando arquivos do Google Drive...")
    arq_fin  = baixar_sheet(ID_FINANCEIRO, "financeiro")
    arq_cart = baixar_sheet(ID_CARTOES,    "cartoes")

    # 2. Extrair dados
    print("\n🔄 Processando dados...")
    dados = extrair_dados(arq_fin, arq_cart)

    # 3. Carregar template HTML
    print("\n📄 Atualizando painel HTML...")
    if not TEMPLATE_PATH.exists():
        print(f"  ❌ Template não encontrado: {TEMPLATE_PATH}")
        print("  💡 Coloque o index.html na mesma pasta deste script")
        sys.exit(1)

    html = TEMPLATE_PATH.read_text(encoding='utf-8')
    html_atualizado = atualizar_js_no_html(html, dados)

    # 4. Salvar localmente
    saida = Path("/tmp/index_atualizado.html")
    saida.write_text(html_atualizado, encoding='utf-8')
    print(f"  ✅ HTML gerado: {saida} ({len(html_atualizado.encode())//1024}KB)")

    # Também salvar ao lado do script para conveniência
    (TEMPLATE_PATH.parent / "index.html").write_text(html_atualizado, encoding='utf-8')
    print(f"  ✅ Template atualizado: {TEMPLATE_PATH.parent / 'index.html'}")

    # 5. Publicar no GitHub
    print("\n🚀 Publicando no GitHub Pages...")
    publicar_github(html_atualizado)

    # Limpar temporários
    arq_fin.unlink(missing_ok=True)
    arq_cart.unlink(missing_ok=True)

    print("\n" + "=" * 55)
    print("  ✅ Concluído!")
    print("=" * 55)
