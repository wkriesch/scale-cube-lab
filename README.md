🏗️ **Laboratório Scale Cube: Microserviços & Sharding SQL**

Este repositório contém um ambiente experimental projetado para validar as três dimensões de escalabilidade do modelo Scale Cube (AKF Partners) utilizando tecnologias modernas de containerização e orquestração.

---

### 1. Visão Geral dos Eixos de Escalabilidade

- **Eixo X (Horizontal Scaling)**  
  Escalabilidade via replicação de instâncias. No Kubernetes, o `service-a` roda com múltiplas réplicas balanceadas.

- **Eixo Y (Functional Decomposition)**  
  Separação de responsabilidades e tecnologias de persistência:
  - PostgreSQL para usuários
  - Redis para sessões
  - MongoDB para auditoria

- **Eixo Z (Data Partitioning / Sharding)**  
  Particionamento físico de dados SQL. O roteamento para diferentes instâncias de banco de dados é decidido em tempo de execução via cabeçalho `X-Tenant-ID`.

---

### 2. Arquitetura Técnica

| Serviço       | Tecnologia               | Banco de Dados           | Porta Local | Papel                                  |
|---------------|--------------------------|--------------------------|-------------|----------------------------------------|
| Service A     | Python (FastAPI Async)   | PostgreSQL (Dual Shard)  | 8001        | Orquestrador e Router de Shards        |
| Service B     | Python (FastAPI)         | Redis                    | 8002        | Cache de Sessão volátil                |
| Service C     | Python (FastAPI)         | MongoDB                  | 8003        | Logs de Auditoria NoSQL                |

#### Infraestrutura de Bancos (Sharding)

- **Shard 1 (Default)**  
  Instância PostgreSQL dedicada para usuários padrão.

- **Shard 2 (Premium)**  
  Instância PostgreSQL dedicada para usuários premium.

---

### 3. Como Montar o Laboratório

#### Pré-requisitos

- Docker e Docker Compose
- Python 3.9+ (para rodar o script de stress)
- Bibliotecas Python:  

Bibliotecas Python: 
```bash
pip install requests httpx fastapi uvicorn psycopg2-binary
```

#### Passo 1: Estrutura de Pastas
```
├── docker-compose.yml
├── stress_test.py
├── service-a-users/
│   ├── main.py
│   └── Dockerfile
├── service-b-session/
│   ├── main.py
│   └── Dockerfile
└── service-c-audit/
    ├── main.py
    └── Dockerfile
```
#### Passo 2: Execução

Suba todo o ecossistema com um único comando:

```bash
docker-compose up --build -d
```

---

### 4. Roteiro de Testes e Validação

#### A. Teste de Carga e Sharding (Eixo X + Z)

O script `stress_test.py` simula concorrência e envia cabeçalhos que forçam o uso de diferentes bancos de dados.

```bash
python3 stress_test.py
```

**O que observar:**

- Requisições com ID par devem ser direcionadas ao `postgres-db-shard2`.
- Requisições com ID ímpar devem ser direcionadas ao `postgres-db`.

#### B. Prova Real de Particionamento (SQL)

Após o teste, execute os comandos abaixo para confirmar que os dados foram fisicamente separados:

# Contagem no Shard 1 (Default)
```bash
docker exec -it scale-cube-lab-postgres-db-1 psql -U postgres -d users_db -c "SELECT count(*) FROM users;"
```
# Contagem no Shard 2 (Premium)
```bash
docker exec -it scale-cube-lab-postgres-db-shard2-1 psql -U postgres -d users_db -c "SELECT count(*) FROM users;"
```

Cada banco deve conter exatamente 50% da carga total enviada.

#### C. Verificação de Propagação (Eixo Y)

Valide se o Service A notificou corretamente os outros sistemas:

- **Redis (Sessões):**

Redis (Sessões): 
```bash
docker exec -it <container_redis> redis-cli KEYS "*"
```

- **MongoDB (Auditoria):**  
Acesse `http://localhost:8003/audit` no navegador.

---

### 5. Recuperação de Desastres e Manutenção Isolada

Uma das maiores vantagens do Eixo Z é o isolamento de falhas.

#### Simular Falha

Derrube o Shard 1:
```bash
docker stop scale-cube-lab-postgres-db-1.
```

#### Testar

Rode o `stress_test.py`.

#### Resultado Esperado

- Requisições para `X-Tenant-ID: default` falharão com erro `503`/`500`.
- Requisições para `X-Tenant-ID: premium` continuarão funcionando normalmente, provando que um shard não afeta o outro.


