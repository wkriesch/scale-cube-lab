# Usa uma imagem base leve do Python
FROM python:3.9-slim

# Define diretório de trabalho dentro do container
WORKDIR /app

# Copia primeiro os requisitos (para aproveitar o cache do Docker)
COPY requirements.txt .

# Instala as dependências
# --no-cache-dir mantém a imagem pequena
RUN pip install --no-cache-dir -r requirements.txt

# Copia o código fonte
COPY main.py .

# Expõe a porta (apenas documentação, quem define a porta real é o comando de run)
EXPOSE 8000

# Comando para iniciar a aplicação
# host 0.0.0.0 é crucial para rodar dentro de container
ENV OTEL_SERVICE_NAME=service-c-audit
CMD ["opentelemetry-instrument", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]