import bcrypt
import redis
import json
import dash
import logging
import os
import pandas as pd
import numpy as np
import plotly.colors
from dash import dash_table
import plotly.subplots as sp
import plotly.express as px
from dash import Dash, dcc, html
from flask_mail import Mail, Message
from dash.dependencies import Input, Output
import dash_bootstrap_components as dbc
from plotly.colors import qualitative
from dash import dash_table, html, dcc
from dash import dcc, html, callback
import plotly.graph_objects as go
from itsdangerous import URLSafeTimedSerializer
from flask_mail import Mail, Message
from flask import url_for
from flask import Flask, request, redirect, render_template, session, url_for, flash

# Inicializando o Flask
server = Flask(__name__)

#app = Flask(__name__)
server.secret_key = 'E4szBdssrjeeYOp1o4XiuH8QJruHXQ1g'


# Configurações de email 
server.config['MAIL_SERVER'] = 'smtp.gmail.com'
server.config['MAIL_PORT'] = 587
server.config['MAIL_USE_TLS'] = True
server.config['MAIL_USERNAME'] = 'andreandson09@gmail.com'  # Seu email
server.config['MAIL_PASSWORD'] = 'cjuk badq koxo xhkj'            # Api do email
server.config['MAIL_DEFAULT_SENDER'] = 'andreandson09@gmail.com'

mail = Mail(server)

# Configuração do serializer para gerar tokens
serializer = URLSafeTimedSerializer(server.secret_key)

# Conectando ao banco de dados Redis com a senha
r = redis.Redis(
    host='redis-11835.c278.us-east-1-4.ec2.redns.redis-cloud.com',
    port=11835,
    password='Carlos123456#',
    db=0,
    decode_responses=True
)

def get_user_data(batch_size=500):
    
    all_records = []

    try:
        # Recuperar todas as chaves que começam com 'ia_dummy:*'
        keys = list(r.scan_iter("ia_dummy:*"))
        
        # Dividir as chaves em lotes
        for i in range(0, len(keys), batch_size):
            batch_keys = keys[i:i + batch_size]
            batch_values = r.mget(batch_keys)  # Obter todos os valores em um único comando
            
            for record_json in batch_values:
                if record_json:
                    try:
                        record_data = json.loads(record_json)  # Converter o JSON para um dicionário
                        all_records.append(record_data)  # Adicionar o dicionário à lista
                    except json.JSONDecodeError as e:
                        print(f"Erro ao decodificar JSON: {e}")

    except Exception as e:
        print(f"Erro ao buscar dados do Redis: {e}")

    # Converter a lista de dicionários em um DataFrame
    return pd.DataFrame(all_records)

# Uso da função
df_data = get_user_data(batch_size=500)

# Criar uma coluna de data combinando ano e mês
df_data['Data'] = pd.to_datetime(df_data['Year'].astype(str) + '-' + df_data['Month'].astype(str) + '-01')

# Inicialize o aplicativo Dash
app_dash = Dash(__name__, server=server, url_base_pathname='/dashboard/', external_stylesheets=[dbc.themes.BOOTSTRAP])

# Layout da barra lateral
sidebar = html.Div(
    [
        dbc.Card(
            [
                html.Img(src="/static/logo.png", style={"width": "100%", "height": "auto"}),
                html.Hr(),
                dbc.Nav(
                    [
                        #dbc.NavLink("Home", href="/home", active="exact"),#
                        dbc.NavLink("Home", href="/home", active="exact"),
                        dbc.NavLink("Tabela", href="https://tabela-8fdd318c24e8.herokuapp.com/", active="exact"),
                    ],
                    vertical=True,
                    pills=True,
                ),
            ],
            style={"height": "100vh", "padding": "20px", "backgroundColor": "#e0e0e0"},
        )
    ],
    style={"position": "fixed", "top": 0, "left": 0, "bottom": 0, "width": "120px", "zIndex": 1},
)

