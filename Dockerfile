FROM python:3.11-slim

# Sem isso, os prints do main.py ficam presos no buffer do Python e não
# aparecem em "docker compose logs" / "docker compose up" até o processo
# terminar, dá a falsa impressão de que nada está acontecendo.
ENV PYTHONUNBUFFERED=1

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Porta do Streamlit.
EXPOSE 8501

# Roda o setup do banco (main.py) e, se der certo, sobe o dashboard.
CMD sh -c "python main.py && \
    streamlit run app.py \
    --server.port=8501 \
    --server.address=0.0.0.0 \
    --server.headless=true"