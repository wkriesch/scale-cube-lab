import requests
import random
import time
from concurrent.futures import ThreadPoolExecutor

# Configurações
BASE_URL = "http://localhost:8001/users"
TOTAL_REQS = 100
CONCURRENCY = 10

session = requests.Session()
adapter = requests.adapters.HTTPAdapter(pool_connections=20, pool_maxsize=20)
session.mount("http://", adapter)

def run_task(i):
    # Alterna entre os tenants para testar o Sharding (Eixo Z)
    tenant = "premium" if i % 2 == 0 else "default"
    payload = {"username": f"stress_user_{i}", "email": f"user{i}@test.com"}
    headers = {"X-Tenant-ID": tenant}
    
    try:
        start = time.time()
        resp = session.post(BASE_URL, json=payload, headers=headers, timeout=5)
        latency = time.time() - start
        
        if resp.status_code == 200:
            data = resp.json()
            return f"✅ [ID {i}] Shard: {data.get('shard_db')} | {latency:.3f}s"
        return f"❌ [ID {i}] Status: {resp.status_code}"
    except Exception as e:
        return f"🔥 [ID {i}] Erro: {str(e)[:50]}"

def main():
    print(f"🚀 Iniciando Teste de Sharding SQL em {BASE_URL}")
    print(f"Enviando {TOTAL_REQS} requisições (50% Default / 50% Premium)...\n")
    
    start_time = time.time()
    with ThreadPoolExecutor(max_workers=CONCURRENCY) as executor:
        results = list(executor.map(run_task, range(TOTAL_REQS)))

    # Relatório
    duration = time.time() - start_time
    success = [r for r in results if "✅" in r]
    
    for r in results[:10]: print(r) # Printa os 10 primeiros
    print("...")
    print(f"\n📊 RESULTADOS:")
    print(f"Sucesso: {len(success)}/{TOTAL_REQS}")
    print(f"Tempo Total: {duration:.2f}s")
    print(f"Vazão: {len(success)/duration:.2f} req/s")

if __name__ == "__main__":
    main()