import { useCallback } from "react";
import { useDispatch, useSelector } from "react-redux";
import type { AppDispatch, RootState } from "@/store";
import {
  login,
  logout,
  verifyToken,
  setAuthMethod,
} from "@/store/slices/authSlice";
import type { User } from "@/store/slices/authSlice";

export function useAuth() {
  const dispatch = useDispatch<AppDispatch>();
  const { user, token, authMethod, isLoading, error } = useSelector(
    (state: RootState) => state.auth
  );

  const signIn = useCallback(
    async (credentials: {
      email?: string;
      password?: string;
      web3_wallet?: string;
    }) => {
      try {
        const result = await dispatch(login(credentials)).unwrap();
        return result;
      } catch (error) {
        console.error("Login failed:", error);
        throw error;
      }
    },
    [dispatch]
  );

  const signOut = useCallback(() => {
    dispatch(logout());
  }, [dispatch]);

  const checkAuth = useCallback(async () => {
    try {
      await dispatch(verifyToken()).unwrap();
    } catch (error) {
      console.error("Token verification failed:", error);
    }
  }, [dispatch]);

  const updateAuthMethod = useCallback(
    (method: string) => {
      dispatch(setAuthMethod(method));
    },
    [dispatch]
  );

  return {
    user,
    token,
    authMethod,
    isLoading,
    error,
    signIn,
    signOut,
    checkAuth,
    updateAuthMethod,
  };
}
