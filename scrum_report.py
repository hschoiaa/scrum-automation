#!/usr/bin/env python3
"""
JIRA 티켓을 분석하여 Confluence 위키에 스크럼 보고서를 자동으로 생성하는 스크립트
"""

import os
import json
import requests
from datetime import datetime

# 환경 변수에서 설정 가져오기
JIRA_EMAIL = os.environ.get('JIRA_EMAIL')
JIRA_TOKEN = os.environ.get('JIRA_TOKEN')
WIKI_PARENT_PAGE_ID = os.environ.get('WIKI_PARENT_PAGE_ID', '291243949')

JIRA_BASE_URL = "https://musinsa-oneteam.atlassian.net"
WIKI_BASE_URL = f"{JIRA_BASE_URL}/wiki"

# 날짜 정보
TODAY = datetime.now().strftime('%Y-%m-%d')
MONTH = datetime.now().strftime('%Y-%m')
YEAR = datetime.now().strftime('%Y')
MONTH_NUM = datetime.now().strftime('%m')

print(f"📅 날짜: {TODAY}")
print(f"📁 월: {MONTH}")

def api_request(method, url, json_data=None):
    """API 요청 헬퍼 함수"""
    auth = (JIRA_EMAIL, JIRA_TOKEN)
    headers = {"Content-Type": "application/json"}

    if method == "GET":
        response = requests.get(url, auth=auth, headers=headers)
    elif method == "POST":
        response = requests.post(url, auth=auth, headers=headers, json=json_data)
    else:
        raise ValueError(f"Unsupported method: {method}")

    return response.json()

def get_jira_tickets():
    """JIRA 티켓 조회"""
    print("🔍 JIRA 티켓 조회 중...")

    jql = "assignee=currentUser() AND updated>=-7d ORDER BY updated DESC"
    url = f"{JIRA_BASE_URL}/rest/api/3/search/jql"
    params = f"?jql={requests.utils.quote(jql)}&maxResults=50&fields=summary,status,description,updated,created,comment"

    response = api_request("GET", url + params)

    print(f"  ✅ {len(response.get('issues', []))}개 티켓 조회됨")
    return response.get('issues', [])

def get_confluence_pages():
    """Confluence 페이지 조회"""
    print("📄 Confluence 페이지 조회 중...")

    # 최근 7일간 생성/수정한 페이지 조회
    cql = "contributor=currentUser() AND lastModified >= now('-7d') ORDER BY lastModified DESC"
    url = f"{WIKI_BASE_URL}/rest/api/content/search"
    params = f"?cql={requests.utils.quote(cql)}&limit=20&expand=history"

    response = api_request("GET", url + params)

    print(f"  ✅ {len(response.get('results', []))}개 페이지 조회됨")
    return response.get('results', [])

