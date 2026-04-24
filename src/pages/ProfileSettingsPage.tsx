import { Alert, Button, Card, DatePicker, Form, Input, Select, Space, Tabs } from 'antd';
import dayjs from 'dayjs';
import { PageHeader } from '../components/shared/PageHeader';
import { useUserStore } from '../stores/useUserStore';

export function ProfileSettingsPage() {
  const { name, locale, targetGrade, examDate } = useUserStore();

  return (
    <>
      <PageHeader
        title="프로필 설정"
        description="기본 프로필, 학습 목표, 언어 설정을 관리합니다."
      />
      <Card>
        <Tabs
          items={[
            {
              key: 'profile',
              label: '기본 프로필',
              children: (
                <Form layout="vertical" initialValues={{ name, nickname: 'topik_master', locale }}>
                  <Form.Item label="이름" name="name">
                    <Input aria-label="이름" />
                  </Form.Item>
                  <Form.Item label="닉네임" name="nickname">
                    <Input aria-label="닉네임" />
                  </Form.Item>
                  <Form.Item label="화면 언어" name="locale">
                    <Select
                      aria-label="화면 언어"
                      options={[
                        { value: 'KO', label: '한국어' },
                        { value: 'VI', label: 'Tiếng Việt' },
                        { value: 'EN', label: 'English' },
                      ]}
                    />
                  </Form.Item>
                  <Button type="primary">프로필 저장</Button>
                </Form>
              ),
            },
            {
              key: 'goal',
              label: '학습 목표',
              children: (
                <Form
                  layout="vertical"
                  initialValues={{ targetGrade, examDate: dayjs(examDate) }}
                >
                  <Form.Item label="목표 급수" name="targetGrade">
                    <Select
                      aria-label="목표 급수"
                      options={['TOPIK I 2급', 'TOPIK II 4급', 'TOPIK II 5급', 'TOPIK II 6급'].map((grade) => ({
                        value: grade,
                        label: grade,
                      }))}
                    />
                  </Form.Item>
                  <Form.Item label="시험일" name="examDate">
                    <DatePicker aria-label="시험일" style={{ width: '100%' }} />
                  </Form.Item>
                  <Button type="primary">목표 저장</Button>
                </Form>
              ),
            },
            {
              key: 'security',
              label: '계정 보안',
              children: (
                <Space direction="vertical" style={{ width: '100%' }}>
                  <Alert
                    type="warning"
                    showIcon
                    message="중요한 계정 변경은 확인 단계를 거칩니다"
                    description="비밀번호 변경, 마케팅 수신 동의, 회원 탈퇴는 실제 API 연결 시 별도 확인 창을 붙여야 합니다."
                  />
                  <Button>비밀번호 변경</Button>
                  <Button danger>회원 탈퇴 요청</Button>
                </Space>
              ),
            },
          ]}
        />
      </Card>
    </>
  );
}
