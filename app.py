import bcrypt
import logging
import pandas as pd
import numpy as np
import plotly.express as px
from flask import Flask, request, redirect, render_template, session, url_for, flash
from dash import Dash, dcc, html
from dash.dependencies import Input, Output
import dash_bootstrap_components as dbc
import redis
import json
from dash import dash_table
import dash
from plotly.colors import qualitative
import plotly.colors
from dash import dash_table
from dash import dash_table, html, dcc


app = Flask(__name__)
app.secret_key = 'E4szBdssrjeeYOp1o4XiuH8QJruHXQ1g'

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
app_dash = Dash(__name__, server=app, url_base_pathname='/dashboard/', external_stylesheets=[dbc.themes.BOOTSTRAP])

# Layout da barra lateral
sidebar = html.Div(
    [
        dbc.Card(
            [
                html.Img(src="/static/logo.png", style={"width": "100%", "height": "auto"}),
                html.Hr(),
                dbc.Nav(
                    [
                        dbc.NavLink(
                            [html.I(className="fas fa-home", style={"marginRight": "8px"}), " Home"],
                            href="https://cravalbusiness.com/",
                            active="exact"
                        ),  # Link para a página inicial
                        dbc.NavLink(
                            [html.I(className="fas fa-tachometer-alt", style={"marginRight": "8px"}), " Dashboard"],
                            href="/dashboard",
                            active="exact"
                        ),
                        dbc.NavLink(
                            [html.I(className="fas fa-cogs", style={"marginRight": "8px"}), " Tabela"],
                            href="/tabela",
                            active="exact"
                        ),
                        
                        
                    ],
                    vertical=True,
                    pills=True,
                ),
            ],
            style={"height": "100vh", "padding": "20px", "backgroundColor": "#e0e0e0"},
        )
    ],
    style={
        "position": "fixed",
        "top": 0,
        "left": 0,
        "bottom": 0,
        "width": "200px",
        "zIndex": 1,
        "backgroundColor": "#e0e0e0"
    },
)


# Conteúdo principal
content = html.Div(id="page-content", style={"margin-left": "260px", "padding": "20px"})

