# Stylish Spell Battle

## TODO
- [ ] ダメージ計算ロジックの微修正

## Boot up locally
```sh
docker compose up --build
```

## Deploy to Google Cloud
```sh
export CLOUDSDK_PYTHON=/Users/nttcom/.anyenv/envs/pyenv/versions/3.9.10/bin/python3
gcloud builds submit --tag gcr.io/teak-flash-436008-q2/stylish-spells
gcloud run deploy --image gcr.io/teak-flash-436008-q2/stylish-spells --platform managed --region asia-northeast1 --set-env-vars REDISHOST=10.155.126.3,REDISPORT=6379
```