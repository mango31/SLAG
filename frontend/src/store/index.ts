import { configureStore, combineReducers } from "@reduxjs/toolkit";
import { persistStore, persistReducer } from "redux-persist";
import storage from "redux-persist/lib/storage";
import { useDispatch, useSelector } from "react-redux";
import type { TypedUseSelectorHook } from "react-redux";

import authReducer from "./slices/authSlice";
import web3Reducer from "./slices/web3Slice";
import queueReducer from "./slices/queueSlice";
import { errorMiddleware } from "./middleware/errorMiddleware";

// Configure persist options
const persistConfig = {
  key: "root",
  storage,
  whitelist: ["auth", "queue"], // Only persist these reducers
  blacklist: ["web3"], // Don't persist web3 state
  version: 1, // Add version for future migrations
};

const rootReducer = combineReducers({
  auth: authReducer,
  web3: web3Reducer,
  queue: queueReducer,
});

const persistedReducer = persistReducer(persistConfig, rootReducer);

export const store = configureStore({
  reducer: persistedReducer,
  middleware: (getDefaultMiddleware) =>
    getDefaultMiddleware({
      serializableCheck: {
        ignoredActions: ["persist/PERSIST", "persist/REHYDRATE"],
      },
    }).concat(errorMiddleware),
  devTools: process.env.NODE_ENV !== "production",
});

export const persistor = persistStore(store);

// Infer the `RootState` and `AppDispatch` types from the store itself
export type RootState = ReturnType<typeof store.getState>;
export type AppDispatch = typeof store.dispatch;

// Create typed hooks
export const useAppDispatch: () => AppDispatch = useDispatch;
export const useAppSelector: TypedUseSelectorHook<RootState> = useSelector;
