# NGINX Access-Host-Proxy

```
nginx/
├── Dockerfile
├── nginx.conf
├── conf.d/
│   └── http-status.conf
└── stream.d/
    └── stream-proxy.conf
```



## Build

```bash
docker compose build --no-cache access-host-proxy
```

## Run

```bash
docker compose up -d access-host-proxy
```

## Test Configuration

```bash
docker exec -it access-host-proxy nginx -t
```

## Test status page

```bash
docker exec -it access-host-proxy curl http://localhost:8081/nginx_status
```
# 🔥 ** CẦN LÀM 3 LỆNH SAU**


```bash
find nginx -type f -exec dos2unix {} \;

docker compose build --no-cache access-host-proxy

docker compose up -d access-host-proxy
```

## Rồi test:

```bash
docker exec -it access-host-proxy nginx -t
docker exec -it access-host-proxy curl http://localhost:8081/nginx_status
```