# Layout do dashboard atualizado
dashboard_layout = html.Div(children=[
    dbc.Row([
        # Barra lateral (Sidebar)
        dbc.Col([
            sidebar
        ], sm=2, style={"position": "fixed", "height": "100%", "background-color": "#e0e0e0"}),  # Fixando a barra lateral e definindo altura completa

        # Conteúdo principal
        dbc.Col([
            dbc.Container([
                dbc.Card([
                    dbc.Row([
                        dbc.Col([
                            html.H6("SELECT COUNTRY", className="titulo-selecao"),
                            dcc.Dropdown(
                                id="dropdown-pais",
                                options=[{'label': pais, 'value': pais} for pais in df_data["Country"].unique()],
                                value=sorted(df_data["Country"].unique()),
                                multi=True,
                                style={
                                    'maxHeight': '300px',
                                    'overflowY': 'auto',
                                    'width': '100%'
                                },
                                searchable=True
                            ),
                        ], width=3),

                        dbc.Col([
                            html.H6("SELECT YEAR", style={"margin-top": "7px"}),
                            dcc.Dropdown(
                                id='dropdown-ano',
                                options=[{'label': ano, 'value': ano} for ano in sorted(df_data["Year"].unique())],
                                value=sorted(df_data["Year"].unique()),
                                multi=True
                            ),
                        ], width=3),

                        dbc.Col([
                            html.H6("ANALYSIS VARIABLE", style={"margin-top": "7px"}),
                            dcc.RadioItems(
                                options=[
                                    {'label': 'Box 9L', 'value': 'Box 9L'},
                                ],
                                value='Box 9L',
                                id="main_variable",
                                inputStyle={"margin-right": "5px", "margin-left": "20px"}
                            ),
                        ], width=3)
                    ]),
                ], style={"height": "auto", "margin": "10px", "padding": "15px", "background-color": "#e0e0e0"})
            ], fluid=True, style={"margin-left": "220px", "background-color": "#e0e0e0"})  # Ajustando a margem para compensar a barra lateral
        ], sm=10),
    ]),

    # Gráficos
    dbc.Container([
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader("Total Volume Ano Móvel"),
                    dbc.CardBody([
                        dcc.Graph(id="total-volume-ano-movel", style={"height": "350px", "margin-left": "20px"})
                    ])
                ])
            ], sm=6.5),
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader("Total Volume YTD"),
                    dbc.CardBody([
                        dcc.Graph(id="total-volume-ytd", style={"height": "350px"})
                    ])
                ])
            ], sm=6.5)
        ], style={"margin-left": "220px", "background-color": "#f0f0f0"}),

        # Segunda linha com dois gráficos
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader("Total Volume Ano Calendário"),
                    dbc.CardBody([
                        dcc.Graph(id="total-volume-ano-calendario", style={"height": "350px", "width": "100%"})
                    ])
                ])
            ], sm=6.5),
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader("Total Volume Pais"),
                    dbc.CardBody([
                        dcc.Graph(id='total-volume-pais', style={"height": "350px", "width": "100%"})
                    ])
                ])
            ], sm=6.5)
        ], style={"margin-left": "220px", "background-color": "#f0f0f0"}),

        # Terceira linha com gráfico e tabela divididos igualmente
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader("Total Volume Produtos"),
                    dbc.CardBody([
                        dcc.Graph(id="total-volume-ano", style={"height": "350px", "width": "100%"})
                    ])
                ])
            ], sm=6.5),
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader("Volume Company Brand"),
                    dbc.CardBody([
                        dcc.Graph(id="total-volume-acima-5", style={"height": "350px", "width": "100%"})
                    ])
                ])
            ], sm=6.5) # Divisão igual para o gráfico (6 colunas)
        ], style={"margin-left": "220px", "background-color": "#f0f0f0"})
    ]),

    # Footer
    html.Footer(
        children=[
            html.Div("© 2024 Craval Business. All rights reserved.", style={"textAlign": "center", "padding": "10px", "color": "#f7f4f4"}),
            html.Div("Developed by ADW Startup ADW - Advanced Digital Wellness", style={"textAlign": "center", "padding": "5px", "color": "#f7f4f4"})
        ],
        style={
            "position": "relative",
            "bottom": "0",
            "width": "100%",
            "background-color": "rgba(52, 51, 53, 0.9)",
            "color": "#333",
            "borderTop": "1px solid #ddd",
            "height": "70px",
            "padding": "5px",
            "text-align": "center",
            "font-size": "10px",
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
        Output('total-volume-ano-calendario', 'figure'),
        Output('total-volume-pais', 'figure'),
        Output('total-volume-ano', 'figure'),
        Output('total-volume-acima-5', 'figure')
    ],
    [
        Input('dropdown-ano', 'value'),
        Input('dropdown-pais', 'value')
    ]
)
def update_graphs(selected_years, selected_countries):
    # Verifica se não há seleções
    if not selected_years or not selected_countries:
        return {}, {}, {}, {}  # Retorna gráficos vazios

    # Gráfico Total Volume Ano Móvel
    df_filtered = df_data[(df_data['Year'].isin(selected_years)) & (df_data['Country'].isin(selected_countries))]
    df_sorted = df_filtered.sort_values(by=['Country', 'Year', 'Month'])

    # Calcular o Total Volume Ano Móvel (12 meses móveis) por País
    df_sorted['Moving Year Total Volume'] = df_sorted.groupby('Country')['Box 9L'].rolling(window=12, min_periods=1).sum().reset_index(0, drop=True)

    # Agrupar por País e Ano para ter a soma do volume móvel anual
    total_volume_ano_movel = df_sorted.groupby(['Country', 'Year'])['Moving Year Total Volume'].last().reset_index()

    # Criar o gráfico com o volume total por ano móvel
    fig_ano_movel = px.line(total_volume_ano_movel, x='Year', y='Moving Year Total Volume', title='Total Volume Ano Móvel',
                            color='Country')  # Define uma linha para cada país
    fig_ano_movel.update_xaxes(tickmode='linear')  # Define o modo de tick para linear

    # Atualizar layout do gráfico
    fig_ano_movel.update_layout(
        plot_bgcolor='DarkSeaGreen',
        paper_bgcolor='DarkSeaGreen',
        font_color='black'
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
        title='Total Volume YTD',
        markers=True  # Adiciona pontos na linha
)

    # Removendo a legenda
    fig_ytd.update_traces(showlegend=False)

    # Atualizando o layout do gráfico
    fig_ytd.update_xaxes(
        tickangle=90,
        tickvals=total_ytd['YearMonth'].dt.year.unique(),  # Definindo os ticks do eixo x como os anos únicos
        ticktext=total_ytd['YearMonth'].dt.year.unique()  # Definindo o texto do tick como os anos
    )

    fig_ytd.update_layout(
        plot_bgcolor='DarkSeaGreen',
        paper_bgcolor='DarkSeaGreen',
        font_color='black'
    )


    # Gráfico Total Volume Ano Calendário
    total_calendario = df_filtered.groupby('Year')['Box 9L'].sum().reset_index()
    fig_calendario = px.bar(total_calendario, x='Year', y='Box 9L', title='Total Volume Ano Calendário',
                            color_discrete_sequence=["#8B4513"])  # Marrom (SaddleBrown)
    
    fig_calendario.update_xaxes(tickmode='linear')  # Define o modo de tick para linear
    fig_calendario.update_layout(
        plot_bgcolor='DarkSeaGreen',
        paper_bgcolor='DarkSeaGreen',
        font_color='black'
    )

    # Gráfico Total Volume por País
    total_por_pais = df_filtered.groupby(['Year', 'Country'])['Box 9L'].sum().reset_index()
    
    fig_pais = px.bar(total_por_pais, x='Year', y='Box 9L', color='Country',
                      title='Total Volume por País ao Longo dos Anos',
                      labels={'Box 9L': 'Total Volume (9L)', 'Year': 'Ano'},
                      barmode='group')
    fig_pais.update_xaxes(tickmode='linear')  # Define o modo de tick para linear

    fig_pais.update_layout(
        plot_bgcolor='DarkSeaGreen',
        paper_bgcolor='DarkSeaGreen',
        font_color='black'
    )

   # Gráfico Total Volume por Ano
    total_volume_por_ano = df_filtered.groupby(['Year', 'Product'])['Box 9L'].sum().reset_index()
    fig_total_volume_ano = px.bar(
        total_volume_por_ano,
        x='Year',
        y='Box 9L',
        color='Product',
        title='Total Volume por Product',
        labels={'Box 9L': 'Total Volume', 'Year': 'Ano', 'Product': 'Produto'},
        barmode='group'
    )
    fig_total_volume_ano.update_xaxes(tickmode='linear')  # Define o modo de tick para linear
    
    fig_total_volume_ano.update_layout(
        plot_bgcolor='DarkSeaGreen',
        paper_bgcolor='DarkSeaGreen',
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
        title='Total Volume Brand',
        color='Fabricante Produtor',
        hole=0.4,  # Para criar o efeito de rosca
        color_discrete_sequence=cores_personalizadas  # Usando a paleta de cores personalizada
    )

    # Atualizando o layout do gráfico
    fig_volume_acima_5_percent.update_traces(textinfo='percent+label')
    fig_volume_acima_5_percent.update_layout(
        plot_bgcolor='DarkSeaGreen',
        paper_bgcolor='DarkSeaGreen',
        font_color='black'
    )

    # Retorna todos os gráficos
    return fig_ano_movel, fig_ytd, fig_calendario, fig_pais, fig_total_volume_ano, fig_volume_acima_5_percent