# Layout do dashboard atualizado
dashboard_layout = html.Div(children=[
    # Link para o arquivo CSS na pasta static
    html.Link(rel='stylesheet', href='/static/style.css'),

    # Barra lateral (Sidebar)
    sidebar,

    # Componente para controlar a URL
    dcc.Location(id='url', refresh=False),

    # Conteúdo principal
    html.Div(id="page-content", style={"margin-left": "260px", "padding": "20px"}),

    # Card com a centralização da seleção
    dbc.Row([  # Agrupando as colunas em uma única linha
        dbc.Col([  # Coluna para selecionar país
            html.Div([
                html.Label("Selecione País:", style={"position": "absolute", "top": "0px"}),
                dcc.Dropdown(
                    id="dropdown-pais",
                    options=[{'label': pais, 'value': pais} for pais in df_data["Country"].unique()],
                    value=sorted(df_data["Country"].unique()),
                    multi=True,
                    placeholder="Selecione País"
                ),
            ], style={"margin-top": "0px"})  # Removendo margem superior
        ], width=4),  # Aumentando a largura da coluna para 3

        dbc.Col([  # Coluna para selecionar ano
            html.Div([
                html.Label("Selecione Ano:", style={"position": "absolute", "top": "0px"}),
                dcc.Dropdown(
                    id='dropdown-ano',
                    options=[{'label': ano, 'value': ano} for ano in sorted(df_data["Year"].unique())],
                    value=sorted(df_data["Year"].unique()),
                    multi=True,
                    placeholder="Selecione Ano"
                ),
            ], style={"margin-top": "0px"})  # Removendo margem superior
        ], width=4),  # Aumentando a largura da coluna para 3

        dbc.Col([  # Coluna para variável de análise
            html.Div([
                html.H6("Variavel Análise:", style={"position": "absolute", "top": "0px"}),
                dcc.RadioItems(
                    options=[{'label': 'Box 9L', 'value': 'Box 9L'}],
                    value='Box 9L',
                    id="main_variable",
                    inputStyle={"margin-right": "5px", "margin-left": "20px"}
                ),
            ], style={"margin-top": "0px"})  # Removendo margem superior  # Centralizando e ajustando espaçamento
        ], width=3),  # Aumentando a largura da coluna para 3
    ], justify="center", style={"margin-top": "0px"}),  # Centralizando as colunas dentro da Row

    # Gráficos
    dbc.Container([  
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader("Volume Ano Móvel"),
                    dbc.CardBody([
                        dcc.Graph(id="total-volume-ano-movel", className="graph")
                    ])
                ])
            ], width=6),  # Ajustado para ocupar metade da linha (6 colunas)

            dbc.Col([
                dbc.Card([
                    dbc.CardHeader("Volume YTD"),
                    dbc.CardBody([
                        dcc.Graph(id="total-volume-ytd", className="graph"),
                        dcc.Dropdown(
                        id='periodo-dropdown',
                        options=[
                            {'label': '3 Meses', 'value': '3'},
                            {'label': '6 Meses', 'value': '6'},
                            {'label': '9 Meses', 'value': '9'},
                        ],
                        value='3',  # Valor padrão
                        clearable=False
                    )
                ])
            ])
            ], width=6)
        ], className="row"),

        # Segunda linha com dois gráficos
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader("Volume Calendario"),
                    dbc.CardBody([
                        dcc.Graph(id='total-volume-pais', className="graph")
                    ])
                ])
            ], width=6)
        ], className="row"),

        # Terceira linha com gráfico e tabela divididos igualmente
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader("Volume Produtos"),
                    dbc.CardBody([
                        dcc.Graph(id="total-volume-ano", className="graph")
                    ])
                ])
            ], width=6),

            dbc.Col([
                dbc.Card([
                    dbc.CardHeader("Volume Marca"),
                    dbc.CardBody([
                        dcc.Graph(id="total-volume-acima-5", className="graph")
                    ])
                ])
            ], width=6)
        ], className="row"),

        # Quarta linha com um novo gráfico
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader("Volume by Company"),
                    dbc.CardBody([
                        dcc.Graph(id="total-volume-fabricante", className="graph")
                    ])
                ])
            ], width=6),

            dbc.Col([
                dbc.Card([
                    dbc.CardHeader("Analytcs Volume by Type"),
                    dbc.CardBody([
                        dcc.Graph(id="volume-Tipo", className="graph")
                    ])
                ])
            ], width=6)
        ], className="row")
    ]),

    # Footer
    html.Footer(
        children=[
            html.Div("Developed by Startup ADW - Advanced Digital Wellness",
                     style={"textAlign": "center", "padding": "5px", "color": "#f7f4f4"})
        ],
        style={
            "position": "relative",
            "bottom": "0",
            "width": "105%",
            "background-color": "rgba(52, 51, 53, 0.9)",
            "color": "#333",
            "borderTop": "1px solid #ddd",
            "height": "40px",
            "padding": "5px",
            "text-align": "center",
            "font-size": "12px",
            "left": "0",
        }
    )
])

