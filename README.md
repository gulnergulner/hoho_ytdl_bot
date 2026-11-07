# hoho_ytdl_bot

개인 텔레그램 봇에 유튜브 영상 링크를 보내면 Synology NAS에서 MP3로 변환합니다. 지정한 사용자와의 개인 대화만 처리합니다. 49,000,000바이트 이하 파일은 텔레그램으로 전송하며, 모든 파일은 `data/telegram/`에 보관합니다. 다운로드 권한이 있는 영상에 사용하고 저작권과 이용 약관을 확인하세요.

이 저장소는 manna2와 별도입니다. 향후 manna2 연동은 계획이며 현재 API, 공유 작업 큐 또는 자동 게시는 구현되어 있지 않습니다.

## 설치

Container Manager와 Docker Compose가 필요합니다. 실제 볼륨 경로 및 접근 권한은 NAS에서 확인하세요. 아래 경로는 예시입니다.

1. [BotFather](https://t.me/BotFather)에서 봇을 만들고 `/start`를 본인 봇에 보냅니다. 토큰과 숫자 사용자 ID가 필요합니다. ID는 봇 실행 전에 다음 명령에서 본인 메시지의 `from.id`로 확인할 수 있습니다. 토큰은 채팅이나 Git에 올리지 마세요.

```sh
python3 -c 'import getpass,json,urllib.request; t=getpass.getpass("Bot token: "); print(json.dumps(json.load(urllib.request.urlopen("https://api.telegram.org/bot"+t+"/getUpdates")), ensure_ascii=False, indent=2))'
```

2. 저장소는 비공개이므로 NAS에서 GitHub 인증(SSH 키 또는 액세스 토큰)이 필요합니다. 저장소를 NAS에 복제하고 설정합니다. **기존 서비스가 있는 경로에 바로 복제하거나 덮어쓰지 마세요.**

```sh
git clone https://github.com/gulnergulner/hoho_ytdl_bot.git /volume4/docker/hoho_ytdl_bot-new
cd /volume4/docker/hoho_ytdl_bot-new
mkdir -p data/telegram state/telegram
sudo chown 10001:10001 data/telegram state/telegram
cp .env.example .env
chmod 600 .env
```

`.env`에 `TELEGRAM_BOT_TOKEN`과 `TELEGRAM_USER_ID`를 설정한 다음 실행합니다.

```sh
sudo docker compose up -d --build
sudo docker compose ps
sudo docker compose logs --tail 50
```

컨테이너는 외부로 polling하므로 NAS 인바운드 포트가 필요 없습니다. 같은 토큰으로 다른 프로세스를 동시에 실행하거나 webhook과 함께 사용하지 마세요. 파일은 자동 삭제되지 않습니다. 로그인 필요 영상과 유튜브 차단은 동작하지 않을 수 있습니다.

## 업데이트

설치 폴더에서 `git pull --ff-only`로 새 코드를 받은 다음 `sudo docker compose up -d --build`로 교체합니다. `.env`, `data/`, `state/`는 Git 추적 대상이 아닙니다. NAS에서 수정한 코드가 있으면 먼저 변경 내용을 확인하세요. 중단 중 요청이 다시 처리되거나 알림이 중복될 수 있습니다.

기존 NAS의 `hoho_ytdl_bot`이 이 코드와 동일한지 확인하지 않았으므로 기존 컨테이너나 파일을 자동으로 교체하지 않습니다. 기존 파일과 설정을 확인한 뒤 별도로 이전해야 합니다. Docker 빌드 및 실제 Telegram/YouTube/NAS 통합은 아직 검증하지 않았습니다.

## 테스트

```sh
python3 -m unittest -v
```
