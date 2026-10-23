<<<<<<< HEAD
# Reino Persistente — protótipo web

Protótipo inicial de um jogo de administração de recursos e caça automática, inspirado em conceitos de sandbox e progressão, com identidade própria.

## O que já funciona
- Painel medieval no navegador.
- Banco de dados SQLite criado automaticamente (`game.db`).
- Recursos iniciais e sistema de coleta temporizada: cada atividade entrega um lote fixo quando termina.
- Cinco recursos coletáveis com três níveis provisórios por recurso; níveis superiores demoram mais e aumentam a qualidade média do estoque.
- Até duas coletas simultâneas, persistidas no SQLite e concluídas pelo servidor mesmo se o navegador estiver fechado.
- Construção de serraria e forno de fundição.
- Filas de produção com tempo real, processadas no servidor.
- Expedições de caça com combate automático e recompensas.
- Derrota sem perda permanente de itens ou habilidades.
- Registro de eventos e progressão inicial de caça.

## Requisitos
- Windows 10/11
- Python 3.11 ou mais recente
- Conexão à internet na primeira execução para instalar Flask e carregar as fontes da interface. O jogo em si roda localmente depois da instalação.

## Como executar no Windows
1. Extraia o ZIP para uma pasta, por exemplo `C:\Jogos\ReinoPersistente`.
2. Instale Python 3.11+ em https://www.python.org/downloads/ e marque **Add Python to PATH**.
3. Dê dois cliques em `run.bat`.
4. Aguarde a instalação das dependências.
5. Abra `http://127.0.0.1:5000` no navegador.
6. Para encerrar, volte à janela preta e pressione `Ctrl+C`.

## Banco de dados
O SQLite `game.db` será criado automaticamente na primeira execução e guardará o progresso. Ao iniciar esta versão atualizada, a tabela de coletas é criada automaticamente sem apagar as tabelas ou o progresso existente. Faça uma cópia de segurança de `game.db` antes de atualizar. Para reiniciar o jogo, feche o servidor e apague `game.db`; na próxima execução, uma propriedade nova será criada.

## Limitações conhecidas desta versão
- É um protótipo local, não um MMORPG público/multijogador ainda.
- O mundo e o banco de dados ficam neste computador.
- Ainda não há contas, login, chat, mercado entre jogadores, comércio real, sincronização multiplayer ou proteção de produção para internet pública.
- Os níveis de coleta são provisórios: a qualidade é agregada à qualidade média do recurso no inventário; ainda não existem estoques separados para cada qualidade.
- Tempos e quantidades de coleta são valores iniciais de teste e devem ser rebalanceados conforme as receitas e a economia forem desenvolvidas.
- Valores de balanceamento, tempos e recompensas são provisórios.
- O servidor Flask incluído é para desenvolvimento local. Não exponha diretamente à internet.

## Próximas etapas
1. Contas e autenticação segura.
2. Servidor de produção e banco PostgreSQL para mundo compartilhado.
3. Transações atômicas de mercado e inventário.
4. Sistema completo de qualidade de materiais e equipamentos.
5. Receitas, árvore tecnológica, mais construções e regiões.
6. Hospedagem, monitoramento, backup e proteção contra trapaças.

## Estrutura
```text
reino_persistente/
├── app.py
├── game.db            # criado automaticamente ao iniciar
├── requirements.txt
├── run.bat
├── README.md
├── templates/
│   └── index.html
└── static/
    ├── style.css
    └── app.js
```
=======
# Reino-Persistente
Projeto de jogo de página http
>>>>>>> 533e978146de79f69403ad404f9c747043a3fe89
