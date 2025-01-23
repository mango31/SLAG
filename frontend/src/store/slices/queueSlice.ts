import { createSlice, createAsyncThunk, PayloadAction } from "@reduxjs/toolkit";

// Types
export interface StoryTask {
  id: string;
  prompt: string;
  status: "generating" | "completed" | "error" | "stopped";
  progress: number;
  currentStep: string;
  error?: string;
  storyId?: string;
  timestamp?: number;
  wordCount?: number;
  requestId?: string;
  title?: string;
}

interface QueueState {
  tasks: StoryTask[];
  activePolls: Record<string, boolean>;
  isProcessing: boolean;
  error: string | null;
}

const initialState: QueueState = {
  tasks: [],
  activePolls: {},
  isProcessing: false,
  error: null,
};

// Constants
const STORY_ENGINE_URL =
  process.env.NEXT_PUBLIC_STORY_ENGINE_URL ||
  "http://vmini-engine-alb-production-943444221.us-west-2.elb.amazonaws.com";
const BACKEND_URL = process.env.NEXT_PUBLIC_API_URL;

// Async thunks
export const generateStory = createAsyncThunk(
  "queue/generateStory",
  async (prompt: string, { rejectWithValue }) => {
    try {
      const response = await fetch(`${STORY_ENGINE_URL}/generate`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${localStorage.getItem("auth_token")}`,
        },
        body: JSON.stringify({ prompt }),
      });

      if (!response.ok) {
        throw new Error("Failed to start story generation");
      }

      const data = await response.json();
      return {
        requestId: data.request_id,
        prompt,
      };
    } catch (error) {
      return rejectWithValue(
        error instanceof Error ? error.message : "Generation failed"
      );
    }
  }
);

export const checkStoryStatus = createAsyncThunk(
  "queue/checkStoryStatus",
  async (requestId: string, { rejectWithValue }) => {
    try {
      const response = await fetch(`${STORY_ENGINE_URL}/status/${requestId}`, {
        headers: {
          Authorization: `Bearer ${localStorage.getItem("auth_token")}`,
        },
      });

      if (!response.ok) {
        throw new Error("Failed to check story status");
      }

      const data = await response.json();
      return {
        requestId,
        status: data.status,
        result: data.result,
      };
    } catch (error) {
      return rejectWithValue(
        error instanceof Error ? error.message : "Status check failed"
      );
    }
  }
);

export const saveCompletedStory = createAsyncThunk(
  "queue/saveCompletedStory",
  async (storyData: any, { rejectWithValue }) => {
    try {
      const response = await fetch(`${BACKEND_URL}/api/stories`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${localStorage.getItem("auth_token")}`,
        },
        body: JSON.stringify(storyData),
      });

      if (!response.ok) {
        throw new Error("Failed to save story");
      }

      return await response.json();
    } catch (error) {
      return rejectWithValue(
        error instanceof Error ? error.message : "Save failed"
      );
    }
  }
);

const queueSlice = createSlice({
  name: "queue",
  initialState,
  reducers: {
    addTask: (state, action: PayloadAction<StoryTask>) => {
      state.tasks.push(action.payload);
    },
    removeTask: (state, action: PayloadAction<string>) => {
      state.tasks = state.tasks.filter((task) => task.id !== action.payload);
    },
    updateTaskProgress: (
      state,
      action: PayloadAction<{
        id: string;
        progress: number;
        currentStep: string;
      }>
    ) => {
      const task = state.tasks.find((t) => t.id === action.payload.id);
      if (task) {
        task.progress = action.payload.progress;
        task.currentStep = action.payload.currentStep;
      }
    },
    setTaskError: (
      state,
      action: PayloadAction<{ id: string; error: string }>
    ) => {
      const task = state.tasks.find((t) => t.id === action.payload.id);
      if (task) {
        task.status = "error";
        task.error = action.payload.error;
      }
    },
    stopTask: (state, action: PayloadAction<string>) => {
      const task = state.tasks.find((t) => t.id === action.payload);
      if (task) {
        task.status = "stopped";
      }
    },
    clearQueue: (state) => {
      state.tasks = [];
      state.activePolls = {};
      state.isProcessing = false;
      state.error = null;
    },
  },
  extraReducers: (builder) => {
    builder
      // Generate story
      .addCase(generateStory.pending, (state) => {
        state.isProcessing = true;
        state.error = null;
      })
      .addCase(generateStory.fulfilled, (state, action) => {
        state.isProcessing = false;
        // Task addition is handled by the component
      })
      .addCase(generateStory.rejected, (state, action) => {
        state.isProcessing = false;
        state.error = action.payload as string;
      })
      // Check status
      .addCase(checkStoryStatus.fulfilled, (state, action) => {
        const task = state.tasks.find(
          (t) => t.requestId === action.payload.requestId
        );
        if (task && action.payload.status === "completed") {
          task.status = "completed";
          task.progress = 100;
          task.currentStep = "Story completed!";
          if (action.payload.result) {
            task.title = action.payload.result.title;
            task.wordCount = action.payload.result.word_count;
            task.timestamp = Date.now();
          }
        }
      })
      // Save completed story
      .addCase(saveCompletedStory.fulfilled, (state, action) => {
        const task = state.tasks.find(
          (t) => t.requestId === action.payload.request_id
        );
        if (task) {
          task.storyId = action.payload.id;
        }
      });
  },
});

export const {
  addTask,
  removeTask,
  updateTaskProgress,
  setTaskError,
  stopTask,
  clearQueue,
} = queueSlice.actions;

export default queueSlice.reducer;