def analyze_tickets(issues, pages=[]):
    """티켓 및 Confluence 페이지 분석 및 분류"""
    print("📊 티켓 분석 중...")

    in_progress = []
    ktlo_items = []

    # Confluence 페이지 처리
    for page in pages:
        page_id = page['id']
        title = page['title']

        # 자동 생성된 스크럼 보고서 페이지는 제외
        if title.startswith('202') and len(title) == 10:  # YYYY-MM-DD 형식
            continue

        # 업데이트 날짜 추출 (안전하게 처리)
        try:
            if 'history' in page and 'lastUpdated' in page['history']:
                updated = page['history']['lastUpdated']['when'][:10]
            elif 'lastModified' in page:
                updated = page['lastModified'][:10]
            else:
                updated = TODAY
        except:
            updated = TODAY

        page_url = f"{WIKI_BASE_URL}{page['_links']['webui']}"

        item = {
            'key': f'WIKI-{page_id}',
            'summary': f'📄 {title}',
            'status': 'Wiki',
            'updated': updated,
            'url': page_url,
            'comment': None
        }
        in_progress.append(item)

    # JIRA 티켓 처리
    for issue in issues:
        key = issue['key']
        summary = issue['fields']['summary']
        status = issue['fields']['status']['name']
        updated = issue['fields']['updated'][:10]

        # 댓글 추출
        comments = issue['fields'].get('comment', {}).get('comments', [])
        recent_comment = None

        if comments:
            last_comment = comments[-1]
            author = last_comment['author']['displayName']
            created = last_comment['created'][:10]
            body_text = ''

            if 'body' in last_comment:
                body = last_comment['body']
                if isinstance(body, dict) and 'content' in body:
                    for content in body['content']:
                        if content.get('type') == 'paragraph' and 'content' in content:
                            for text_node in content['content']:
                                if text_node.get('type') == 'text':
                                    body_text += text_node.get('text', '')

            if body_text and '자동메시지' not in body_text:
                recent_comment = {
                    'author': author.split('/')[0],
                    'date': created,
                    'text': body_text[:150]
                }

        item = {
            'key': key,
            'summary': summary,
            'status': status,
            'updated': updated,
            'comment': recent_comment
        }

        # 분류
        if status in ['In Progress', 'SUGGESTED']:
            in_progress.append(item)
        elif status == '완료' and any(word in summary for word in ['확인', '문의', '데이터', '요청']):
            ktlo_items.append(item)

    print(f"  ✅ 진행중: {len(in_progress)}개, KTLO: {len(ktlo_items)}개")
    return in_progress, ktlo_items

def generate_html(in_progress, ktlo_items):
    """HTML 콘텐츠 생성 - 표 형식"""
    # 다음 주 금요일 계산
    from datetime import timedelta
    today = datetime.now()
    days_until_friday = (4 - today.weekday()) % 7
    if days_until_friday == 0:
        days_until_friday = 7
    next_friday = today + timedelta(days=days_until_friday)
    target_date = next_friday.strftime('~%m/%d')

    # HTML 시작
    html = '<h1>어제 온콜 이슈</h1><p><br /></p><hr />'
    html += '<table data-layout="center"><colgroup>'
    html += '<col style="width: 80px;" />'
    html += '<col style="width: 400px;" />'
    html += '<col style="width: 300px;" />'
    html += '<col style="width: 250px;" />'
    html += '<col style="width: 300px;" />'
    html += '</colgroup><tbody>'

    # 헤더
    html += '<tr>'
    html += '<th><p><strong>이름</strong></p></th>'
    html += '<th><p><strong>과제</strong></p></th>'
    html += f'<th><p><strong>{target_date} 목표</strong></p></th>'
    html += '<th><p><strong>이슈</strong></p></th>'
    html += '<th><p><strong>KTLO</strong></p></th>'
    html += '</tr>'

    # 최형수 행
    html += '<tr>'
    html += '<td><p>최형수</p></td>'

    # 과제 (진행중)
    html += '<td><ul>'
    if not in_progress:
        html += '<li><p><em>진행중인 과제가 없습니다.</em></p></li>'
    else:
        for item in in_progress:
            # URL 결정 (Confluence 페이지면 url 필드 사용, 아니면 JIRA 링크)
            if 'url' in item:
                link_url = item['url']
                link_text = item['summary']
            else:
                link_url = f"https://jira.team.musinsa.com/browse/{item['key']}"
                link_text = f"{item['key']}: {item['summary']}"

            html += f'<li><p><a href="{link_url}">{link_text}</a></p>'
            if item.get('comment'):
                html += f'<ul><li><p><em>[{item["comment"]["date"]}] {item["comment"]["author"]}: {item["comment"]["text"]}</em></p></li></ul>'
            html += '</li>'
    html += '</ul><p><br /></p></td>'

    # 목표 (빈칸)
    html += '<td><p><br /></p></td>'

    # 이슈 (빈칸)
    html += '<td><p><br /></p></td>'

    # KTLO
    html += '<td><ul>'
    if not ktlo_items:
        html += '<li><p><em>완료된 KTLO가 없습니다.</em></p></li>'
    else:
        for item in ktlo_items[:15]:
            html += f'<li><p><a href="https://jira.team.musinsa.com/browse/{item["key"]}">{item["key"]}</a>: {item["summary"]} <em>({item["updated"]})</em></p></li>'
    html += '</ul></td>'

    html += '</tr>'
    html += '</tbody></table>'
    html += '<p><br /></p>'

    return html