# Adicione o layout à aplicação Dash
app_dash.layout = dashboard_layout

@app_dash.callback(
    [
        Output('total-volume-ano-movel', 'figure'),
        Output('total-volume-ytd', 'figure'),
        Output('total-volume-pais', 'figure'),
        Output('total-volume-ano', 'figure'),
        Output('total-volume-acima-5', 'figure'),
        Output('total-volume-fabricante', 'figure'),
        Output('volume-Tipo', 'figure')
    ],
    [
        Input('dropdown-ano', 'value'),
        Input('dropdown-pais', 'value')
    ]
)
def update_graphs(selected_years, selected_countries):
    # Verifica se não há seleções
    if not selected_years or not selected_countries:
        return {}, {}, {}, {}, {} # Retorna gráficos vazios


    # Filtrando os dados com base nos anos e países selecionados
    df_filtered = df_data[(df_data['Year'].isin(selected_years)) & (df_data['Country'].isin(selected_countries))]
    df_sorted = df_filtered.sort_values(by=['Country', 'Year', 'Month'])

    # Calcular a Média Móvel (12 meses) do Volume por País
    df_sorted['Media Móvel Ano Móvel'] = df_sorted.groupby('Country')['Box 9L'].rolling(window=12, min_periods=1).mean().reset_index(0, drop=True)

    # Agrupar por País e Ano para ter a média móvel por ano
    media_volume_movel = df_sorted.groupby(['Country', 'Year'])['Media Móvel Ano Móvel'].last().reset_index()

    # Criar a figura
    fig = go.Figure()

    # Adicionar barras para o volume total acumulado
    for country in media_volume_movel['Country'].unique():
        country_data = media_volume_movel[media_volume_movel['Country'] == country]
        fig.add_trace(go.Bar(
            x=country_data['Year'],
            y=country_data['Media Móvel Ano Móvel'],
            name=country,
            hoverinfo='y+name',
            showlegend=True
        ))

    # Adicionar linha de média móvel
    # Para fazer isso, você deve calcular a média da média móvel total para cada ano
    media_anual = media_volume_movel.groupby('Year')['Media Móvel Ano Móvel'].mean().reset_index()
    
    fig.update_xaxes(tickmode='linear')  # Define o modo de tick para linear
    # Adicionar a linha
    fig.add_trace(go.Scatter(
        x=media_anual['Year'],
        y=media_anual['Media Móvel Ano Móvel'],
        mode='lines+markers',
        name='Média Geral Móvel',
        line=dict(color='red', width=2)
    ))

    # Atualizar o layout do gráfico
    fig.update_layout(
        title='Média Móvel do Volume por Ano',
        xaxis_title='Ano',
        yaxis_title='Média Móvel do Volume',
        font_color='black',
        barmode='group'
    )


    # Gráfico Total Volume Ano YTD 
    # Criando uma coluna para o ano e o mês
    df_filtered['YearMonth'] = df_filtered['Data'].dt.to_period('M')

    # Agrupando por YearMonth e Country, e somando o volume
    total_ytd = df_filtered.groupby(['YearMonth', 'Country'])['Box 9L'].sum().reset_index()

    # Calculando o volume acumulado
    total_ytd['Cumulative Volume'] = total_ytd['Box 9L'].cumsum()

    # Convertendo YearMonth para datetime para plotagem
    total_ytd['YearMonth'] = total_ytd['YearMonth'].dt.to_timestamp()

    # Criando o gráfico com pontos conectados por uma linha
    fig_ytd = px.line(
        total_ytd,
        x='YearMonth',
        y='Cumulative Volume',
        color='Country',  # Define uma linha para cada país
        title='Volume YTD',
        markers=True  # Adiciona pontos na linha
)
   
    # Atualizando o layout do gráfico
    fig_ytd.update_xaxes(
        tickangle=90,
        tickvals=total_ytd['YearMonth'].dt.year.unique(),  # Definindo os ticks do eixo x como os anos únicos
        ticktext=total_ytd['YearMonth'].dt.year.unique()  # Definindo o texto do tick como os anos
    )

    fig_ytd.update_layout(
    font_color='black',
    legend_title_text='Country',  # Definindo o título da legenda
    title={'text': "Total Volume YTD", 'x': 0.5},  # Centralizando o título
    xaxis_title="Year",
    yaxis_title="Volume Acumulado"
    )
 

    # Gráfico Total Volume por País
    total_por_pais = df_filtered.groupby(['Year', 'Country'])['Box 9L'].sum().reset_index()
    
    fig_pais = px.bar(total_por_pais, x='Year', y='Box 9L', color='Country',
                      title='Volume Calendario',
                      labels={'Box 9L': 'Total Volume (9L)', 'Year': 'Year'},
                      barmode='group')
    fig_pais.update_xaxes(tickmode='linear')  # Define o modo de tick para linear

    fig_pais.update_layout(
        
        font_color='black'
    )

   # Gráfico Total Volume por Ano
    total_volume_por_ano = df_filtered.groupby(['Year', 'Product'])['Box 9L'].sum().reset_index()
    fig_total_volume_ano = px.bar(
        total_volume_por_ano,
        x='Year',
        y='Box 9L',
        color='Product',
        title='Volume by Product',
        labels={'Box 9L': 'Total Volume', 'Year': 'Year', 'Product': 'Product'},
        barmode='group'
    )
    fig_total_volume_ano.update_xaxes(tickmode='linear')  # Define o modo de tick para linear
    
    fig_total_volume_ano.update_layout(
        
        font_color='black'
    )

