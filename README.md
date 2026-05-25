# CoinGecko Analytics Pipeline

Pipeline local de analytics engineering para coletar dados da API CoinGecko, armazenar em PostgreSQL, transformar com dbt e consumir no Power BI.

## Stack

- Docker Compose
- Apache Airflow
- PostgreSQL
- dbt Core + dbt-postgres
- Power BI

## Arquitetura

O Airflow orquestra uma DAG diária que:

1. Coleta o ranking de moedas via CoinGecko.
2. Coleta histórico diário das principais moedas.
3. Grava os dados brutos no schema `raw`.
4. Executa o dbt para criar modelos `staging` e `marts`.

O Power BI pode se conectar diretamente ao PostgreSQL local e consumir as tabelas finais do schema `marts`.

## Estrutura

```text
airflow/dags/   DAGs do Airflow
src/            Cliente CoinGecko e loaders Python
dbt/            Modelos, sources, macros e testes dbt
scripts/        Scripts auxiliares
```

## Como Rodar

Crie o arquivo `.env`:

```bash
cp .env.example .env
```

Preencha sua chave da CoinGecko:

```env
COINGECKO_API_KEY=sua_chave_aqui
COINGECKO_API_TIER=demo
```

Suba a stack:

```bash
docker compose up --build airflow-init
docker compose up --build -d
```

Acesse o Airflow:

```text
http://localhost:8080
```

Credenciais padrão:

```text
admin / admin
```

Dispare a DAG manualmente:

```bash
docker compose run --rm airflow-cli airflow dags trigger coingecko_daily_pipeline
```

## Modelos Finais

Principais tabelas para análise:

- `marts.dim_coins`
- `marts.fct_latest_market_snapshot`
- `marts.fct_coin_market_daily`

## Power BI

Conexão PostgreSQL:

```text
Host: localhost
Port: 5433
Database: crypto_warehouse
User: analytics
Password: analytics
```

## Comandos Úteis

```bash
docker compose ps
docker compose run --rm --entrypoint /bin/bash dbt -lc "/home/airflow/dbt-venv/bin/dbt debug"
docker compose run --rm --entrypoint /bin/bash dbt -lc "/home/airflow/dbt-venv/bin/dbt build"
docker compose down
```

## Observação

Use `.env.example` como referência de configuração.
