import { Card } from 'antd';
import type { CardProps } from 'antd';

function joinClassNames(...values: Array<string | undefined>) {
  return values.filter(Boolean).join(' ');
}

export function AppCard({ className, ...props }: CardProps) {
  return (
    <Card
      className={joinClassNames('app-card', 'app-surface', className)}
      {...props}
    />
  );
}
