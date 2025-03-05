# MD Wallet - Sistema de Autenticação

Este documento explica como funciona o sistema de autenticação do MD Wallet e como gerenciar usuários.

## Estrutura do Sistema

O sistema de autenticação utiliza:
- `streamlit-authenticator` para gerenciar login/logout
- Armazenamento de dados de usuário em arquivos JSON
- Senhas armazenadas de forma segura com hash bcrypt

## Arquivos e Diretórios Importantes

- `data/config.yaml`: Contém as credenciais dos usuários
- `data/users/`: Diretório onde os dados de cada usuário são armazenados
- `utils/user_data.py`: Funções para carregar/salvar dados de usuário
- `utils/generate_password_hash.py`: Utilitário para gerar hashes de senha

## Gerenciando Usuários

### Adicionar um Novo Usuário

1. Gere um hash para a senha do novo usuário:
   ```
   python utils/generate_password_hash.py
   ```

2. Adicione o usuário ao arquivo `data/config.yaml`:
   ```yaml
   credentials:
     usernames:
       novousuario:
         email: novousuario@exemplo.com
         name: Novo Usuário
         password: $2b$12$...  # Use o hash gerado no passo anterior
   ```

### Redefinir Senha de um Usuário Existente

1. Gere um novo hash de senha usando o utilitário
2. Substitua o hash de senha existente no arquivo `data/config.yaml`

### Remover um Usuário

1. Remova a entrada do usuário do arquivo `data/config.yaml`
2. Opcionalmente, remova os dados do usuário de `data/users/nome_do_usuario/`

## Estrutura de Dados do Usuário

Cada usuário tem três arquivos de dados em `data/users/nome_do_usuario/`:

- `transactions.json`: Transações atuais
- `history.json`: Histórico de relatórios submetidos
- `settings.json`: Configurações do usuário, incluindo datas do período atual

## Funcionamento

1. Quando um usuário faz login, seus dados são carregados dos arquivos em `data/users/nome_do_usuario/`
2. Durante o uso da aplicação, os dados são mantidos na sessão do Streamlit
3. Quando transações são adicionadas ou relatórios são submetidos, os dados são salvos automaticamente

## Segurança

- As senhas são armazenadas com hash bcrypt (não em texto simples)
- Cada usuário só tem acesso aos seus próprios dados
- Os cookies de autenticação são criptografados e expiram após 30 dias por padrão 