# Primeiro, garantir que a coluna 'Box 9L' seja do tipo numérico
df_data['Box 9L'] = pd.to_numeric(df_data['Box 9L'], errors='coerce')

# Agrupar por 'Type' e 'Fabricante Produtor' e somar o volume de vendas
volume_by_type_and_company = df_data.groupby(['Type', 'Fabricante Produtor'])['Box 9L'].sum().reset_index()
volume_by_type_and_company.rename(columns={'Box 9L': 'Total Volume'}, inplace=True)

# Definindo total_volume_company
total_volume_company = df_data.groupby('Fabricante Produtor')['Box 9L'].sum().reset_index()
total_volume_company.rename(columns={'Box 9L': 'Total Volume'}, inplace=True)

# Definindo total_volume_company_brand_label
total_volume_company_brand_label = df_data.groupby(['Fabricante Produtor', 'Type'])['Box 9L'].sum().reset_index()
total_volume_company_brand_label.rename(columns={'Box 9L': 'Total Volume'}, inplace=True)

# Transpondo as tabelas para que fiquem na horizontal
total_volume_company_brand_label_transposed = total_volume_company_brand_label.set_index(['Fabricante Produtor', 'Type']).T.reset_index()
total_volume_company_transposed = total_volume_company.set_index('Fabricante Produtor').T.reset_index()
volume_by_type_and_company_transposed = volume_by_type_and_company.set_index(['Type', 'Fabricante Produtor']).T.reset_index()

