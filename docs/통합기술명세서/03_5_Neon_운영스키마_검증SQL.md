# Neon `production` — 운영 물리 스키마 검증용 조회 전용 SQL

**대상:** `AI_DevCoach` → `production` → `neondb` → `public`  
**사용처:** Neon Console → SQL Editor. 모든 명령은 시스템 카탈로그/메타데이터 **SELECT**이며 개인정보나 실제 코칭 본문은 조회하지 않습니다. 결과를 공유할 때는 비밀정보가 포함되지 않았는지 점검하세요.

> 이번 세션에서는 Neon 연결 도구 오류로 아래 결과를 가져오지 못했습니다. 따라서 SQL을 제공하는 것은 운영 DB 조회 완료를 의미하지 않습니다.

## Q1. 테이블·뷰 전체 목록

```sql
SELECT table_schema, table_name, table_type
FROM information_schema.tables
WHERE table_schema = 'public'
ORDER BY table_name;
```

## Q2. 컬럼명·자료형·NULL·기본값 확인

```sql
SELECT table_name, ordinal_position, column_name,
       data_type, udt_name, character_maximum_length,
       is_nullable, column_default, is_identity
FROM information_schema.columns
WHERE table_schema = 'public'
ORDER BY table_name, ordinal_position;
```

## Q3. PK·UNIQUE·CHECK·FK 제약조건 (실제 정의)

```sql
SELECT c.conrelid::regclass::text AS table_name,
       c.conname AS constraint_name,
       CASE c.contype WHEN 'p' THEN 'PRIMARY KEY'
           WHEN 'f' THEN 'FOREIGN KEY'
           WHEN 'u' THEN 'UNIQUE'
           WHEN 'c' THEN 'CHECK' ELSE c.contype::text END AS type,
       pg_get_constraintdef(c.oid, true) AS definition
FROM pg_constraint AS c
JOIN pg_namespace AS n ON n.oid = c.connamespace
WHERE n.nspname = 'public'
ORDER BY 1, 3, 2;
```

## Q4. 테이블별 인덱스

```sql
SELECT tablename AS table_name, indexname AS index_name, indexdef
FROM pg_indexes
WHERE schemaname = 'public'
ORDER BY tablename, indexname;
```

## Q5. Alembic 버전

```sql
SELECT version_num FROM public.alembic_version;
```

## Q6. 외래키 컬럼 대응표

```sql
SELECT con.conrelid::regclass::text AS source_table,
       a.attname AS source_column,
       con.confrelid::regclass::text AS target_table,
       af.attname AS target_column,
       con.confdeltype AS on_delete_code
FROM pg_constraint con
JOIN LATERAL unnest(con.conkey) WITH ORDINALITY sk(attnum, ord) ON true
JOIN LATERAL unnest(con.confkey) WITH ORDINALITY tk(attnum, ord) ON tk.ord=sk.ord
JOIN pg_attribute a ON a.attrelid=con.conrelid AND a.attnum=sk.attnum
JOIN pg_attribute af ON af.attrelid=con.confrelid AND af.attnum=tk.attnum
WHERE con.contype='f' AND con.connamespace='public'::regnamespace
ORDER BY source_table, source_column;
```

## Q7. AI 대화기록 테이블 존재 여부 (데이터 본문 조회 없음)

```sql
SELECT to_regclass('public.agent_chat_messages') AS chat_table;
```

## 검증 기록표

| 조회 | 상태 | 운영에서 확인한 결과 | 증빙 |
|---|---|---|---|
| Q1 테이블 목록 | 미실행 | — | — |
| Q2 컬럼 | 미실행 | — | — |
| Q3 제약조건 | 미실행 | — | — |
| Q4 인덱스 | 미실행 | — | — |
| Q5 Alembic | 미실행 | — | — |
| Q6 FK | 미실행 | — | — |
| Q7 채팅 테이블 | 미실행 | — | — |

**판정 원칙:** 운영 물리 모델은 Q1~Q6 결과가 확보될 때 확정합니다. `alembic_version` 값과 GitHub 마이그레이션 head가 같더라도 운영 테이블의 drift는 별도로 확인해야 합니다.