# Gráfico Total Volume por Marca Acima de 5%
    df_filtrado_acima_100 = df_filtered[df_filtered['Box 9L'] > 100]

    # Calculando o volume total
    total_volume = df_filtrado_acima_100['Box 9L'].sum()

    # Filtrando marcas com volume acima de 5% do total
    df_filtrado_acima_5_percent = df_filtrado_acima_100[
        df_filtrado_acima_100['Box 9L'] > 0.01 * total_volume
    ]

    # Agrupando por Fabricante Produtor e Marca
    total_volume_acima_5_percent = df_filtrado_acima_5_percent.groupby(['Fabricante Produtor', 'Brand'])['Box 9L'].sum().reset_index()

    # Criando uma paleta de cores personalizada que evita repetição
    unique_brands = total_volume_acima_5_percent['Brand'].nunique()
    cores_personalizadas = plotly.colors.qualitative.Plotly * (unique_brands // len(plotly.colors.qualitative.Plotly) + 1)
    cores_personalizadas = cores_personalizadas[:unique_brands]

    # Criando o gráfico de rosca
    fig_volume_acima_5_percent = px.pie(
        total_volume_acima_5_percent,
        names='Brand',
        values='Box 9L',
        title='Volume Brand',
        color='Fabricante Produtor',
        hole=0.4,  # Para criar o efeito de rosca
        color_discrete_sequence=cores_personalizadas  # Usando a paleta de cores personalizada
    )

    # Atualizando o layout do gráfico
    fig_volume_acima_5_percent.update_traces(textinfo='percent+label')
    fig_volume_acima_5_percent.update_layout(
        
        font_color='black'
    )
    
        # Total Volume por Fabricante Produtor
    total_volume_fabricante = df_data[(df_data['Year'].isin(selected_years)) & (df_data['Country'].isin(selected_countries))]
    top_manufacturers = total_volume_fabricante.groupby('Fabricante Produtor')['Box 9L'].sum().nlargest(10).reset_index()

    fig_total_volume_fabricante = px.bar(
        total_volume_fabricante,
        y=top_manufacturers['Fabricante Produtor'],
        x=top_manufacturers['Box 9L'],
        orientation='h',  # Gráfico de barras horizontais
        color_discrete_sequence=['blue'],  # Cor das barras
    )

    # Atualizando o layout e nomeando os eixos
    fig_total_volume_fabricante.update_layout(
        font_color='black',
        xaxis_title="Volume em Box 9L",  # Nome do eixo X
        yaxis_title="Fabricante Produtor",  # Nome do eixo Y
        #title={'text': "Top 10 Fabricantes por Volume", 'x': 0.5},  # Centralizando o título
    )

    
    # Filtrar os dados com base nos anos e países selecionados
    volume_tipo = df_data[(df_data['Year'].isin(selected_years)) & (df_data['Country'].isin(selected_countries))]

    # Agrupar o volume por tipo e empresa
    company_sales = volume_tipo.groupby(['Type', 'Fabricante Produtor'])['Box 9L'].sum().reset_index()

    # Criar o gráfico de barras horizontais
    fig_bar = px.bar(
        company_sales.groupby('Type')['Box 9L'].sum().reset_index(),  # Soma o volume por tipo
        y='Type',  # Eixo Y contém os tipos (categorias) para barras horizontais
        x='Box 9L',  # Eixo X contém os valores numéricos (volume)
        color_discrete_sequence=['blue'],  # Cor das barras
        text='Box 9L',  # Exibir valores nas pontas das barras
        orientation='h'  # Definir a orientação como horizontal
    )

    # Atualizando o layout do gráfico de barras
    fig_bar.update_layout(
        title='Volume by Type',
        xaxis_title='Volume (Box 9L)',
        yaxis_title='Tipo',
        font_color='black',
        height=400
        
    )

    # Posicionar o texto fora das barras
    fig_bar.update_traces(textposition='outside')

    
    # Criar o gráfico de pizza para mostrar a proporção de cada tipo
    fig_pie = px.pie(
        company_sales.groupby('Type')['Box 9L'].sum().reset_index(),  # Soma o volume por tipo
        values='Box 9L',  # Valores numéricos para o gráfico de pizza
        names='Type',  # Categorias que serão exibidas como fatias
        title='Share by Type',
        color_discrete_sequence=px.colors.sequential.Blues  # Paleta de cores
    )

        # Encontrar o tipo com maior valor
    grouped_sales = company_sales.groupby('Type')['Box 9L'].sum().reset_index()
    max_value_index = grouped_sales['Box 9L'].idxmax()

    # Atualizar layout do gráfico de pizza e destacar a fatia com maior % (pull=0.1)
    fig_pie.update_traces(
        textposition='inside', 
        textinfo='percent+label',
        pull=[0.1 if i == max_value_index else 0 for i in range(len(grouped_sales))]  # Destaca a fatia maior
    )

        # Atualizar o layout do gráfico
    fig_pie.update_layout(
        height=400,
        
        showlegend=True
    )
    # Criar a tabela com volume por tipo e empresa
    fig_table = go.Figure(data=[go.Table(
        header=dict(values=['<b>Type</b>', '<b>Company</b>', '<b>Volume (Box 9L)</b>'],
                    fill_color='lightgrey',
                    align='center'),
        cells=dict(values=[company_sales['Type'], company_sales['Fabricante Produtor'], company_sales['Box 9L']],
                fill_color='white',
                align='center'))
    ])

    fig_table.update_layout(title="Volume by Type and Company", font_color='black', height=400
    )

    # Criar um layout de subplots com os gráficos de barras e pizza na parte superior e a tabela na parte inferior
    fig_combined = sp.make_subplots(
        rows=2, cols=2, 
        row_heights=[0.7, 0.3],  # Ajusta a altura das linhas
        column_widths=[0.5, 0.5],  # Ajusta a largura das colunas
        subplot_titles=("Volume por Tipo", "Share by Type", "Volume by Type and Company"),
        specs=[[{"type": "bar"}, {"type": "pie"}], [{"colspan": 2, "type": "table"}, None]]  # Define a tabela ocupando duas colunas
    )

    # Adicionar o gráfico de barras ao subplot 1 (superior esquerdo)
    for trace in fig_bar.data:
        fig_combined.add_trace(trace, row=1, col=1)

    # Adicionar o gráfico de pizza ao subplot 2 (superior direito)
    for trace in fig_pie.data:
        fig_combined.add_trace(trace, row=1, col=2)

    # Adicionar a tabela ao subplot 3 (inferior)
    for trace in fig_table.data:
        fig_combined.add_trace(trace, row=2, col=1)

    # Ajustar o layout geral
    fig_combined.update_layout(
        height=800,  # Aumenta a altura total do gráfico combinado
        width=1000,  # Aumenta a largura total do gráfico combinado
        title_text="Analytics Volume by Type,Share by Type e Company", 
        showlegend=False
    )

    # Retorna todos os gráficos, incluindo o gráfico combinado de barras, pizza e tabela
    return fig, fig_ytd, fig_pais, fig_total_volume_ano, fig_volume_acima_5_percent, fig_total_volume_fabricante, fig_combined


# Callback para atualizar o conteúdo com base na URL
@app_dash.callback(
    Output('page-content', 'children'),
    Input('url', 'pathname')  # Observa mudanças na URL
)

def display_page(pathname):
    if pathname == '/home':
        return render_template('home.html')  # Renderiza a página Home
    elif pathname == '/login':
        return render_template('login.html')  # Renderiza a página de login
    elif pathname == '/register':
        return render_template('register.html')  # Renderiza a página de registro
    elif pathname == '/recover_password':
        return render_template('recover_password.html')  # Renderiza a página de recuperação de senha
    
# Rota para a página Home
@server.route('/home')
def home():
    return render_template('home.html')  # arquivo 'home.html'


# Rota para a página de login
@server.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        # Obtendo o usuário do Redis
        stored_password = r.hget(f"user:{email}", "password")

        if stored_password and bcrypt.checkpw(password.encode('utf-8'), stored_password.encode('utf-8')):
            session['email'] = email  # Armazenando a sessão do usuário
            return redirect('/dashboard')
        else:
            return "Incorrect email or password."

    return render_template('login.html')


# Rota de registro
@server.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')

        # Verificando se o usuário já existe
        if r.hget(f"user:{email}", "email"):
            return "User already registered!"

        # Hasheando a senha antes de armazenar
        hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

        # Armazenando os dados no Redis
        r.hset(f"user:{email}", mapping={
            "username": username,
            "email": email,
            "password": hashed_password.decode('utf-8'),
            "confirmed": "false"  # Marcando o email como não confirmado
        })
        print(f"User {username} registered with email {email}")
        # Gerar um token de verificação
        token = serializer.dumps(email, salt='email-confirmation')

        # Criar URL de verificação
        confirm_url = url_for('confirm_email', token=token, _external=True)

        # Enviar e-mail de verificação
        msg = Message('Confirm your email', recipients=[email])
        msg.body = f'Please click the link to confirm your registration: {confirm_url}'
        mail.send(msg)

        return "Registration complete! Please check your email to confirm your account."

    return render_template('register.html')

@server.route('/confirm_email/<token>')
def confirm_email(token):
    try:
        # Validar o token com duração de 1 hora
        email = serializer.loads(token, salt='email-confirmation', max_age=3600)
        print(f"Token valid, email: {email}")
    except:
        print("The confirmation link is invalid or has expired.")
        return "The confirmation link is invalid or has expired."

    # Atualizar o campo 'confirmed' para 'true' no Redis
    r.hset(f"user:{email}", "confirmed", "true")

    return redirect('/login')


@server.route('/recover_password', methods=['GET', 'POST'])
def recover_password():
    # Lógica para recuperação de senha
    if request.method == 'POST':
        # Aqui você processaria a recuperação de senha
        email = request.form.get('email')
        # Verifique se o email está no banco de dados e envie um email de recuperação.
        return "Recovery email sent!"

    return render_template('recover_password.html')

@server.route('/logout')
def logout():
    session.pop('email', None)  # Remover a sessão do usuário
    return redirect('/login')

@server.route('/')
def index():
       
    return app_dash ('home.html')  # Página inicial gerenciada pelo Flask


# Executando a aplicação
if __name__ == '__main__':
    app_dash.run(server=server)
    
