import { createSlice, createAsyncThunk } from "@reduxjs/toolkit";

// Types
interface User {
  id: string;
  username?: string;
  email?: string;
  first_name?: string;
  last_name?: string;
}

interface AuthState {
  user: User | null;
  token: string | null;
  isLoading: boolean;
  error: string | null;
  authMethod: "email" | "wallet" | null;
}

const clearAuthData = () => {
  localStorage.removeItem("auth_token");
  localStorage.removeItem("user");
  localStorage.removeItem("authMethod");
};

const initialState: AuthState = {
  user: null,
  token: null,
  isLoading: false,
  error: null,
  authMethod: null,
};

// Traditional login
export const loginWithEmail = createAsyncThunk(
  "auth/loginWithEmail",
  async (
    credentials: { identifier: string; password: string },
    { dispatch, rejectWithValue }
  ) => {
    try {
      // First, ensure we're completely logged out
      await dispatch(logout()).unwrap();

      const response = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL}/api/auth/login`,
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            ...(credentials.identifier.includes("@")
              ? { email: credentials.identifier }
              : { username: credentials.identifier }),
            password: credentials.password,
            login_method: "email",
          }),
        }
      );

      const data = await response.json();
      if (!response.ok) {
        throw new Error(data.detail || "Failed to sign in");
      }

      localStorage.setItem("auth_token", data.token);
      localStorage.setItem("authMethod", "email");
      return { user: data.user, token: data.token };
    } catch (error) {
      return rejectWithValue(
        error instanceof Error ? error.message : "Login failed"
      );
    }
  }
);

// Web3 wallet login
export const loginWithWallet = createAsyncThunk(
  "auth/loginWithWallet",
  async (publicKey: string, { dispatch, rejectWithValue }) => {
    try {
      // First, ensure we're completely logged out
      await dispatch(logout()).unwrap();

      const response = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL}/api/auth/login`,
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            web3_wallet: publicKey,
            login_method: "web3",
          }),
        }
      );

      const data = await response.json();
      if (!response.ok) {
        throw new Error(data.detail || "Failed to sign in");
      }

      localStorage.setItem("auth_token", data.token);
      localStorage.setItem("authMethod", "wallet");
      return { user: data.user, token: data.token };
    } catch (error) {
      return rejectWithValue(
        error instanceof Error ? error.message : "Login failed"
      );
    }
  }
);

// Logout
export const logout = createAsyncThunk("auth/logout", async () => {
  clearAuthData();
  // Clear any other auth-related data in localStorage
  const authKeys = Object.keys(localStorage).filter(
    (key) =>
      key.startsWith("auth_") || key.includes("token") || key.includes("user")
  );
  authKeys.forEach((key) => localStorage.removeItem(key));
  return null;
});

// Add registration interface
interface RegistrationData {
  username: string;
  email: string;
  password: string;
  first_name: string;
  last_name: string;
}

// Add registration thunk after the existing thunks
export const registerWithEmail = createAsyncThunk(
  "auth/registerWithEmail",
  async (data: RegistrationData, { dispatch, rejectWithValue }) => {
    try {
      // First, ensure we're completely logged out
      await dispatch(logout()).unwrap();

      const BACKEND_URL = process.env.NEXT_PUBLIC_API_URL;
      if (!BACKEND_URL) {
        throw new Error("API URL not configured");
      }

      const response = await fetch(`${BACKEND_URL}/api/users`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          ...data,
          login_method: "email",
          web3_wallet: null,
        }),
        credentials: "include",
      });

      const responseData = await response.json();

      if (!response.ok) {
        throw new Error(
          responseData.detail || responseData.message || "Registration failed"
        );
      }

      // Store new auth data
      localStorage.setItem("auth_token", responseData.token);
      localStorage.setItem("authMethod", "email");

      return { user: responseData.user, token: responseData.token };
    } catch (error) {
      console.error("Registration error:", error);
      return rejectWithValue(
        error instanceof Error ? error.message : "Registration failed"
      );
    }
  }
);

const authSlice = createSlice({
  name: "auth",
  initialState,
  reducers: {
    clearError: (state) => {
      state.error = null;
    },
  },
  extraReducers: (builder) => {
    builder
      // Email login
      .addCase(loginWithEmail.pending, (state) => {
        state.isLoading = true;
        state.error = null;
      })
      .addCase(loginWithEmail.fulfilled, (state, action) => {
        state.isLoading = false;
        state.user = action.payload.user;
        state.token = action.payload.token;
        state.authMethod = "email";
        state.error = null;
      })
      .addCase(loginWithEmail.rejected, (state, action) => {
        state.isLoading = false;
        state.error = action.payload as string;
      })
      // Wallet login
      .addCase(loginWithWallet.pending, (state) => {
        state.isLoading = true;
        state.error = null;
      })
      .addCase(loginWithWallet.fulfilled, (state, action) => {
        state.isLoading = false;
        state.user = action.payload.user;
        state.token = action.payload.token;
        state.authMethod = "wallet";
        state.error = null;
      })
      .addCase(loginWithWallet.rejected, (state, action) => {
        state.isLoading = false;
        state.error = action.payload as string;
      })
      // Logout
      .addCase(logout.fulfilled, (state) => {
        state.user = null;
        state.token = null;
        state.authMethod = null;
        state.error = null;
      })
      // Add registration cases
      .addCase(registerWithEmail.pending, (state) => {
        state.isLoading = true;
        state.error = null;
      })
      .addCase(registerWithEmail.fulfilled, (state, action) => {
        state.isLoading = false;
        state.user = action.payload.user;
        state.token = action.payload.token;
        state.authMethod = "email";
        state.error = null;
      })
      .addCase(registerWithEmail.rejected, (state, action) => {
        state.isLoading = false;
        state.error = action.payload as string;
      });
  },
});

export const { clearError } = authSlice.actions;
export default authSlice.reducer;
