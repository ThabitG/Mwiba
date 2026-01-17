import os, asyncio, threading
from metaapi_cloud_sdk import MetaApi
from http.server import BaseHTTPRequestHandler, HTTPServer

# ================== NEW AUTHENTICATION ==================
META_API_TOKEN = "eyJhbGciOiJSUzUxMiIsInR5cCI6IkpXVCJ9.eyJfaWQiOiIyOWU2NGU0YjYzNWE2MTkyODNjY2U5Mjc1M2ZhYWQ5OCIsImFjY2Vzc1J1bGVzIjpbeyJpZCI6InRyYWRpbmctYWNjb3VudC1tYW5hZ2VtZW50LWFwaSIsIm1ldGhvZHMiOlsidHJhZGluZy1hY2NvdW50LW1hbmFnZW1lbnQtYXBpOnJlc3Q6cHVibGljOio6KiJdLCJyb2xlcyI6WyJyZWFkZXIiXSwicmVzb3VyY2VzIjpbImFjY291bnQ6JFVTRVJfSUQkOmZhNTQ4ZGI3LTA4YjctNGY4YS1hY2E5LWIwYjUyODBhZjY5NCJdfSx7ImlkIjoibWV0YWFwaS1yZXN0LWFwaSIsIm1ldGhvZHMiOlsibWV0YWFwaS1hcGk6cmVzdDpwdWJsaWM6KjoqIl0sInJvbGVzIjpbInJlYWRlciIsIndyaXRlciJdLCJyZXNvdXJjZXMiOlsiYWNjb3VudDokVVNFUl9JRCQ6ZmE1NDhkYjctMDhiNy00ZjhhLWFjYTktYjBiNTI4MGFmNjk0Il19LHsiaWQiOiJtZXRhYXBpLXJwYy1hcGkiLCJtZXRob2RzIjpbIm1ldGFhcGktYXBpOndzOnB1YmxpYzoqOioiXSwicm9sZXMiOlsicmVhZGVyIiwid3JpdGVyIl0sInJlc291cmNlcyI6WyJhY2NvdW50OiRVU0VSX0lEJDpmYTU0OGRiNy0wOGI3LTRmOGEtYWNhOS1iMGI1MjgwYWY2OTQiXX0seyJpZCI6Im1ldGFhcGktcmVhbC10aW1lLXN0cmVhbWluZy1hcGkiLCJtZXRob2RzIjpbIm1ldGFhcGktYXBpOndzOnB1YmxpYzoqOioiXSwicm9sZXMiOlsicmVhZGVyIiwid3JpdGVyIl0sInJlc291cmNlcyI6WyJhY2NvdW50OiRVU0VSX0lEJDpmYTU0OGRiNy0wOGI3LTRmOGEtYWNhOS1iMGI1MjgwYWY2OTQiXX0seyJpZCI6Im1ldGFzdGF0cy1hcGkiLCJtZXRob2RzIjpbIm1ldGFzdGF0cy1hcGk6cmVzdDpwdWJsaWM6KjoqIl0sInJvbGVzIjpbInJlYWRlciJdLCJyZXNvdXJjZXMiOlsiYWNjb3VudDokVVNFUl9JRCQ6ZmE1NDhkYjctMDhiNy00ZjhhLWFjYTktYjBiNTI4MGFmNjk0Il19LHsiaWQiOiJyaXNrLW1hbmFnZW1lbnQtYXBpIiwibWV0aG9kcyI6WyJyaXNrLW1hbmFnZW1lbnQtYXBpOnJlc3Q6cHVibGljOio6KiJdLCJyb2xlcyI6WyJyZWFkZXIiXSwicmVzb3VyY2VzIjpbImFjY291bnQ6JFVTRVJfSUQkOmZhNTQ4ZGI3LTA4YjctNGY4YS1hY2E5LWIwYjUyODBhZjY5NCJdfV0sImlnbm9yZVJhdGVMaW1pdHMiOmZhbHNlLCJ0b2tlbklkIjoiMjAyMTAyMTMiLCJpbXBlcnNvbmF0ZWQiOmZhbHNlLCJyZWFsVXNlcklkIjoiMjllNjRlNGI2MzVhNjE5MjgzY2NlOTI3NTNmYWFkOTgiLCJpYXQiOjE3Njg2NTI3OTAsImV4cCI6MTc3NjQyODc5MH0.N-h8idvah5EGfIw6hOehU6naU5Fy7EyTGjMEDounROIqqWH1OJQSa0b8YX-LlfbYzjgo1rKbBs4aRFrqGvm7Mu3LbiX72wl-uFe1CnKj9Ap6ayTIkZob58cUK0vdvvlraE-jncDaFetdqpQqbTCWgpJrQpOXYrI0vqJdQ4nzPC8uf-x1UBK-5HD5sMg76SuE27SaliqMjIhVuIe5_esmgCoGiNtcGfZ6N7LAUngUZDiT7ndyRGygFJjsO1ljf6AeTEAAD3SDiDM_OV39vnGcvCAfVDOPml0f81vZXvk5W5zgtJhrkeoXs_kQ6dKCVwspm1jNClrP968iO_kuOs8OHYXPVWqxc63wyvPq26urmdvWPPgi6rMJPGWiFhkTKQTVQcWGUAzHqCQQft-Cn3_lrOhIpDJCydQXdBp0gD4qb_4zE9ooqJDjHK8RC3kwKy7e3bJKVWdE5-CbDV1vWoEUqxHtYd2gzQTwRZcXrsKxRWbbXqEHDq3y2fCwopqDsEPEMPdqmnSOt1rL4i9FZIX119ts6fZCyN-5qsoRQHvQXKhCNvz68XZmbPNeC15jUTlUd2nqQWH-3lcLlbrY8E5HwHN2Dny4fW8nw2t2on81eOW-ohhUW6ufxYL4-UI3UGMeDVJVGlZdplJEvfzRbSv11nkjGac3RykXc-GKxvHh1f0"
ACCOUNT_ID = "fa548db7-08b7-4f8a-aca9-b0b5280af694"

async def main():
    api = MetaApi(META_API_TOKEN)
    try:
        print("--- 🔄 JARIBIO LA KUUNGANISHA UPYA ---")
        acc = await api.metatrader_account_api.get_account(ACCOUNT_ID)
        await acc.wait_connected()
        conn = acc.get_rpc_connection()
        await conn.connect()
        await conn.wait_synchronized()
        
        # Pata taarifa za akaunti kama uthibitisho
        info = await conn.get_account_information()
        print(f"--- ✅ HONGERA! BOT IMEWAKA! ---")
        print(f"Akaunti: {info['name']} | Salio: {info['balance']} {info['currency']}")
        
        while True:
            # Hapa bot itaendelea kuangalia soko (Health Check Only for now)
            await asyncio.sleep(60)
            
    except Exception as e:
        print(f"--- ❌ KOSA LA KIUFUNDI: {e} ---")

if __name__ == "__main__":
    # VPS keep-alive server
    threading.Thread(target=lambda: HTTPServer(('0.0.0.0', 8080), type('H', (BaseHTTPRequestHandler,), {'do_GET': lambda s: (s.send_response(200), s.end_headers())})).serve_forever(), daemon=True).start()
    asyncio.run(main())
