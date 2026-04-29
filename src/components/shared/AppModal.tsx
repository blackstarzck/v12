import { Modal } from 'antd';
import type { ModalProps } from 'antd';

function joinClassNames(...values: Array<string | undefined>) {
  return values.filter(Boolean).join(' ');
}

export function AppModal({ wrapClassName, ...props }: ModalProps) {
  return (
    <Modal
      wrapClassName={joinClassNames('app-modal', wrapClassName)}
      {...props}
    />
  );
}
