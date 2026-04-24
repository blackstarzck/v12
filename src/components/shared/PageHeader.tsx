import { Flex, Space, Typography } from 'antd';
import type { ReactNode } from 'react';

interface PageHeaderProps {
  title: string;
  description: string;
  extra?: ReactNode;
}

export function PageHeader({ title, description, extra }: PageHeaderProps) {
  return (
    <div className="page-header">
      <Flex vertical gap={4}>
        <Typography.Title level={1}>
          {title}
        </Typography.Title>
        <Typography.Paragraph type="secondary">{description}</Typography.Paragraph>
      </Flex>
      {extra && <Space wrap>{extra}</Space>}
    </div>
  );
}
