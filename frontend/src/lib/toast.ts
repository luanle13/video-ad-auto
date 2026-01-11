import toast from 'react-hot-toast';

export const toastSuccess = (message: string) => {
  return toast.success(message);
};

export const toastError = (message: string) => {
  return toast.error(message);
};

export const toastLoading = (message: string) => {
  return toast.loading(message);
};

export const toastDismiss = (toastId: string) => {
  return toast.dismiss(toastId);
};

export const toastPromise = <T,>(
  promise: Promise<T>,
  messages: {
    loading: string;
    success: string | ((result: T) => string);
    error: string | ((error: any) => string);
  }
) => {
  return toast.promise(promise, messages);
};

// Export as a unified object
export const Toast = {
  success: toastSuccess,
  error: toastError,
  loading: toastLoading,
  dismiss: toastDismiss,
  promise: toastPromise,
};

export default Toast;