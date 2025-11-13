import React from 'react';
import { Button } from './Button';

interface DialogProps {
  isOpen: boolean;
  onClose: () => void;
  onConfirm: () => void;
  title: string;
  description: string;
  confirmText?: string;
  cancelText?: string;
  variant?: 'danger' | 'warning' | 'default';
  isLoading?: boolean;
}

export const Dialog: React.FC<DialogProps> = ({
  isOpen,
  onClose,
  onConfirm,
  title,
  description,
  confirmText = 'Confirm',
  cancelText = 'Cancel',
  variant = 'default',
  isLoading = false,
}) => {
  if (!isOpen) return null;

  const getVariantStyles = () => {
    switch (variant) {
      case 'danger':
        return {
          icon: '🗑️',
          confirmClass: 'bg-red-600 hover:bg-red-700 text-white',
        };
      case 'warning':
        return {
          icon: '⚠️',
          confirmClass: 'bg-yellow-600 hover:bg-yellow-700 text-white',
        };
      default:
        return {
          icon: 'ℹ️',
          confirmClass: 'bg-primary-600 hover:bg-primary-700 text-white',
        };
    }
  };

  const { icon, confirmClass } = getVariantStyles();

  return (
    <>
      {/* Overlay */}
      <div
        className="fixed inset-0 bg-black bg-opacity-50 z-40 animate-fade-in"
        onClick={onClose}
      />

      {/* Dialog */}
      <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
        <div className="bg-white dark:bg-slate-800 rounded-xl shadow-2xl max-w-md w-full p-6 animate-scale-in">
          {/* Icon */}
          <div className="flex items-center justify-center w-12 h-12 mx-auto mb-4 text-3xl">
            {icon}
          </div>

          {/* Title */}
          <h3 className="text-xl font-bold text-center mb-2 text-gray-900 dark:text-white">
            {title}
          </h3>

          {/* Description */}
          <p className="text-center text-gray-600 dark:text-gray-300 mb-6">
            {description}
          </p>

          {/* Actions */}
          <div className="flex gap-3">
            <Button
              onClick={onClose}
              disabled={isLoading}
              className="flex-1 bg-gray-200 hover:bg-gray-300 text-gray-800 dark:bg-gray-700 dark:hover:bg-gray-600 dark:text-gray-100"
            >
              {cancelText}
            </Button>
            <Button
              onClick={onConfirm}
              disabled={isLoading}
              className={`flex-1 ${confirmClass}`}
            >
              {isLoading ? 'Loading...' : confirmText}
            </Button>
          </div>
        </div>
      </div>
    </>
  );
};
