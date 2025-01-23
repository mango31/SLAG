import { Middleware } from "@reduxjs/toolkit";
import { isRejectedWithValue } from "@reduxjs/toolkit";

export const errorMiddleware: Middleware = () => (next) => (action) => {
  // Check if the action is a rejected action with a value
  if (isRejectedWithValue(action)) {
    // Log the error
    console.error("Action Error:", {
      type: action.type,
      error: action.payload,
      meta: action.meta,
    });

    // You could also send to an error tracking service like Sentry here
    // if (process.env.NODE_ENV === 'production') {
    //   Sentry.captureException(action.payload);
    // }

    // You could also show a toast notification here
    // toast.error(action.payload);
  }

  return next(action);
};
