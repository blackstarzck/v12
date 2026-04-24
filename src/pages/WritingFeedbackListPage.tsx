import {
  Button,
  Card,
  Empty,
  Input,
  Select,
  Space,
  Table,
  Tabs,
  Tag,
} from 'antd';
import type { ColumnsType } from 'antd/es/table';
import { Link, useNavigate } from 'react-router-dom';
import { PageHeader } from '../components/shared/PageHeader';
import { feedbackRecords } from '../data/mockData';
import { useFeedbackStore } from '../stores/useFeedbackStore';
import type { FeedbackRecord } from '../types/domain';

const columns: ColumnsType<FeedbackRecord> = [
  {
    title: '제목',
    dataIndex: 'title',
    key: 'title',
    render: (value, record) => (
      <Link className="notice-table-title" to={`/writing/feedback/${record.id}`}>
        {value}
      </Link>
    ),
  },
  { title: '유형', dataIndex: 'type', key: 'type', responsive: ['md'] },
  {
    title: '점수',
    key: 'score',
    render: (_, record) => (record.score ? `${record.score}/${record.total}` : '작성 중'),
  },
  {
    title: '상태',
    dataIndex: 'status',
    key: 'status',
    render: (status) => (
      <Tag color={status === 'Draft' ? 'warning' : status === 'Needs review' ? 'error' : 'success'}>
        {status}
      </Tag>
    ),
  },
  { title: '날짜', dataIndex: 'date', key: 'date', responsive: ['lg'] },
];

export function WritingFeedbackListPage() {
  const navigate = useNavigate();
  const { search, statusFilter, sortKey, setSearch, setStatusFilter, setSortKey } =
    useFeedbackStore();

  const filterRecords = (draftOnly: boolean) => {
    const filtered = feedbackRecords
      .filter((record) => (draftOnly ? record.status === 'Draft' : record.status !== 'Draft'))
      .filter((record) => statusFilter === 'all' || record.status === statusFilter)
      .filter((record) => record.title.includes(search) || record.type.includes(search));

    return [...filtered].sort((a, b) =>
      sortKey === 'score' ? b.score - a.score : b.date.localeCompare(a.date),
    );
  };

  const renderTable = (draftOnly: boolean) => {
    const records = filterRecords(draftOnly);
    return (
      <Table
        rowKey="id"
        columns={columns}
        dataSource={records}
        locale={{ emptyText: <Empty description="조건에 맞는 답안이 없습니다" /> }}
        onRow={(record) => ({
          onDoubleClick: () => navigate(`/writing/feedback/${record.id}`),
        })}
        scroll={{ x: 760 }}
      />
    );
  };

  return (
    <>
      <PageHeader
        title="쓰기 보관함"
        description="완료된 AI 피드백과 작성 중인 답안을 구분해 확인합니다."
        extra={
          <Button type="primary">
            <Link to="/writing/setup">새 쓰기 연습</Link>
          </Button>
        }
      />
      <Card>
        <Space wrap style={{ marginBottom: 16 }}>
          <Input.Search
            aria-label="쓰기 피드백 검색"
            allowClear
            placeholder="제목 또는 유형 검색…"
            value={search}
            onChange={(event) => setSearch(event.target.value)}
          />
          <Select
            aria-label="피드백 상태 필터"
            value={statusFilter}
            onChange={setStatusFilter}
            style={{ width: 180 }}
            options={[
              { value: 'all', label: '전체 상태' },
              { value: 'Feedback ready', label: '피드백 완료' },
              { value: 'Needs review', label: '재검토 필요' },
              { value: 'Draft', label: '임시 저장' },
            ]}
          />
          <Select
            aria-label="쓰기 목록 정렬"
            value={sortKey}
            onChange={setSortKey}
            style={{ width: 160 }}
            options={[
              { value: 'latest', label: '최신순' },
              { value: 'score', label: '점수순' },
            ]}
          />
        </Space>
        <Tabs
          items={[
            { key: 'done', label: '완료된 피드백', children: renderTable(false) },
            { key: 'draft', label: '임시 보관 내역', children: renderTable(true) },
          ]}
        />
      </Card>
    </>
  );
}
