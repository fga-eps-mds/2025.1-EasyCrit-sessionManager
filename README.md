# 2025.1-EasyCrit-sessionManager

## Sessions Manager
Esse repositório contém o código fonte do módulo de gerenciamento de sessões do sistema EasyCrit. O módulo é responsável por gerenciar as sessões de RPG, permitindo a criação, edição e exclusão de sessões. Além disso é responsavel pelo gerenciamento do chat.

## Executar o projeto
### Requisitos
- Docker
- Docker Compose

## Inicializar o projeto
1. Clone o repositório:
```bash
git clone https://github.com/fga-eps-mds/2025.1-EasyCrit-sessionManager.git
cd 2025.1-EasyCrit-sessionManager
```
2. Crie um arquivo `.env` na raiz do projeto com as variáveis de ambiente necessárias.

3. É possível executar o projeto pelo Docker Compose presente no repositório de documentação do EasyCrit.
```bash
cd 2025.1-EasyCrit-docs
docker-compose up -d sessionManager
```

## Variáveis de ambiente
| Variável de ambiente | Descrição |
|----------------------|-----------|
| `SESSION_MANAGER_PORT` | Porta que o serviço irá rodar. |

## Documentação
É possível acessar a documentação do projeto através do Swagger, que está disponível na seguinte URL:
```
http://localhost:{AUTH_PORT}/docs
```
A documentação é gerada automaticamente a partir dos comentários do código, utilizando o Swagger UI. Para mais informações sobre como utilizar o Swagger, consulte a [documentação oficial](https://swagger.io/docs/).