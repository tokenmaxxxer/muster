#!/usr/bin/env bash
# 워커를 컨테이너로 실행한다. 어댑터 표는 이 스크립트만 부르면 되고,
# 라우터는 여전히 컨테이너를 모른다.
#
#   run.sh <profile> <명령...>        프롬프트는 stdin 으로 그대로 통과한다
#
# 컨테이너를 쓰는 첫 번째 이유는 성능도 재현성도 아니고 **env 가 기본 차단**이라는
# 것이다. 호스트 실행에서는 환경변수가 기본 상속이라, 자격증명 이름을 하나 빠뜨린
# 거부목록은 그 자리에서 뚫린다. docker run 은 -e 로 명시한 것만 들어간다.
set -euo pipefail

profile=${1:?profile 필요 (reader|builder|prober)}; shift

: "${WORK:?}" "${OUT:?}"
IMAGE=${ORCH_IMAGE:-tokenmaxxxer/worker:latest}
CREDS="$HOME/.claude/.credentials.json"

# 프로파일별 마운트. 계약 경로는 컨테이너 안에서 항상 /work 와 /out 이다.
case "$profile" in
  builder) mounts=(-v "$WORK:/work" -v "$OUT:/out") ;;
  reader)  mounts=(-v "$WORK:/work:ro" -v "$OUT:/out") ;;   # 워크트리 읽기 전용
  prober)  mounts=(-v "$WORK:/work" -v "$OUT:/out") ;;
  *) echo "알 수 없는 프로파일: $profile" >&2; exit 2 ;;
esac

# Anthropic 자격증명만 넣는다. GitHub 자격증명·gh 설정·SSH agent 는 넣지 않는다 —
# 게시는 라우터가 하므로 워커에게 GitHub 로 나갈 수단이 있으면 안 된다.
[ -r "$CREDS" ] || { echo "Anthropic 자격증명 없음: $CREDS" >&2; exit 3; }

exec docker run --rm -i \
  --user "$(id -u):$(id -g)" \
  "${mounts[@]}" \
  -v "$CREDS:/home/worker/.claude/.credentials.json:ro" \
  -w /work \
  -e HOME=/home/worker \
  -e OUT=/out -e WORK=/work \
  -e ISSUE="${ISSUE:-}" -e TITLE="${TITLE:-}" -e PR="${PR:-}" \
  --security-opt no-new-privileges \
  "$IMAGE" "$@"
