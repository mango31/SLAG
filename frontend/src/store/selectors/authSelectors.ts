import { createSelector } from "@reduxjs/toolkit";
import type { RootState } from "@/store";

export const selectAuth = (state: RootState) => state.auth;

export const selectUser = createSelector(selectAuth, (auth) => auth.user);
export const selectAuthMethod = createSelector(
  selectAuth,
  selectAuth,
  (auth) => !!auth.token && !!auth.user

export const selectAuthLoading = createSelector(
  selectAuth,
  (auth) => auth.isLoading
);

export const selectAuthError = createSelector(selectAuth, (auth) => auth.error);

export const selectIsWeb3User = createSelector(
  selectAuthMethod,
  (authMethod) => authMethod === "wallet"
);
export const selectAuthError = createSelector(selectAuth, (auth) => auth.error);  selectUser,
  (user) => user?.web3_wallet !== null