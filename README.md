[README.md](https://github.com/user-attachments/files/31028667/README.md)
# JP Azevedo Locações — Painel de Gestão Financeira 2026

Sistema executivo de gestão financeira desenvolvido por **reZett® Tecnologia e Inteligência Empresarial**.

---

## Módulos do painel (10 abas)

| Aba | Conteúdo |
|-----|----------|
| 📊 Painel Executivo | KPIs principais, semáforos de saúde financeira e plano de ação |
| ⚠️ Risco por Cliente | Inadimplência, PMR e concentração de receita por cliente |
| 🚜 Rentabilidade / Frota | Desempenho por equipamento e controle de seguros |
| 💵 Projeção de Caixa | 3 cenários (pessimista / base / otimista) para 90 dias |
| 🏦 Dívida & Cobertura | DSCR, mapa de financiamentos e oportunidades de alívio |
| 📋 DRE Gerencial | Demonstração de resultado completa — 12 meses + total |
| 💸 Fluxo de Caixa | Regime de caixa — entradas, saídas e saldo mensal |
| 💳 Cartões | Evolução mensal, ranking por subconta e parcelamentos em aberto |
| 📐 Fixo × Variável | Composição de custos por categoria e gráfico mensal |
| ⚖️ Break-even | Ponto de equilíbrio, margem de segurança e análise mensal |

**Filtro global de período** — barra de seleção de mês (Acumulado + Jan a Dez) que atualiza todos os módulos simultaneamente.

---

## Repositório e URL

| Item | Valor |
|------|-------|
| Conta GitHub | `rezettconsultoria-droide` |
| Repositório | `painel` |
| URL pública | `https://rezettconsultoria-droid.github.io/painel` |

---

## Como atualizar o painel mensalmente

Após fechar o mês e lançar os dados nos arquivos Google Sheets:

**Opção A — Script automático (recomendado)**
```bash
python atualizar_painel.py
```
O script baixa os dados do Google Drive, processa tudo e publica automaticamente no GitHub Pages.  
Requisito: configurar `GITHUB_TOKEN` e `GITHUB_USER` no script antes do primeiro uso.

**Opção B — Upload manual**
1. Abra o repositório em `github.com/rezettconsultoria-droide/painel`
2. Clique no arquivo `index.html`
3. Clique no ícone de lápis ✏️ (Edit this file)
4. Selecione tudo (`Ctrl+A`), apague e cole o novo conteúdo
5. Clique em **Commit changes**

A URL não muda. Em menos de 1 minuto o painel está atualizado para todos.

---

## Arquivos do projeto

| Arquivo | Descrição |
|---------|-----------|
| `index.html` | Painel executivo completo — único arquivo, sem dependências externas |
| `atualizar_painel.py` | Script de automação — lê Sheets, processa dados e publica |
| `README.md` | Este arquivo |
| `GUIA_GitHub_Pages.html` | Guia visual de publicação passo a passo |

---

## Atalhos de teclado

| Tecla | Ação |
|-------|------|
| `1` a `8` | Navegar entre as abas |
| `F` | Ativar / desativar tela cheia |

---

## Como compartilhar

- **WhatsApp ou e-mail** — cole a URL diretamente. Abre no navegador do celular sem instalação
- **Google Drive** — botão direito na pasta → Novo → Atalho → cole a URL
- **Reuniões** — abra no Chrome e pressione `F` para tela cheia

---

## Segurança

O repositório **Public** permite que qualquer pessoa com a URL visualize o painel — sem possibilidade de edição.  
Para acesso restrito com senha, configurar via **Netlify** (gratuito no plano básico) ou migrar para repositório **Private** com GitHub Pro (US$ 4/mês).

---

## Dependências e fontes de dados

| Fonte | ID Google Sheets |
|-------|-----------------|
| Controle Financeiro | `1O7vSdKZT3UYAxV1z1R52Ao8-AGSAemoK` |
| Controle de Cartões | `1flbRdMi0qf1RrNZAKlsPO2SS80RqBOOQ` |

Os dados estão embutidos no `index.html` — o painel funciona offline após carregado.  
Para atualizar os dados, usar o script `atualizar_painel.py` ou gerar novo `index.html` via reZett.

---

## Posição dos dados

**Agosto / 2026** — Base: Controle Financeiro + Controle de Cartões · Uso interno — Confidencial

---

*Powered by reZett® Tecnologia e Inteligência Empresarial*
