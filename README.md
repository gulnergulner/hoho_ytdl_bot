# hoho_ytdl_bot

개인 텔레그램 봇에 유튜브 영상 링크를 보내면 Synology NAS에서 MP3로 변환합니다. 지정한 사용자와의 개인 대화만 처리합니다. 모든 파일은 `data/telegram/`에 영상 제목과 ID로 보관하고 File Station 공유 링크를 텔레그램으로 전송합니다. 파일을 텔레그램에 업로드하지 않습니다. 다운로드 권한이 있는 영상에 사용하고 저작권과 이용 약관을 확인하세요.

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

`.env`에 텔레그램 설정과 DSM 설정을 입력합니다. `DSM_URL`은 컨테이너에서 접근 가능한 DSM HTTPS 주소로, 인증서가 해당 호스트명과 일치하고 신뢰되어야 합니다. `DSM_ACCOUNT`와 `DSM_PASSWORD`는 File Station 및 다운로드 폴더 접근과 공유 링크 생성 권한이 있는 별도 DSM 계정의 자격 증명입니다. 2단계 인증이 필요한 계정은 이 방식으로 자동 로그인하지 못할 수 있습니다. `DSM_DOWNLOADS_PATH`는 File Station에서 보이는 경로로, 예를 들어 `/docker/hoho_ytdl_bot-new/data/telegram`입니다 (`/volume4` 제외). Compose의 볼륨 경로와 정확히 같은 폴더여야 합니다. 암호는 환경변수에 저장되므로 .env와 Docker 관리 권한을 제한하세요.

QuickConnect의 고급 설정에서 파일 공유를 활성화하면 File Station에서 외부 접속 가능한 `gofile.me` 링크를 생성할 수 있습니다. 링크는 내일 날짜에 만료되도록 요청하며 링크를 가진 사람은 접근할 수 있습니다. 실제 생성 URL과 만료 동작은 NAS에서 확인하세요. 원격 접속 주소와 DSM 내부 API 주소는 같을 필요가 없습니다.

설정 후 실행합니다.

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
