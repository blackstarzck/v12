import { Space, Typography } from 'antd';
import type { ReactNode } from 'react';

interface PageHeaderProps {
  title: string;
  description: string;
  extra?: ReactNode;
}

export function PageHeader({ title, description, extra }: PageHeaderProps) {
  return (
    <div className="page-header">
      <div>
        <Typography.Title level={1} className="page-title">
          {title}
        </Typography.Title>
        <p className="page-description">{description}</p>
      </div>
      {extra && <Space wrap>{extra}</Space>}
    </div>
  );
}
