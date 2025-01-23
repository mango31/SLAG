import { createSlice, createAsyncThunk, PayloadAction } from "@reduxjs/toolkit";
import { Connection, PublicKey, clusterApiUrl } from "@solana/web3.js";

// Initialize Solana connection
const connection = new Connection(clusterApiUrl("devnet"), "confirmed");

// Check if wallet is already connected
const checkInitialConnection = () => {
  if (typeof window === "undefined") return false;
  const provider = window?.phantom?.solana;
  const wasDisconnected =
    localStorage.getItem("wallet_disconnected") === "true";
  return provider?.isPhantom && provider.isConnected && !wasDisconnected;
};

interface Web3State {
  connected: boolean;
  publicKey: string | null;
  balance: number | null;
  isLoading: boolean;
  error: string | null;
  isAvailable: boolean;
}

const initialState: Web3State = {
  connected: checkInitialConnection(),
  publicKey: null,
  balance: null,
  isLoading: false,
  error: null,
  isAvailable: typeof window !== "undefined" && !!window?.phantom?.solana,
};

// New thunk to check existing connection
export const checkExistingConnection = createAsyncThunk(
  "web3/checkExistingConnection",
  async (_, { rejectWithValue }) => {
    try {
      const provider = window?.phantom?.solana;
      const wasDisconnected =
        localStorage.getItem("wallet_disconnected") === "true";

      if (
        !provider?.isPhantom ||
        !provider.isConnected ||
        !provider.publicKey ||
        wasDisconnected
      ) {
        return null;
      }

      const publicKey = provider.publicKey.toString();
      const balance = await connection.getBalance(provider.publicKey);

      return {
        publicKey,
        balance: balance / 1e9,
      };
    } catch (error) {
      return rejectWithValue(
        error instanceof Error
          ? error.message
          : "Failed to check existing connection"
      );
    }
  }
);

// Async thunks
export const fetchBalance = createAsyncThunk(
  "web3/fetchBalance",
  async (publicKey: string, { rejectWithValue }) => {
    try {
      const balance = await connection.getBalance(new PublicKey(publicKey));
      return balance / 1e9; // Convert lamports to SOL
    } catch (error) {
      return rejectWithValue(
        error instanceof Error ? error.message : "Failed to fetch balance"
      );
    }
  }
);

export const connectWallet = createAsyncThunk(
  "web3/connectWallet",
  async (_, { rejectWithValue }) => {
    try {
      const provider = window?.phantom?.solana;
      if (!provider?.isPhantom) {
        throw new Error("Phantom wallet not found");
      }

      let publicKey: string;

      // Check if already connected
      if (provider.isConnected && provider.publicKey) {
        publicKey = provider.publicKey.toString();
      } else {
        const response = await provider.connect();
        publicKey = response.publicKey.toString();
      }

      const balance = await connection.getBalance(new PublicKey(publicKey));
      localStorage.removeItem("wallet_disconnected");

      return {
        publicKey,
        balance: balance / 1e9,
      };
    } catch (error) {
      console.error("Wallet connection error:", error);
      return rejectWithValue(
        error instanceof Error ? error.message : "Failed to connect wallet"
      );
    }
  }
);

export const disconnectWallet = createAsyncThunk(
  "web3/disconnectWallet",
  async (_, { rejectWithValue }) => {
    try {
      const provider = window?.phantom?.solana;
      if (provider?.isPhantom && provider.isConnected) {
        await provider.disconnect();
        localStorage.setItem("wallet_disconnected", "true");
      }
      return true;
    } catch (error) {
      return rejectWithValue(
        error instanceof Error ? error.message : "Failed to disconnect wallet"
      );
    }
  }
);

const web3Slice = createSlice({
  name: "web3",
  initialState,
  reducers: {
    checkWalletAvailability: (state) => {
      state.isAvailable =
        typeof window !== "undefined" && !!window?.phantom?.solana;
    },
    resetState: (state) => {
      Object.assign(state, initialState);
    },
  },
  extraReducers: (builder) => {
    builder
      // Check existing connection
      .addCase(checkExistingConnection.pending, (state) => {
        state.isLoading = true;
        state.error = null;
      })
      .addCase(checkExistingConnection.fulfilled, (state, action) => {
        state.isLoading = false;
        if (action.payload) {
          state.connected = true;
          state.publicKey = action.payload.publicKey;
          state.balance = action.payload.balance;
        } else {
          state.connected = false;
          state.publicKey = null;
          state.balance = null;
        }
        state.error = null;
      })
      .addCase(checkExistingConnection.rejected, (state, action) => {
        state.isLoading = false;
        state.connected = false;
        state.publicKey = null;
        state.balance = null;
        state.error = action.payload as string;
      })
      // Connect wallet
      .addCase(connectWallet.pending, (state) => {
        state.isLoading = true;
        state.error = null;
      })
      .addCase(connectWallet.fulfilled, (state, action) => {
        state.isLoading = false;
        state.connected = true;
        state.publicKey = action.payload.publicKey;
        state.balance = action.payload.balance;
        state.error = null;
      })
      .addCase(connectWallet.rejected, (state, action) => {
        state.isLoading = false;
        state.connected = false;
        state.publicKey = null;
        state.balance = null;
        state.error = action.payload as string;
      })
      // Disconnect wallet
      .addCase(disconnectWallet.fulfilled, (state) => {
        state.connected = false;
        state.publicKey = null;
        state.balance = null;
        state.error = null;
      })
      // Fetch balance
      .addCase(fetchBalance.fulfilled, (state, action) => {
        state.balance = action.payload;
      })
      .addCase(fetchBalance.rejected, (state, action) => {
        state.error = action.payload as string;
      });
  },
});

export const { checkWalletAvailability, resetState } = web3Slice.actions;
export default web3Slice.reducer;
