export const disconnectWallet = createAsyncThunk(
  "web3/disconnectWallet",
  async (_, { dispatch }) => {
    try {
      // Disconnect from Phantom wallet
      const { solana } = window as any;
      if (solana?.disconnect) {
        await solana.disconnect();
      }

      // Set disconnected flag in localStorage
      localStorage.setItem("wallet_disconnected", "true");

      return null;
    } catch (error) {
      console.error("Error disconnecting wallet:", error);
      throw error;
    }
  }
);

// In the slice reducers:
extraReducers: (builder) => {
  builder
    // ... other cases ...
    .addCase(disconnectWallet.fulfilled, (state) => {
      state.connected = false;
      state.publicKey = null;
      state.balance = null;
      state.error = null;
    });
};