def get_or_create_month_page():
    """월별 페이지 확인 및 생성"""
    print("📂 월별 페이지 확인 중...")

    # 자식 페이지 조회
    url = f"{WIKI_BASE_URL}/rest/api/content/{WIKI_PARENT_PAGE_ID}/child/page"
    response = api_request("GET", url)

    # 이번 달 페이지 찾기
    for page in response.get('results', []):
        if page['title'] == MONTH:
            print(f"  ✅ 월별 페이지 존재: ID={page['id']}")
            return page['id']

    # 없으면 생성
    print(f"  → 월별 페이지 생성 중: {MONTH}")

    page_data = {
        "type": "page",
        "title": MONTH,
        "space": {"key": "~hschoi82"},
        "ancestors": [{"id": WIKI_PARENT_PAGE_ID}],
        "body": {
            "storage": {
                "value": f"<p>{YEAR}년 {MONTH_NUM}월 스크럼 보고서</p>",
                "representation": "storage"
            }
        }
    }

    url = f"{WIKI_BASE_URL}/rest/api/content"
    response = api_request("POST", url, page_data)

    if 'id' in response:
        print(f"  ✅ 월별 페이지 생성 완료: ID={response['id']}")
        return response['id']
    else:
        print(f"  ❌ 월별 페이지 생성 실패: {response}")
        exit(1)

def create_daily_page(month_page_id, html_content):
    """일자별 페이지 생성"""
    print(f"📄 일자별 페이지 생성 중: {TODAY}")

    page_data = {
        "type": "page",
        "title": TODAY,
        "space": {"key": "~hschoi82"},
        "ancestors": [{"id": month_page_id}],
        "body": {
            "storage": {
                "value": html_content,
                "representation": "storage"
            }
        }
    }

    url = f"{WIKI_BASE_URL}/rest/api/content"

    try:
        response = api_request("POST", url, page_data)

        if 'id' in response:
            page_url = f"{response['_links']['base']}{response['_links']['webui']}"
            print(f"  ✅ 페이지 생성 완료!")
            print(f"  🔗 {page_url}")
            return page_url
        else:
            print(f"  ❌ 페이지 생성 실패: {response}")
            return None
    except Exception as e:
        print(f"  ❌ 에러 발생: {e}")
        return None

def main():
    """메인 함수"""
    print("=" * 80)
    print("🚀 스크럼 보고서 자동 생성 시작")
    print("=" * 80)
    print()

    # 환경 변수 확인
    if not JIRA_EMAIL or not JIRA_TOKEN:
        print("❌ 환경 변수가 설정되지 않았습니다.")
        print("   JIRA_EMAIL과 JIRA_TOKEN을 설정해주세요.")
        exit(1)

    # 1. JIRA 티켓 조회
    issues = get_jira_tickets()

    # 2. Confluence 페이지 조회
    pages = get_confluence_pages()

    # 3. 티켓 및 페이지 분석
    in_progress, ktlo_items = analyze_tickets(issues, pages)

    # 4. HTML 생성
    html_content = generate_html(in_progress, ktlo_items)

    # 5. 월별 페이지 확인/생성
    month_page_id = get_or_create_month_page()

    # 6. 일자별 페이지 생성
    page_url = create_daily_page(month_page_id, html_content)

    print()
    print("=" * 80)
    if page_url:
        print("✅ 스크럼 보고서 생성 완료!")
        print(f"🔗 {page_url}")
    else:
        print("❌ 스크럼 보고서 생성 실패")
    print("=" * 80)

if __name__ == "__main__":
    main()
