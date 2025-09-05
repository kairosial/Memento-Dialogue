# 앨범 생성 시 Foreign Key 제약 조건 오류 해결 가이드

**작성일:** 2025-08-19  
**문제:** `insert or update on table "albums" violates foreign key constraint "albums_user_id_fkey"`

## 문제 원인 분석

### 현재 상황
- Google 로그인은 정상적으로 작동함
- 앨범 생성 시 `albums` 테이블의 `user_id` 외래키 제약 조건 위반 발생
- 제약 조건: `albums.user_id` → `public.users.id`

### 핵심 문제
**Google 로그인으로 생성된 사용자가 `public.users` 테이블에 존재하지 않음**

현재 인증 플로우:
1. Google OAuth를 통해 `auth.users` 테이블에 사용자 생성
2. `public.users` 테이블에는 사용자 프로필 정보가 생성되지 않음
3. 앨범 생성 시 `public.users.id`를 참조하려 하지만 해당 레코드가 없어 외래키 제약 조건 위반

## 해결 방법

### 1. 사용자 프로필 자동 생성 트리거 구현 (권장)

Supabase에서 다음 SQL을 실행하여 자동 프로필 생성 트리거를 설정:

```sql
-- 1. 새 사용자 자동 프로필 생성 함수
CREATE OR REPLACE FUNCTION public.handle_new_user()
RETURNS TRIGGER AS $$
BEGIN
  INSERT INTO public.users (id, email, full_name, created_at, updated_at)
  VALUES (
    new.id,
    new.email,
    COALESCE(new.raw_user_meta_data->>'full_name', new.email),
    NOW(),
    NOW()
  );
  RETURN new;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- 2. auth.users 테이블에 트리거 추가
CREATE TRIGGER on_auth_user_created
  AFTER INSERT ON auth.users
  FOR EACH ROW EXECUTE PROCEDURE public.handle_new_user();
```

### 2. 기존 사용자들의 프로필 수동 생성

현재 로그인한 사용자와 과거 사용자들을 위한 프로필 생성:

```sql
-- 기존 auth.users에 있지만 public.users에 없는 사용자들의 프로필 생성
INSERT INTO public.users (id, email, full_name, created_at, updated_at)
SELECT 
  au.id,
  au.email,
  COALESCE(au.raw_user_meta_data->>'full_name', au.email),
  au.created_at,
  NOW()
FROM auth.users au
LEFT JOIN public.users pu ON au.id = pu.id
WHERE pu.id IS NULL;
```

### 3. 프론트엔드에서 프로필 생성 체크 (임시 해결책)

AuthContext에서 로그인 후 프로필 존재 확인 및 생성:

```typescript
// AuthContext.tsx의 signInWithGoogle 함수 수정
const signInWithGoogle = async (googleAccessToken: string, userInfo?: any) => {
  try {
    // 기존 로그인 로직...
    
    if (data.user && data.session) {
      setUser(data.user);
      setSession(data.session);
      
      // 프로필 존재 확인 및 생성
      await ensureUserProfile(data.user);
      
      console.log('Google OAuth login successful');
      return;
    }
  } catch (error) {
    // 에러 처리...
  }
};

// 사용자 프로필 확인 및 생성 함수
const ensureUserProfile = async (user: User) => {
  try {
    // 프로필 존재 확인
    const { data: profile, error: checkError } = await supabase
      .from('users')
      .select('id')
      .eq('id', user.id)
      .single();

    if (checkError && checkError.code === 'PGRST116') {
      // 프로필이 없으면 생성
      const { error: insertError } = await supabase
        .from('users')
        .insert({
          id: user.id,
          email: user.email!,
          full_name: user.user_metadata?.full_name || user.email?.split('@')[0],
          created_at: new Date().toISOString(),
          updated_at: new Date().toISOString()
        });

      if (insertError) {
        console.error('프로필 생성 실패:', insertError);
      } else {
        console.log('사용자 프로필 생성 완료');
      }
    }
  } catch (error) {
    console.error('프로필 확인 중 오류:', error);
  }
};
```

## 권장 구현 순서

1. **즉시 해결**: Supabase에서 방법 1의 트리거 SQL 실행
2. **기존 사용자 처리**: 방법 2의 기존 사용자 프로필 생성 SQL 실행
3. **검증**: 새로운 Google 로그인으로 앨범 생성 테스트
4. **선택사항**: 추가 안전장치로 방법 3의 프론트엔드 체크 구현

## 테스트 방법

### 1. 트리거 동작 확인
```sql
-- 새 사용자 생성 시 public.users에 자동 생성되는지 확인
SELECT au.id, au.email, pu.id IS NOT NULL as has_profile
FROM auth.users au
LEFT JOIN public.users pu ON au.id = pu.id
ORDER BY au.created_at DESC;
```

### 2. 앨범 생성 테스트
1. Google 로그인 실행
2. 새 앨범 생성 시도
3. 성공적으로 생성되는지 확인

## 추가 고려사항

### 보안
- RLS 정책이 올바르게 적용되어 있는지 확인
- 트리거 함수는 `SECURITY DEFINER`로 설정하여 권한 문제 방지

### 데이터 무결성
- 기존 앨범이 있는 사용자의 경우 데이터 정합성 확인
- 중복 프로필 생성 방지를 위한 UNIQUE 제약 조건 활용

이 해결책으로 Google 로그인 후 앨범 생성이 정상적으로 작동할 것입니다.