# Layout da página da Tabela
tabela_layout = html.Div([
    dbc.Row([
        # Barra lateral (Sidebar)
        dbc.Col(sidebar, width=3),

        # Primeira tabela
        dbc.Col([
            dbc.Card([
                dbc.CardHeader("Tabela 1 - Total Volume por Fabricante, Marca e Rótulo"),
                dbc.CardBody([
                    dash_table.DataTable(
                        id='tabela-1',
                        columns=[{'name': col, 'id': col} for col in total_volume_company_brand_label_transposed.columns],
                        data=total_volume_company_brand_label_transposed.to_dict('records'),
                        style_table={'height': '150px', 'width': '100%', 'overflowY': 'auto'},
                        style_cell={'textAlign': 'left', 'minWidth': '80px', 'maxWidth': '180px', 'whiteSpace': 'normal'},
                        style_data={'maxWidth': '180px', 'overflow': 'hidden', 'textOverflow': 'ellipsis'},  # Limitar a largura do conteúdo
                    )
                ])
            ], style={"margin": "10px"})
        ], sm=6),  # Primeira tabela

        # Segunda tabela
        dbc.Col([
            dbc.Card([
                dbc.CardHeader("Tabela 2 - Volume por Tipo e Fabricante Produtor"),
                dbc.CardBody([
                    dash_table.DataTable(
                        id='tabela-2',
                        columns=[{'name': col, 'id': col} for col in volume_by_type_and_company_transposed.columns],
                        data=volume_by_type_and_company_transposed.to_dict('records'),
                        style_table={'height': '150px', 'width': '100%', 'overflowY': 'auto'},
                        style_cell={'textAlign': 'left', 'minWidth': '80px', 'maxWidth': '180px', 'whiteSpace': 'normal'},
                        style_data={'maxWidth': '180px', 'overflow': 'hidden', 'textOverflow': 'ellipsis'},  # Limitar a largura do conteúdo
                    )
                ])
            ], style={"margin": "10px"})
        ], sm=2)  # Segunda tabela
    ]),

    dbc.Row([
        # Terceira tabela
        dbc.Col([
            dbc.Card([
                dbc.CardHeader("Tabela 3"),
                dbc.CardBody([
                    dash_table.DataTable(
                        id='tabela-3',
                        columns=[{'name': col, 'id': col} for col in df_data.columns],
                        data=total_volume_company_transposed.T.to_dict('records'),  # Transpondo a tabela df_data
                        style_table={'height': '200px', 'width': '100%', 'overflowY': 'auto'},
                        style_cell={'textAlign': 'left', 'minWidth': '80px', 'maxWidth': '180px', 'whiteSpace': 'normal'},
                        style_data={'maxWidth': '180px', 'overflow': 'hidden', 'textOverflow': 'ellipsis'},  # Limitar a largura do conteúdo
                    )
                ])
            ], style={"margin": "10px"})
        ], sm=2, className="offset-sm-3"),  # Terceira tabela

        # Quarta tabela
        dbc.Col([
            dbc.Card([
                dbc.CardHeader("Tabela 4"),
                dbc.CardBody([
                    dash_table.DataTable(
                        id='tabela-4',
                        columns=[{'name': col, 'id': col} for col in df_data.columns],
                        data=df_data.head(10).T.to_dict('records'),  # Transpondo a tabela df_data
                        style_table={'height': '150px', 'width': '100%', 'overflowY': 'auto'},
                        style_cell={'textAlign': 'left', 'minWidth': '80px', 'maxWidth': '180px', 'whiteSpace': 'normal'},
                        style_data={'maxWidth': '180px', 'overflow': 'hidden', 'textOverflow': 'ellipsis'},  # Limitar a largura do conteúdo
                    )
                ])
            ], style={"margin": "10px"})
        ], sm=2)  # Quarta tabela
    ])
], style={"margin-left": "240px"})  # Ajuste a margem para alinhar com a barra lateral



# Adiciona o layout da tabela à aplicação Dash
@app_dash.callback(
    Output('page-content', 'children'),
    Input('url', 'pathname')
)
def display_page(pathname):
    if pathname == '/tabela':
        return tabela_layout  # Retorna o layout da tabela quando a URL corresponder
    elif pathname == '/dashboard':
        return html.Div([
            html.H3('Este é o Dashboard'),
            # Adicione o conteúdo do Dashboard aqui
        ])
    else:
        return content

# Rota Flask para a tabela
@app.route('/tabela')
def tabela():
    return render_template(
    'tabela.html',
    total_volume_company_brand_label_transposed=total_volume_company_brand_label_transposed,
    volume_by_type_and_company_transposed=volume_by_type_and_company_transposed,
    df_data=df_data
)



# Rota para a página Home
@app.route('/home')
def home():
    return render_template('home.html')  # arquivo 'home.html'

# Rota para a página de login
@app.route('/login', methods=['GET', 'POST'])
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

# Rota para a página de registro
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        # Coletando os dados do formulário
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
            "password": hashed_password.decode('utf-8')
        })

        return "Registration complete! Now log in."

    return render_template('register.html')

@app.route('/recover_password', methods=['GET', 'POST'])
def recover_password():
    # Lógica para recuperação de senha
    if request.method == 'POST':
        # Aqui você processaria a recuperação de senha
        email = request.form.get('email')
        # Verifique se o email está no banco de dados e envie um email de recuperação.
        return "Recovery email sent!"

    return render_template('recover_password.html')

@app.route('/logout')
def logout():
    session.pop('email', None)  # Remover a sessão do usuário
    return redirect('/login')


   

if __name__ == '__main__':
    app.run(debug=True)