#!/bin/bash

# 스크립트 디렉토리로 이동
cd "$(dirname "$0")"

# 환경 변수 로드
export $(cat .env | xargs)

# 특정 날짜 지정 (선택사항)
# 사용법: ./run_scrum.sh 2026-01-27
if [ -n "$1" ]; then
    export TARGET_DATE="$1"
    echo "📅 지정된 날짜: $TARGET_DATE"
fi

# 가상환경 활성화 및 스크립트 실행
source venv/bin/activate
python scrum_report.py

# 로그 파일에 실행 기록 저장 (선택사항)
echo "[$(date)] Scrum report executed" >> scrum_report.log